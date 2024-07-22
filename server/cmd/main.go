package main

import (
	"context"
	"errors"
	"goth/internal/config"
	"goth/internal/fileops/localfile"
	"goth/internal/handlers"
	"goth/internal/hash/passwordhash"
	"goth/internal/services"
	database "goth/internal/store/db"
	"goth/internal/store/dbstore"
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

	mediaStore := dbstore.NewMediaStore(
		dbstore.NewMediaStoreParams{
			DB: db,
		},
	)

	authMiddleware := m.NewAuthMiddleware(sessionStore, cfg.SessionCookieName)

	/* Serve static media */
	fileServer := http.FileServer(http.Dir(cfg.StaticDir))
	r.Handle("/static/*", http.StripPrefix("/static/", fileServer))

	workDir, _ := os.Getwd()
	mediaDir := filepath.Join(workDir, cfg.StaticMediaDir, "media") // Adjust this path as needed
	logger.Info("downloadsDir", "dir", http.Dir(mediaDir))
	MediaFileServer(r, "/media", http.Dir(mediaDir), logger)

	mediaFileOperator := localfile.NewLocalMediaFileOperator(cfg.StaticMediaDir, cfg.RecycleDir, logger)
	mediaService := services.NewMediaService(mediaStore, mediaFileOperator)

	/* Handlers */
	MediaHandler := handlers.NewMediaItemHandler(*mediaService)
	GlobalHandler := handlers.NewGlobalHandler()

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

		r.Route("/mediaItem/{mediaItemID}", func(r chi.Router) {
			r.Use(MediaHandler.MediaItemCtx)
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
