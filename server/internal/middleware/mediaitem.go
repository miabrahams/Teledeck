package middleware

import (
	"context"
	"goth/internal/controllers"
	"net/http"
)

type ContextKey string

const (
	MediaItemKey ContextKey = "mediaItem"
)

func NewMediaItemMiddleware(controller *controllers.MediaController) func(http.Handler) http.Handler {
	c := controller
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			id := r.PathValue("mediaItemID")

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
