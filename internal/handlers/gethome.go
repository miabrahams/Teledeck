package handlers

import (
	"goth/internal/middleware"
	"goth/internal/store"
	"goth/internal/templates"
	"math"
	"net/http"
	"strconv"

	"github.com/a-h/templ"
)

type HomeHandler struct {
	MediaStore store.MediaStore
}

type NewHomeHandlerParams struct {
	MediaStore store.MediaStore
}

func NewHomeHandler(params NewHomeHandlerParams) *HomeHandler {
	return &HomeHandler{MediaStore: params.MediaStore}
}

func (h *HomeHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	user, _ := r.Context().Value(middleware.UserKey).(*store.User)

	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	itemsPerPage := 100

	sort := r.URL.Query().Get("sort")
	if sort == "" {
		sort = "date_desc"
	}

	mediaItems, err := h.MediaStore.GetPaginatedMediaItems(page, itemsPerPage, sort)
	if err != nil {
		http.Error(w, "Error fetching media items", http.StatusInternalServerError)
		return
	}

	totalPages := int(math.Ceil(float64(h.MediaStore.GetTotalMediaItems()) / float64(itemsPerPage)))

	var c templ.Component
	if user != nil {
		c = templates.Index(user.Email, mediaItems, page, totalPages, sort)
	} else {
		c = templates.GuestIndex(mediaItems, page, totalPages, sort)
	}

	if r.Header.Get("HX-Request") == "true" {
		err = c.Render(r.Context(), w)
	} else {
		err = templates.Layout(c, "Media Gallery").Render(r.Context(), w)
	}
	if err != nil {
		http.Error(w, "Error rendering page", http.StatusInternalServerError)
		return
	}
}
