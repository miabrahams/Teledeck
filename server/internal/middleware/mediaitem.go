package middleware

import (
	"context"
	"net/http"
	"strconv"
	"teledeck/internal/controllers"
	"teledeck/internal/models"

	"github.com/go-chi/chi/v5"
)

// TODO: Rename

type ContextKey string

const (
	MediaItemKey  ContextKey = "mediaItem"
	PageKey       ContextKey = "pageNumber"
	SearchPrefKey ContextKey = "searchPrefs"
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

func SearchParamsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {

		sort := r.URL.Query().Get("sort")
		videosOnly := r.URL.Query().Get("videos") == "true"
		favorites := r.URL.Query().Get("favorites")
		search := r.URL.Query().Get("search")

		searchPrefs := models.SearchPrefs{
			Sort:       sort,
			VideosOnly: videosOnly,
			Favorites:  favorites,
			Search:     search,
		}

		ctx := r.Context()
		ctx = context.WithValue(ctx, SearchPrefKey, searchPrefs)

		page, _ := strconv.Atoi(chi.URLParam(r, "page"))
		if page == 0 {
			page = 1
		}
		ctx = context.WithValue(ctx, PageKey, page)

		next.ServeHTTP(w, r.WithContext(ctx))
	})
}
