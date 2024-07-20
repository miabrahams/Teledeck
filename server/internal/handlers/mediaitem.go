package handlers

import (
	"goth/internal/middleware"
	"goth/internal/store"
	"goth/internal/templates"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"
)

type MediaItemHandler struct {
	MediaStore store.MediaStore
}

func NewMediaItemHandler(store store.MediaStore) *MediaItemHandler {
	return &MediaItemHandler{MediaStore: store}
}

func (h *MediaItemHandler) GetItem(w http.ResponseWriter, r *http.Request) {

	id, err := strconv.ParseUint(r.URL.Query().Get("id"), 10, 64)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	item, err := h.MediaStore.GetMediaItem(id)
	if err != nil {
		http.Error(w, "Error fetching media item", http.StatusNotFound)
		return
	}

	err = templates.GalleryItem(item).Render(r.Context(), w)
	if err != nil {
		http.Error(w, "Error rendering gallery item", http.StatusInternalServerError)
		return
	}
}

func (h *MediaItemHandler) PostFavorite(w http.ResponseWriter, r *http.Request) {
	logger := middleware.GetLogger(r.Context())
	idStr := chi.URLParam(r, "id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	logger.Info("Toggling favorite", "id", id)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	item, err := h.MediaStore.ToggleFavorite(id)
	if err != nil {
		logger.Error("Error toggling favorite", "error", err)
		http.Error(w, "Error toggling favorite", http.StatusInternalServerError)
		return
	}
	templates.GalleryItem(item).Render(r.Context(), w)
}
