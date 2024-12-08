package web

import (
	"embed"
	"io/fs"
	"log"
	"log/slog"
	"net/http"
)

//go:embed dist/*
var dist embed.FS
var srv http.Handler

func init() {
	subdir, err := fs.Sub(dist, "dist")
	if err != nil {
		log.Fatal("Could not open web asset directory: %w", err)
	}
	httpFS := http.FS(subdir)
	srv = http.FileServer(httpFS)
}

func WebFileHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		slog.Info(r.URL.Path)
		srv.ServeHTTP(w, r)
	}
}
