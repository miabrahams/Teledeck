package webapi

import (
	"errors"
	"fmt"
	"log/slog"
	"math"
	"net/http"
	"teledeck/internal/controllers"
	"teledeck/internal/middleware"
	"teledeck/internal/models"

	"github.com/go-chi/chi/v5"
)

type MediaJsonHandler struct {
	c   *controllers.MediaController
	log *slog.Logger
}

func NewMediaJsonHandler(controller *controllers.MediaController, log *slog.Logger) *MediaJsonHandler {
	return &MediaJsonHandler{c: controller, log: log}
}

// TODO: Make configurable
const (
	itemsPerPage = 100
)

/*
func newSearchPrefs(sort string, favorites string, videos bool, query string) models.SearchPrefs {
	return models.SearchPrefs{
		Sort:       sort,
		Favorites:  favorites,
		VideosOnly: videos,
		Search:     query,
	}
}
*/

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
		items, err := h.c.GetPaginatedMediaItems(page, itemsPerPage, searchPrefs)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "Error fetching media items")
			return
		}
		writeJSON(w, http.StatusOK, items)
	})
}

func (h *MediaJsonHandler) GetThumbnail(w http.ResponseWriter, r *http.Request) {
	mediaItemID := chi.URLParam(r, "mediaItemID")

	fileName, err := h.c.GetThumbnail(mediaItemID)
	if errors.Is(err, controllers.ErrThumbnailInProgress) {
		writeJSON(w, http.StatusAccepted, map[string]string{"message": "Thumbnail generation in progress"})
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, fmt.Sprintf("Error generating thumbnail: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"fileName": fileName})
}

func (h *MediaJsonHandler) GetGalleryIds(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters for pagination and preferences
	h.getWithPrefs(w, r, func(searchPrefs models.SearchPrefs, page int) {
		items, err := h.c.GetPaginatedMediaItemIds(page, itemsPerPage, searchPrefs)
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
		mic := h.c.GetMediaItemCount(p)
		totalPages := int(math.Ceil(float64(mic) / float64(itemsPerPage)))
		h.log.Info("getNumPages", "mic", mic, "totalPages", totalPages)
		writeJSON(w, http.StatusOK, totalPages)
	})
}

func (h *MediaJsonHandler) ToggleFavorite(w http.ResponseWriter, r *http.Request) {
	h.mediaCallback(w, r, func(m *models.MediaItemWithMetadata) {
		item, err := h.c.ToggleFavorite(m.ID)
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

		if err := h.c.RecycleMediaItem(m.MediaItem); err != nil {
			writeError(w, http.StatusInternalServerError, "Error deleting item")
			return
		}

		w.WriteHeader(http.StatusNoContent)
	})
}
