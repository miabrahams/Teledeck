package main

import (
	"context"
	"errors"
	"goth/internal/config"
	"goth/internal/controllers"
	"goth/internal/handlers"
	external "goth/internal/service/external/api"
	"goth/internal/service/files/localfile"
	"goth/internal/service/hash/passwordhash"
	database "goth/internal/service/store/db"
	"goth/internal/service/store/dbstore"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	m "goth/internal/middleware"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"

	"path/filepath"
	"strings"

	"github.com/joho/godotenv"
)

/*
* Set to production at build time
* used to determine what assets to load
 */
var Environment = "development"

func init() {
	os.Setenv("env", Environment)
}

// FileServer conveniently sets up a http.FileServer handler to serve
// static files from a http.FileSystem.
func MediaFileServer(r chi.Router, path string, root http.FileSystem, logger *slog.Logger) {
	if strings.ContainsAny(path, "{}*") {
		panic("FileServer does not permit any URL parameters.")
	}

	if path != "/" && path[len(path)-1] != '/' {
		r.Get(path, http.RedirectHandler(path+"/", http.StatusMovedPermanently).ServeHTTP)
		path += "/"
	}
	path += "*"

	rootServer := http.FileServer(root)

	r.Get(path, func(w http.ResponseWriter, r *http.Request) {
		rctx := chi.RouteContext(r.Context())
		pathPrefix := strings.TrimSuffix(rctx.RoutePattern(), "/*")
		fs := http.StripPrefix(pathPrefix, rootServer)
		fs.ServeHTTP(w, r)
	})
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	err := godotenv.Load("../.env")
	if err != nil {
		logger.Error("Error loading .env file")
		return
	}

	r := chi.NewRouter()

	cfg := config.MustLoadConfig()

	/* Register Database Stores */
	db := database.MustOpen(cfg.DatabaseName)
	passwordhash := passwordhash.NewHPasswordHash()

	userStore := dbstore.NewUserStore(
		dbstore.NewUserStoreParams{
			DB:           db,
			PasswordHash: passwordhash,
		},
	)

	sessionStore := dbstore.NewSessionStore(
		dbstore.NewSessionStoreParams{
			DB: db,
		},
	)

	mediaStore := dbstore.NewMediaStore(db, logger)

	tagsStore := dbstore.NewTagsStore(db, logger)
	aestheticsStore := dbstore.NewAestheticsStore(db, logger)

	/* Static file paths */
	workDir, _ := os.Getwd()
	mediaDir := filepath.Join(workDir, cfg.StaticMediaDir, "media") // Adjust this path as needed
	logger.Info("downloadsDir", "dir", http.Dir(mediaDir))
	fileServer := http.FileServer(http.Dir(cfg.StaticDir))
	r.Handle("/static/*", http.StripPrefix("/static/", fileServer))

	MediaFileServer(r, "/media", http.Dir(mediaDir), logger)

	/* External services */
	// twitterScrapeServce := services.NewTwitterScraper()
	// telegramService := services.NewTelegramService(cfg.Telegram_API_ID, cfg.Telegram_API_Hash)
	// TODO: Handle gracefully if service is unavailable
	taggingService := external.NewTaggingService(logger, cfg.TagServicePort)
	aestheticsService := external.NewAestheticsService(logger, cfg.TagServicePort)

	mediaFileOperator := localfile.NewLocalMediaFileOperator(cfg.StaticMediaDir, cfg.RecycleDir, logger)
	mediaController := controllers.NewMediaController(mediaStore, mediaFileOperator, mediaDir)
	tagsController := controllers.NewTagsController(tagsStore, mediaStore, taggingService)
	scoreController := controllers.NewAestheticsController(aestheticsStore, mediaController, aestheticsService)

	// Middleware
	authMiddleware := m.NewAuthMiddleware(sessionStore, cfg.SessionCookieName)
	mediaItemMiddleware := m.NewMediaItemMiddleware(mediaController)

	/* Handlers */
	GlobalHandler := handlers.NewGlobalHandler()
	MediaHandler := handlers.NewMediaItemHandler(*mediaController)
	TagsHandler := handlers.NewTagsHandler(*tagsController)
	ScoreHandler := handlers.NewScoreHandler(*scoreController)
	// TwitterScrapeHandler := handlers.NewTwitterScrapeHandler(twitterScrapeServce)

	r.Group(func(r chi.Router) {
		r.Use(
			middleware.Logger,
			m.TextHTMLMiddleware,
			m.CSPMiddleware,
			authMiddleware.AddUserToContext,
			m.WithLogger(logger),
		)

		r.NotFound(handlers.NewNotFoundHandler().ServeHTTP)

		r.Get("/", handlers.NewHomeHandler(handlers.NewHomeHandlerParams{
			MediaStore: mediaStore,
			Logger:     logger,
		}).ServeHTTP)

		r.Get("/about", GlobalHandler.GetAbout)
		r.Get("/register", GlobalHandler.GetRegister)
		r.Get("/login", GlobalHandler.GetLogin)

		r.Post("/register", handlers.NewPostRegisterHandler(handlers.PostRegisterHandlerParams{
			UserStore: userStore,
		}).ServeHTTP)

		// r.Get("/scrape", TwitterScrapeHandler.ScrapeUser)
		r.Route("/tags/{mediaItemID}", func(r chi.Router) {
			r.Use(mediaItemMiddleware)
			r.Get("/", TagsHandler.GetTagsImage)
			r.Get("/generate", TagsHandler.GenerateTagsImage)
		})

		r.Route("/score/{mediaItemID}", func(r chi.Router) {
			r.Use(mediaItemMiddleware)
			r.Get("/", ScoreHandler.GetImageScore)
			r.Get("/generate", ScoreHandler.GenerateImageScore)
		})

		r.Route("/mediaItem/{mediaItemID}", func(r chi.Router) {
			r.Use(mediaItemMiddleware)
			r.Get("/", MediaHandler.GetMediaItem)
			r.Delete("/", MediaHandler.RecycleMediaItem)
			r.Post("/favorite", MediaHandler.PostFavorite)
			r.Delete("/favorite", MediaHandler.DeleteFavorite)
		})

		r.Post("/login", handlers.NewPostLoginHandler(handlers.PostLoginHandlerParams{
			UserStore:         userStore,
			SessionStore:      sessionStore,
			PasswordHash:      passwordhash,
			SessionCookieName: cfg.SessionCookieName,
		}).ServeHTTP)

		r.Post("/logout", handlers.NewPostLogoutHandler(handlers.PostLogoutHandlerParams{
			SessionCookieName: cfg.SessionCookieName,
		}).ServeHTTP)
	})

	// Listen for kill signal
	killSig := make(chan os.Signal, 1)

	signal.Notify(killSig, os.Interrupt, syscall.SIGTERM)

	srv := &http.Server{
		Addr:    "0.0.0.0" + cfg.Port,
		Handler: r,
	}

	go func() {
		err := srv.ListenAndServe()

		if errors.Is(err, http.ErrServerClosed) {
			logger.Info("Server shutdown complete")
		} else if err != nil {
			logger.Error("Server error", slog.Any("err", err))
			os.Exit(1)
		}
	}()

	logger.Info("Server started", slog.String("port", cfg.Port), slog.String("env", Environment))
	// Block until we receive a kill signal
	<-killSig

	logger.Info("Shutting down server")

	// Create a context with a timeout for shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Attempt to gracefully shut down the server
	if err := srv.Shutdown(ctx); err != nil {
		logger.Error("Server shutdown failed", slog.Any("err", err))
		os.Exit(1)
	}

	logger.Info("Server shutdown complete")
}
