package main

import (
	"context"
	"errors"
	"goth/internal/config"
	"goth/internal/handlers"
	"goth/internal/hash/passwordhash"
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

    "encoding/json"
    "io/ioutil"
    "goth/internal/store"
    "path/filepath"
	"strings"
)

/*
* Set to production at build time
* used to determine what assets to load
 */
var Environment = "development"

func init() {
	os.Setenv("env", Environment)
}


// Add this function to load media items
func loadMediaItems(filename string) ([]store.MediaItem, error) {
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var mediaItems []store.MediaItem
	err = json.Unmarshal(data, &mediaItems)
	if err != nil {
		return nil, err
	}


	for i := range mediaItems{
		downloadIndex := strings.Index(mediaItems[i].Path, "/downloads")
		if downloadIndex != -1 {
			mediaItems[i].Path = mediaItems[i].Path[downloadIndex + 11:]
		} else {
			mediaItems[i].Path = filepath.Base(mediaItems[i].Path)
		}

		if !strings.HasPrefix(mediaItems[i].Path, "/") {
			mediaItems[i].Path = "/" + mediaItems[i].Path
		}
	}
	return mediaItems, nil
}

// FileServer conveniently sets up a http.FileServer handler to serve
// static files from a http.FileSystem.
func DownloadFileServer(r chi.Router, path string, root http.FileSystem, logger *slog.Logger) {
    if strings.ContainsAny(path, "{}*") {
        panic("FileServer does not permit any URL parameters.")
    }

    if path != "/" && path[len(path)-1] != '/' {
        r.Get(path, http.RedirectHandler(path+"/", 301).ServeHTTP)
        path += "/"
    }
    path += "*"

	rootServer := http.FileServer(root)

    r.Get(path, func(w http.ResponseWriter, r *http.Request) {
        rctx := chi.RouteContext(r.Context())
        pathPrefix := strings.TrimSuffix(rctx.RoutePattern(), "/*")
        fs := http.StripPrefix(pathPrefix, rootServer)
		logger.Info("Requesting path: ", "Path", r.URL.Path, "fs", fs)
        fs.ServeHTTP(w, r)
    })
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
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

	authMiddleware := m.NewAuthMiddleware(sessionStore, cfg.SessionCookieName)

	/* Static media handlers */
	fileServer := http.FileServer(http.Dir("./static"))
	r.Handle("/static/*", http.StripPrefix("/static/", fileServer))

    workDir, _ := os.Getwd()
    downloadsDir := filepath.Join(workDir, "../", "downloads") // Adjust this path as needed
	logger.Info("downloadsDir", "dir", http.Dir(downloadsDir))
    DownloadFileServer(r, "/downloads", http.Dir(downloadsDir), logger)

    mediaItems, err := loadMediaItems("media_data.json")
    if err != nil {
        logger.Error("Failed to load media items", slog.Any("err", err))
        os.Exit(1)
    }


	r.Group(func(r chi.Router) {
		r.Use(
			middleware.Logger,
			m.TextHTMLMiddleware,
			m.CSPMiddleware,
			authMiddleware.AddUserToContext,
		)

		r.NotFound(handlers.NewNotFoundHandler().ServeHTTP)

        r.Get("/", handlers.NewHomeHandler(mediaItems).ServeHTTP)

		r.Get("/about", handlers.NewAboutHandler().ServeHTTP)

		r.Get("/register", handlers.NewGetRegisterHandler().ServeHTTP)

		r.Post("/register", handlers.NewPostRegisterHandler(handlers.PostRegisterHandlerParams{
			UserStore: userStore,
		}).ServeHTTP)

		r.Get("/login", handlers.NewGetLoginHandler().ServeHTTP)

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

	killSig := make(chan os.Signal, 1)

	signal.Notify(killSig, os.Interrupt, syscall.SIGTERM)

	srv := &http.Server{
		Addr:    cfg.Port,
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
