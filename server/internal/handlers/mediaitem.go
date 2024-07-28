package handlers

import (
	"goth/internal/controllers"
	m "goth/internal/middleware"
	"goth/internal/models"
	"goth/internal/templates"
	"net/http"
)

type MediaItemHandler struct {
	controller controllers.MediaController
}

func NewMediaItemHandler(controller controllers.MediaController) *MediaItemHandler {
	return &MediaItemHandler{controller: controller}
}

func (h *MediaItemHandler) GetMediaItem(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	mediaItem, ok := ctx.Value(m.MediaItemKey).(*models.MediaItemWithMetadata)
	if !ok {
		status := http.StatusUnprocessableEntity
		http.Error(w, http.StatusText(status), status)
		return
	}

	err := templates.GalleryItem(mediaItem).Render(r.Context(), w)
	if err != nil {
		http.Error(w, "Error rendering gallery item", http.StatusInternalServerError)
		return
	}
}

func (h *MediaItemHandler) PostFavorite(w http.ResponseWriter, r *http.Request) {
	// What are the risks to not error checking here?
	ctx := r.Context()
	mediaItem, ok := ctx.Value(m.MediaItemKey).(*models.MediaItemWithMetadata)
	if !ok {
		status := http.StatusUnprocessableEntity
		http.Error(w, http.StatusText(status), status)
		return
	}

	item, err := h.controller.ToggleFavorite(mediaItem.ID)
	if err != nil {
		http.Error(w, "Error toggling favorite", http.StatusInternalServerError)
		return
	}
	templates.GalleryItem(item).Render(r.Context(), w)
}

func (h *MediaItemHandler) DeleteFavorite(w http.ResponseWriter, r *http.Request) {
	logger := m.GetLogger(r.Context())
	id := r.PathValue("id")
	logger.Info("Toggling favorite", "id", id)
	item, err := h.controller.ToggleFavorite(id)
	if err != nil {
		logger.Error("Error toggling favorite", "error", err)
		http.Error(w, "Error toggling favorite", http.StatusInternalServerError)
		return
	}
	templates.GalleryItem(item).Render(r.Context(), w)
}

func (h *MediaItemHandler) RecycleMediaItem(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	mediaItem, ok := ctx.Value(m.MediaItemKey).(*models.MediaItemWithMetadata)
	if !ok {
		status := http.StatusUnprocessableEntity
		http.Error(w, http.StatusText(status), status)
		return
	}
	if mediaItem.Favorite {
		http.Error(w, "Cannot delete a favorite item", http.StatusBadRequest)
		return
	}

	err := h.controller.RecycleMediaItem(mediaItem.MediaItem)
	if err != nil {
		http.Error(w, "Error deleting gallery item", http.StatusInternalServerError)
		return
	}
	// Send status OK with empty body
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(""))
}
