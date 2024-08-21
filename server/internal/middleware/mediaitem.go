package middleware

import (
	"context"
	"net/http"
	"teledeck/internal/controllers"

	"github.com/go-chi/chi/v5"
)

type ContextKey string

const (
	MediaItemKey ContextKey = "mediaItem"
)

func NewMediaItemMiddleware(controller *controllers.MediaController) func(http.Handler) http.Handler {
	c := controller
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			id := chi.URLParam(r, "mediaItemID")

			mediaItem, err := c.GetMediaItem(id)
			if err != nil {
				http.Error(w, "Error fetching media item", http.StatusNotFound)
				return
			}

			ctx := context.WithValue(r.Context(), MediaItemKey, mediaItem)

			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
