package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"teledeck/internal/config"
	"teledeck/internal/controllers"
	api "teledeck/internal/handlers/api"
	hx "teledeck/internal/handlers/htmx"
	external "teledeck/internal/service/external/api"
	"teledeck/internal/service/files/localfile"
	"teledeck/internal/service/hash/passwordhash"
	database "teledeck/internal/service/store/db"
	"teledeck/internal/service/store/dbstore"
	"teledeck/internal/service/web"
	"time"

	m "teledeck/internal/middleware"

	"github.com/go-chi/chi/v5"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

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

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	err := godotenv.Load("../.env")
	if err != nil {
		logger.Error("Error loading .env file")
		return
	}

	cfg := config.MustLoadConfig()

	/* Register Database Stores */
	db := database.MustOpen(cfg.DatabaseName)
	mediaStore := dbstore.NewMediaStore(db, logger)
	tagsStore := dbstore.NewTagsStore(db, logger)
	aestheticsStore := dbstore.NewAestheticsStore(db, logger)

	passwordhash := passwordhash.NewHPasswordHash()
	userStore := dbstore.NewUserStore(
		dbstore.NewUserStoreParams{DB: db, PasswordHash: passwordhash},
	)
	sessionStore := dbstore.NewSessionStore(
		dbstore.NewSessionStoreParams{DB: db},
	)

	/* Static file paths */
	pwd, err := os.Getwd()
	if err != nil {
		logger.Error("could not read working directory", slog.Any("err", err))
		os.Exit(1)
	}
	mediaDir := cfg.MediaDir(pwd)
	logger.Info("Media folder", "dir", mediaDir)

	r := chi.NewMux()
	StaticFileServer(r, "/media", mediaDir, cfg.StaticDir)

	/* External services */
	// twitterScrapeServce := services.NewTwitterScraper()
	// telegramService := services.NewTelegramService(cfg.Telegram_API_ID, cfg.Telegram_API_Hash)

	// TODO: Better handling for unavailable services
	conn, err := grpc.NewClient(cfg.TaggerURL, grpc.WithTransportCredentials(insecure.NewCredentials()))
	var taggingService *external.TaggingService
	var aestheticsService *external.AestheticsService
	if err != nil {
		logger.Info("Could not connect to AI services.")
	} else {
		taggingService = external.NewTaggingService(logger, conn)
		aestheticsService = external.NewAestheticsService(logger, conn)
	}

	mediaFileOperator := localfile.NewLocalMediaFileOperator(cfg.StaticMediaDir, cfg.RecycleDir, logger)
	mediaController := controllers.NewMediaController(mediaStore, mediaFileOperator, mediaDir)
	tagsController := controllers.NewTagsController(tagsStore, mediaStore, taggingService)
	scoreController := controllers.NewAestheticsController(aestheticsStore, mediaController, aestheticsService)

	// Middleware
	authMiddleware := m.NewAuthMiddleware(sessionStore, cfg.SessionCookieName)
	mediaItemMiddleware := m.NewMediaItemMiddleware(mediaController)

	/* Handlers */
	hxTagsHandler := hx.NewTagsHandler(*tagsController)
	hxScoreHandler := hx.NewScoreHandler(*scoreController)
	hxGlobalHandler := hx.NewGlobalHandler()
	hxHomeHandler := hx.NewHomeHandler(hx.NewHomeHandlerParams{
		MediaStore: mediaStore,
		Logger:     logger,
	})
	hxMediaHandler := hx.NewMediaItemHandler(*mediaController)
	hxUserHandler := hx.NewUserHandler(hx.UserHandlerParams{
		UserStore:         userStore,
		SessionStore:      sessionStore,
		PasswordHash:      passwordhash,
		SessionCookieName: cfg.SessionCookieName,
	})

	// TwitterScrapeHandler := handlers.NewTwitterScrapeHandler(twitterScrapeServce)

	mediaJsonHandler := api.NewMediaJsonHandler(mediaStore, logger)

	webFileHandler := web.WebFileHandler()

	r.Group(func(r chi.Router) {
		r.Use(
			// middleware.Logger,
			m.CSPMiddleware,
			authMiddleware.AddUserToContext,
			m.WithLogger(logger),
		)

		r.Group(func(r chi.Router) {
			r.Use(m.TextHTMLMiddleware)
			r.NotFound(hx.NewNotFoundHandler().ServeHTTP)

			r.Get("/about", hxGlobalHandler.GetAbout)
			r.Get("/register", hxGlobalHandler.GetRegister)
			r.Get("/login", hxGlobalHandler.GetLogin)

			r.Post("/register", hxUserHandler.PostRegister)
			r.Post("/login", hxUserHandler.PostLogin)
			r.Post("/logout", hxUserHandler.PostLogout)

			r.Group(func(r chi.Router) {
				r.Use(m.SearchParamsMiddleware)

				r.Route("/x", func(r chi.Router) {
					r.Get("/", hxHomeHandler.ServeHTTP)

					r.Route("/mediaItem/{mediaItemID}", func(r chi.Router) {
						r.Use(mediaItemMiddleware)
						r.Get("/", hxMediaHandler.GetMediaItem)
						r.Delete("/", hxMediaHandler.RecycleAndGetNext)
						r.Post("/favorite", hxMediaHandler.PostFavorite)
						r.Delete("/favorite", hxMediaHandler.DeleteFavorite)
					})
				})
			})

			// r.Get("/scrape", TwitterScrapeHandler.ScrapeUser)
			r.Route("/tags/{mediaItemID}", func(r chi.Router) {
				r.Use(mediaItemMiddleware)
				r.Get("/", hxTagsHandler.GetTagsImage)
				r.Get("/generate", hxTagsHandler.GenerateTagsImage)
			})

			r.Route("/score/{mediaItemID}", func(r chi.Router) {
				r.Use(mediaItemMiddleware)
				r.Get("/", hxScoreHandler.GetImageScore)
				r.Get("/generate", hxScoreHandler.GenerateImageScore)
			})

			r.Get("/", webFileHandler)
		})

		r.Get("/assets/{x}", webFileHandler)

		r.Route("/api", func(r chi.Router) {
			r.Use(m.SearchParamsMiddleware)
			r.Get("/gallery", mediaJsonHandler.GetGallery)
			r.Get("/gallery/totalPages", mediaJsonHandler.GetNumPages)
			r.Get("/gallery/ids", mediaJsonHandler.GetGalleryIds)
			r.Route("/media/{mediaItemID}", func(r chi.Router) {
				r.Use(mediaItemMiddleware)
				r.Get("/", mediaJsonHandler.GetMediaItem)
				r.Delete("/", mediaJsonHandler.DeleteMedia)
				r.Post("/favorite", mediaJsonHandler.ToggleFavorite)
			})
		})
	})

	srv := &http.Server{
		Addr:    "0.0.0.0" + cfg.Port,
		Handler: r,
	}

	wg := sync.WaitGroup{}

	// Listen for traffic
	wg.Add(1)
	go func() {
		defer wg.Done()
		err := srv.ListenAndServe()

		if errors.Is(err, http.ErrServerClosed) {
			logger.Info("Server shutdown complete")
		} else if err != nil {
			logger.Error("Server error", slog.Any("err", err))
			os.Exit(1)
		}
	}()

	logger.Info("Server started", slog.String("port", cfg.Port), slog.String("env", Environment))

	// Kill signal will request shutdown
	killSig := make(chan os.Signal, 1)
	go func() {
		signal.Notify(killSig, os.Interrupt, syscall.SIGTERM)
		<-killSig

		// Attempt to gracefully shut down the server
		logger.Info("Shutting down server")
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := srv.Shutdown(ctx); err != nil {
			logger.Error("Server shutdown failed", slog.Any("err", err))
			os.Exit(1)
		}
	}()

	// Block until shutdown
	wg.Wait()

	logger.Info("Server shutdown complete")
}

// FileServer conveniently sets up a http.FileServer handler to serve static files from a http.FileSystem.
// Installs static files on /static (js, css etc) and media files on [path]
func StaticFileServer(r chi.Router, path string, mediaDir string, staticDir string) {

	fileServer := http.FileServer(http.Dir(staticDir))
	r.Handle("/static/*", http.StripPrefix("/static/", fileServer))

	if strings.ContainsAny(path, "{}*") {
		panic("FileServer does not permit any URL parameters.")
	}

	// Ensure path is formatted correctly and ends with '/'
	if path != "/" && path[len(path)-1] != '/' {
		r.Get(path, http.RedirectHandler(path+"/", http.StatusMovedPermanently).ServeHTTP)
		path += "/"
	}

	mediaRoot := http.Dir(mediaDir)
	// Ensure exists??

	r.Get(path+"*", func(w http.ResponseWriter, r *http.Request) {
		rctx := chi.RouteContext(r.Context())
		pathPrefix := strings.TrimSuffix(rctx.RoutePattern(), "/*")
		fs := http.StripPrefix(pathPrefix, http.FileServer(mediaRoot))
		fs.ServeHTTP(w, r)
	})
}
