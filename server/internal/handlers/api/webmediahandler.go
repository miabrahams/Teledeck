package webapi

import (
	"math"
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

const (
	itemsPerPage = 100
)

func newSearchPrefs(sort string, favorites string, videos bool, query string) models.SearchPrefs {
	return models.SearchPrefs{
		Sort:       sort,
		Favorites:  favorites,
		VideosOnly: videos,
		Search:     query,
	}
}

func (h *MediaJsonHandler) GetGallery(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters for pagination and preferences
	page := 1

	// page := chi.URLParam(r, "page")
	searchPrefs := newSearchPrefs("", "", false, "")

	items, err := h.mediaStore.GetPaginatedMediaItems(page, itemsPerPage, searchPrefs)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Error fetching media items")
		return
	}

	writeJSON(w, http.StatusOK, items)
}

func (h *MediaJsonHandler) GetMediaItem(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	mediaItem, ok := ctx.Value(middleware.MediaItemKey).(*models.MediaItemWithMetadata)
	if !ok {
		status := http.StatusUnprocessableEntity
		http.Error(w, http.StatusText(status), status)
		return
	}

	writeJSON(w, http.StatusOK, mediaItem)
}

func (h *MediaJsonHandler) GetNumPages(w http.ResponseWriter, r *http.Request) {
	searchPrefs := newSearchPrefs("", "", false, "")

	totalPages := int(math.Ceil(float64(h.mediaStore.GetMediaItemCount(searchPrefs)) / float64(itemsPerPage)))
	writeJSON(w, http.StatusOK, totalPages)
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
