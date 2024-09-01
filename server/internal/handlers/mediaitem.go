package handlers

import (
	"net/http"
	"teledeck/internal/controllers"
	m "teledeck/internal/middleware"
	"teledeck/internal/models"
	"teledeck/internal/templates"

	"github.com/go-chi/chi/v5"
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
	id := chi.URLParam(r, "id")
	logger.Info("Toggling favorite", "id", id)
	item, err := h.controller.ToggleFavorite(id)
	if err != nil {
		logger.Error("Error toggling favorite", "error", err)
		http.Error(w, "Error toggling favorite", http.StatusInternalServerError)
		return
	}
	templates.GalleryItem(item).Render(r.Context(), w)
}

func (h *MediaItemHandler) RecycleAndGetNext(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	mediaItem, ok := ctx.Value(m.MediaItemKey).(*models.MediaItemWithMetadata)
	page, ok2 := ctx.Value(m.PageKey).(int)
	searchPrefs, ok3 := ctx.Value(m.SearchPrefKey).(models.SearchPrefs)
	if !ok {
		status := http.StatusUnprocessableEntity
		http.Error(w, http.StatusText(status), status)
		return
	}

	if !ok2 || !ok3 {
		http.Error(w, "Error loading settings", http.StatusInternalServerError)
		return
	}

	if mediaItem.Favorite {
		http.Error(w, "Cannot delete a favorite item", http.StatusBadRequest)
		return
	}

	nextItem, err := h.controller.RecycleAndGetNext(&mediaItem.MediaItem, page, searchPrefs)
	if err != nil {
		http.Error(w, "Error deleting gallery item", http.StatusInternalServerError)
		return
	}
	templates.ReplacementGalleryItem(nextItem).Render(r.Context(), w)
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
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(""))
}
