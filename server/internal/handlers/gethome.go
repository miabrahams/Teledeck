package handlers

import (
	"goth/internal/middleware"
	"goth/internal/store"
	"goth/internal/templates"
	"math"
	"net/http"
	"strconv"

	"log/slog"

	"github.com/a-h/templ"
)

type HomeHandler struct {
	MediaStore store.MediaStore
	logger     *slog.Logger
}

type NewHomeHandlerParams struct {
	MediaStore store.MediaStore
	Logger     *slog.Logger
}

func NewHomeHandler(params NewHomeHandlerParams) *HomeHandler {
	return &HomeHandler{MediaStore: params.MediaStore, logger: params.Logger}
}

func (h *HomeHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	user, _ := r.Context().Value(middleware.UserKey).(*store.User)
	h.logger.Info("Handling request: ", "URL", r.URL, "Query", r.URL.Query())

	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	itemsPerPage := 100

	sort := r.URL.Query().Get("sort")
	if sort == "" {
		sort = "date_desc"
	}

	videos := r.URL.Query().Get("videos")
	only_videos := false
	if videos == "true" {
		only_videos = true
	}

	mediaItems, err := h.MediaStore.GetPaginatedMediaItems(page, itemsPerPage, sort, only_videos)
	if err != nil {
		http.Error(w, "Error fetching media items", http.StatusInternalServerError)
		return
	}

	totalPages := int(math.Ceil(float64(h.MediaStore.GetTotalMediaItems(only_videos)) / float64(itemsPerPage)))

	gallery := templates.Gallery(mediaItems, page, totalPages, sort, videos)

	var index templ.Component
	if user != nil {
		index = templates.Index(user.Email, gallery)
	} else {
		index = templates.GuestIndex(gallery)
	}

	if r.Header.Get("HX-Request") == "true" {
		err = index.Render(r.Context(), w)
	} else {
		err = templates.Layout(index, "Media Gallery").Render(r.Context(), w)
	}
	if err != nil {
		http.Error(w, "Error rendering page", http.StatusInternalServerError)
		return
	}
}
