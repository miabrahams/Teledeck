package webapi

import (
	"math"
	"net/http"
	"teledeck/internal/middleware"
	"teledeck/internal/models"
	"teledeck/internal/service/store"
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

func (h *MediaJsonHandler) GetGalleryIds(w http.ResponseWriter, r *http.Request) {
	page := 1
	searchPrefs := newSearchPrefs("", "", false, "")

	items, err := h.mediaStore.GetPaginatedMediaItemIds(page, itemsPerPage, searchPrefs)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Error fetching media items")
		return
	}

	writeJSON(w, http.StatusOK, items)
}

func (h *MediaJsonHandler) mediaCallback(
	w http.ResponseWriter,
	r *http.Request,
	callback func(m *models.MediaItemWithMetadata),
) {
	ctx := r.Context()
	mediaItem, ok := ctx.Value(middleware.MediaItemKey).(*models.MediaItemWithMetadata)
	if !ok {
		writeError(w, http.StatusUnprocessableEntity, "Media item not found")
		return
	}

	callback(mediaItem)
}

func (h *MediaJsonHandler) GetMediaItem(w http.ResponseWriter, r *http.Request) {
	h.mediaCallback(w, r, func(m *models.MediaItemWithMetadata) {
		writeJSON(w, http.StatusOK, m)
	})
}

func (h *MediaJsonHandler) GetNumPages(w http.ResponseWriter, r *http.Request) {
	searchPrefs := newSearchPrefs("", "", false, "")

	totalPages := int(math.Ceil(float64(h.mediaStore.GetMediaItemCount(searchPrefs)) / float64(itemsPerPage)))
	writeJSON(w, http.StatusOK, totalPages)
}

func (h *MediaJsonHandler) ToggleFavorite(w http.ResponseWriter, r *http.Request) {
	h.mediaCallback(w, r, func(m *models.MediaItemWithMetadata) {
		item, err := h.mediaStore.ToggleFavorite(m.ID)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "Error toggling favorite")
			return
		}
		writeJSON(w, http.StatusOK, item)
	})
}

func (h *MediaJsonHandler) DeleteMedia(w http.ResponseWriter, r *http.Request) {
	h.mediaCallback(w, r, func(m *models.MediaItemWithMetadata) {
		if m.Favorite {
			writeError(w, http.StatusBadRequest, "Cannot delete a favorite item")
			return
		}

		if err := h.mediaStore.MarkDeleted(&m.MediaItem); err != nil {
			writeError(w, http.StatusInternalServerError, "Error deleting item")
			return
		}

		w.WriteHeader(http.StatusNoContent)
	})
}
