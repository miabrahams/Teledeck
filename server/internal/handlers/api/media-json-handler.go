// Package webapi contains API handlers for JSON requests
package webapi

import (
	"encoding/json"
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

type MediaJSONHandler struct {
	c   controllers.MediaController
	log *slog.Logger
}

func NewMediaJSONHandler(controller controllers.MediaController, log *slog.Logger) *MediaJSONHandler {
	return &MediaJSONHandler{c: controller, log: log}
}

// TODO: Make configurable
const (
	itemsPerPage = 100
)

// Wrapper function to parse query parameters for pagination and preferences
func (h *MediaJSONHandler) getWithPrefs(w http.ResponseWriter, r *http.Request, callback func(searchPrefs models.SearchPrefs, page int)) {
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

func (h *MediaJSONHandler) GetGallery(w http.ResponseWriter, r *http.Request) {
	h.getWithPrefs(w, r, func(searchPrefs models.SearchPrefs, page int) {
		items, err := h.c.GetPaginatedMediaItems(page, itemsPerPage, searchPrefs)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "Error fetching media items")
			return
		}
		writeJSON(w, http.StatusOK, items)
	})
}

func (h *MediaJSONHandler) GetThumbnail(w http.ResponseWriter, r *http.Request) {
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

func (h *MediaJSONHandler) GetGalleryIds(w http.ResponseWriter, r *http.Request) {
	h.getWithPrefs(w, r, func(searchPrefs models.SearchPrefs, page int) {
		items, err := h.c.GetPaginatedMediaItemIds(page, itemsPerPage, searchPrefs)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "Error fetching media items")
			return
		}

		writeJSON(w, http.StatusOK, items)
	})
}

// Wrapper function to retrieve media item from context and pass it to a callback
func (h *MediaJSONHandler) mediaCallback(
	w http.ResponseWriter, r *http.Request, callback func(m *models.MediaItemWithMetadata),
) {
	ctx := r.Context()
	mediaItem, ok := ctx.Value(middleware.MediaItemKey).(*models.MediaItemWithMetadata)
	if !ok {
		writeError(w, http.StatusUnprocessableEntity, "Media item not found")
		return
	}

	callback(mediaItem)
}

func (h *MediaJSONHandler) GetMediaItem(w http.ResponseWriter, r *http.Request) {
	h.mediaCallback(w, r, func(m *models.MediaItemWithMetadata) {
		writeJSON(w, http.StatusOK, m)
	})
}

func (h *MediaJSONHandler) GetNumPages(w http.ResponseWriter, r *http.Request) {
	h.getWithPrefs(w, r, func(p models.SearchPrefs, _ int) {
		mic := h.c.GetMediaItemCount(p)
		totalPages := int(math.Ceil(float64(mic) / float64(itemsPerPage)))
		h.log.Info("getNumPages", "mic", mic, "totalPages", totalPages)
		writeJSON(w, http.StatusOK, totalPages)
	})
}

func (h *MediaJSONHandler) ToggleFavorite(w http.ResponseWriter, r *http.Request) {
	h.mediaCallback(w, r, func(m *models.MediaItemWithMetadata) {
		item, err := h.c.ToggleFavorite(m.ID)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "Error toggling favorite")
			return
		}
		writeJSON(w, http.StatusOK, item)
	})
}

func (h *MediaJSONHandler) DeleteMedia(w http.ResponseWriter, r *http.Request) {
	h.mediaCallback(w, r, func(m *models.MediaItemWithMetadata) {
		h.getWithPrefs(w, r, func(p models.SearchPrefs, page int) {
			if m.Favorite {
				writeError(w, http.StatusBadRequest, "Cannot delete a favorite item")
				return
			}
			slog.Info("Deleting item", "item", m, "prefs", p, "page", page)

			nextItem, err := h.c.RecycleAndGetNext(&m.MediaItem, page, p)
			if err != nil {
				writeError(w, http.StatusInternalServerError, "Error deleting item")
				return
			}

			if nextItem == nil {
				w.WriteHeader(http.StatusNoContent)
			} else {
				slog.Info("retrieved next item", "item", nextItem)
				writeJSON(w, http.StatusOK, nextItem)
			}
		})
	})
}

type DeletePageRequest struct {
	ItemIDs []string `json:"itemIds"`
}

func (h *MediaJSONHandler) DeletePage(w http.ResponseWriter, r *http.Request) {
	var req DeletePageRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if len(req.ItemIDs) == 0 {
		writeError(w, http.StatusBadRequest, "No item IDs provided")
		return
	}

	h.getWithPrefs(w, r, func(searchPrefs models.SearchPrefs, page int) {
		// Get the current page items to verify the request
		currentPageItems, err := h.c.GetPaginatedMediaItems(page, itemsPerPage, searchPrefs)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "Error fetching current page items")
			return
		}

		// Create a map of current page item IDs for verification
		currentPageIDMap := make(map[string]bool)
		for _, item := range currentPageItems {
			currentPageIDMap[item.ID] = true
		}

		// Verify all requested IDs are actually on the current page (security measure)
		for _, id := range req.ItemIDs {
			if !currentPageIDMap[id] {
				writeError(w, http.StatusBadRequest, fmt.Sprintf("Item ID %s is not on the current page", id))
				return
			}
		}

		result, err := h.c.DeletePageItems(req.ItemIDs, page, searchPrefs)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "Error deleting page items")
			return
		}

		slog.Info("Deleted page items", "deletedCount", result.DeletedCount, "skippedCount", result.SkippedCount, "page", page)

		writeJSON(w, http.StatusOK, result)
	})
}

func (h *MediaJSONHandler) UndoDelete(w http.ResponseWriter, r *http.Request) {
	restoredItem, err := h.c.UndoLastDeleted()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Error undoing delete")
		return
	}

	if restoredItem == nil {
		writeError(w, http.StatusNotFound, "No deleted items to restore")
		return
	}

	writeJSON(w, http.StatusOK, restoredItem)
}
