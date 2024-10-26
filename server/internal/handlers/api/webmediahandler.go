package apihandlers

import (
	"net/http"
	"teledeck/internal/middleware"
	"teledeck/internal/models"
	"teledeck/internal/service/store"

	"github.com/go-chi/chi/v5"
)

type MediaJsonHandler struct {
	mediaStore store.MediaStore
}

func NewMediaJsonHandler(mediaStore store.MediaStore) *MediaJsonHandler {
	return &MediaJsonHandler{mediaStore: mediaStore}
}

func (h *MediaJsonHandler) GetMedia(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters for pagination and preferences
	page := 1
	itemsPerPage := 100 // Could make this configurable

	searchPrefs, ok := r.Context().Value(middleware.SearchPrefKey).(models.SearchPrefs)
	if !ok {
		writeError(w, http.StatusInternalServerError, "Error loading preferences")
		return
	}

	items, err := h.mediaStore.GetPaginatedMediaItems(page, itemsPerPage, searchPrefs)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Error fetching media items")
		return
	}

	writeJSON(w, http.StatusOK, items)
}

func (h *MediaJsonHandler) ToggleFavorite(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")

	item, err := h.mediaStore.ToggleFavorite(id)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Error toggling favorite")
		return
	}

	writeJSON(w, http.StatusOK, item)
}

func (h *MediaJsonHandler) DeleteMedia(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")

	item, err := h.mediaStore.GetMediaItem(id)
	if err != nil {
		writeError(w, http.StatusNotFound, "Media item not found")
		return
	}

	if item.Favorite {
		writeError(w, http.StatusBadRequest, "Cannot delete a favorite item")
		return
	}

	err = h.mediaStore.MarkDeleted(&item.MediaItem)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Error deleting item")
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
