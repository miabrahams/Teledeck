package handlers

/*
import (
	"goth/internal/middleware"
	"goth/internal/store"
	"goth/internal/templates"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"
)

type FavoriteHandler struct {
	MediaStore store.MediaStore
}

func NewFavoriteHandler(mediaStore store.MediaStore) *FavoriteHandler {
	return &FavoriteHandler{MediaStore: mediaStore}
}

func (h *FavoriteHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
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
*/
