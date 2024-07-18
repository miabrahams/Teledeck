package handlers

import (
	"goth/internal/store"
	"goth/internal/templates"
	"net/http"

	"strconv"
)

type MediaItemHandler struct {
	MediaStore store.MediaStore
}

type NewMediaItemHandlerParams struct {
	MediaStore store.MediaStore
}

func NewMediaItemHandler(params NewMediaItemHandlerParams) *MediaItemHandler {
	return &MediaItemHandler{}
}

func (h *MediaItemHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {

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
