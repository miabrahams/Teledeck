package webapi

import (
	"fmt"
	"log/slog"
	"math"
	"net/http"
	"teledeck/internal/middleware"
	"teledeck/internal/models"
	"teledeck/internal/service/store"
)

type MediaJsonHandler struct {
	mediaStore store.MediaStore
	log        *slog.Logger
}

func NewMediaJsonHandler(mediaStore store.MediaStore, log *slog.Logger) *MediaJsonHandler {
	return &MediaJsonHandler{mediaStore: mediaStore, log: log}
}

// TODO: Make configurable
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

func (h *MediaJsonHandler) getWithPrefs(w http.ResponseWriter, r *http.Request, callback func(searchPrefs models.SearchPrefs, page int)) {
	// Parse query parameters for pagination and preferences
	ctx := r.Context()
	searchPrefs, ok := ctx.Value(middleware.SearchPrefKey).(models.SearchPrefs)
	if !ok {
		writeError(w, http.StatusInternalServerError, "Error fetching preferences")
		return
	}
	page, ok := ctx.Value(middleware.PageKey).(int)
	if !ok {
		fmt.Printf("Error reading page number")
		return
	}

	callback(searchPrefs, page)
}

func (h *MediaJsonHandler) GetGallery(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters for pagination and preferences
	h.getWithPrefs(w, r, func(searchPrefs models.SearchPrefs, page int) {
		items, err := h.mediaStore.GetPaginatedMediaItems(page, itemsPerPage, searchPrefs)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "Error fetching media items")
			return
		}
		writeJSON(w, http.StatusOK, items)
	})
}

func (h *MediaJsonHandler) GetGalleryIds(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters for pagination and preferences
	h.getWithPrefs(w, r, func(searchPrefs models.SearchPrefs, page int) {
		items, err := h.mediaStore.GetPaginatedMediaItemIds(page, itemsPerPage, searchPrefs)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "Error fetching media items")
			return
		}

		writeJSON(w, http.StatusOK, items)
	})
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
	h.getWithPrefs(w, r, func(p models.SearchPrefs, _ int) {
		mic := h.mediaStore.GetMediaItemCount(p)
		totalPages := int(math.Ceil(float64(mic) / float64(itemsPerPage)))
		h.log.Info("getNumPages", "mic", mic, "totalPages", totalPages)
		writeJSON(w, http.StatusOK, totalPages)
	})
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
