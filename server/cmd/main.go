package main

import (
	"context"
	"errors"
	"fmt"
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
	"strings"
	"syscall"
	"time"

	m "goth/internal/middleware"

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
func MediaFileServer(mux *http.ServeMux, path string, root http.FileSystem) {
	if strings.ContainsAny(path, "{}*") {
		panic("FileServer does not permit any URL parameters.")
	}

	// Ensure path ends with "/"
	if path != "/" && path[len(path)-1] != '/' {
		mux.HandleFunc(path, func(w http.ResponseWriter, r *http.Request) {
			fmt.Println("~~~~URL Path: ", r.URL.Path)
			http.Redirect(w, r, path+"/", http.StatusMovedPermanently)
		})
		path += "/"
	}
	path += "*"

	rootServer := http.FileServer(root)

	mux.HandleFunc(path, func(w http.ResponseWriter, r *http.Request) {
		r.URL.Path = strings.TrimSuffix(r.URL.Path, path)
		fmt.Println("~~~~URL Path: ", r.URL.Path)
		fmt.Println("Root: " + path)
		rootServer.ServeHTTP(w, r)
	})
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	err := godotenv.Load("../.env")
	if err != nil {
		logger.Error("Error loading .env file")
		return
	}

	htmlMux := http.NewServeMux()
	staticMux := http.NewServeMux()
	globalMux := http.NewServeMux()

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

	/* External services */
	// twitterScrapeServce := services.NewTwitterScraper()
	// telegramService := services.NewTelegramService(cfg.Telegram_API_ID, cfg.Telegram_API_Hash)

	// TODO: Handle gracefully if service is unavailable
	taggingService := external.NewTaggingService(logger, cfg.TagServicePort)

	mediaFileOperator := localfile.NewLocalMediaFileOperator(cfg.StaticMediaDir, cfg.RecycleDir, logger)
	mediaController := controllers.NewMediaController(mediaStore, mediaFileOperator)
	tagsController := controllers.NewTagsController(tagsStore, mediaStore, taggingService)

	// Middleware
	authMiddleware := m.NewAuthMiddleware(sessionStore, cfg.SessionCookieName)
	mediaItemMiddleware := m.NewMediaItemMiddleware(mediaController)

	/* Serve static media */
	MediaFileServer(staticMux, "/static/", http.Dir(cfg.StaticDir))

	MediaFileServer(staticMux, "/media/", http.Dir(cfg.StaticMediaDir))

	/* Handlers */
	GlobalHandler := handlers.NewGlobalHandler()
	MediaHandler := handlers.NewMediaItemHandler(*mediaController)
	TagsHandler := handlers.NewTagsHandler(*tagsController)
	homeHandler := handlers.NewHomeHandler(handlers.NewHomeHandlerParams{
		MediaStore: mediaStore,
		Logger:     logger})
	notFoundHandler := handlers.NewNotFoundHandler()
	// TwitterScrapeHandler := handlers.NewTwitterScrapeHandler(twitterScrapeServce)

	/* text/plain */
	// 404
	htmlMux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		logger.Info("home", slog.String("path", r.URL.Path))
		if r.URL.Path != "/" {
			notFoundHandler.ServeHTTP(w, r)
			logger.Info("404", slog.String("path", r.URL.Path))

		} else {
			homeHandler.ServeHTTP(w, r)
		}
	})
	logger.Info("Hi!")

	htmlMux.HandleFunc("GET /about", GlobalHandler.GetAbout)
	// r.Get("/scrape", TwitterScrapeHandler.ScrapeUser)

	// Tags routes
	tagsRouter := http.NewServeMux()
	tagsRouter.HandleFunc("GET /", TagsHandler.GetTagsImage)
	tagsRouter.HandleFunc("GET /generate", TagsHandler.GenerateTagsImage)
	htmlMux.Handle("/tags/", mediaItemMiddleware(http.StripPrefix("/tags", tagsRouter)))

	// Media Item routes
	mediaItemRouter := http.NewServeMux()
	mediaItemRouter.HandleFunc("GET /{mediaItemID}", MediaHandler.GetMediaItem)
	mediaItemRouter.HandleFunc("DELETE /{mediaItemID}", MediaHandler.RecycleMediaItem)
	mediaItemRouter.HandleFunc("POST /{mediaItemID}/favorite", MediaHandler.PostFavorite)
	mediaItemRouter.HandleFunc("DELETE /{mediaItemID}/favorite", MediaHandler.DeleteFavorite)
	htmlMux.Handle("/mediaItem/", mediaItemMiddleware(http.StripPrefix("/mediaItem", mediaItemRouter)))

	// Auth routes
	htmlMux.HandleFunc("GET /register", GlobalHandler.GetRegister)
	htmlMux.HandleFunc("GET /login", GlobalHandler.GetLogin)
	htmlMux.HandleFunc("POST /register", handlers.NewPostRegisterHandler(handlers.PostRegisterHandlerParams{
		UserStore: userStore,
	}).ServeHTTP)

	htmlMux.HandleFunc("POST /login", handlers.NewPostLoginHandler(handlers.PostLoginHandlerParams{
		UserStore:         userStore,
		SessionStore:      sessionStore,
		PasswordHash:      passwordhash,
		SessionCookieName: cfg.SessionCookieName,
	}).ServeHTTP)

	htmlMux.HandleFunc("POST /logout", handlers.NewPostLogoutHandler(handlers.PostLogoutHandlerParams{
		SessionCookieName: cfg.SessionCookieName,
	}).ServeHTTP)

	// Apply middleware
	htmlHandler := m.TextHTMLMiddleware(htmlMux)
	htmlHandler = m.CSPMiddleware(htmlHandler)
	htmlHandler = authMiddleware.AddUserToContext(htmlHandler)
	htmlHandler = m.WithLogger(logger)(htmlHandler)

	globalMux.Handle("/static/", staticMux)
	globalMux.Handle("/media/", staticMux)
	globalMux.Handle("/", htmlHandler)

	// Listen for kill signal
	killSig := make(chan os.Signal, 1)
	signal.Notify(killSig, os.Interrupt, syscall.SIGTERM)

	srv := &http.Server{
		Addr:    "0.0.0.0" + cfg.Port,
		Handler: globalMux,
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
