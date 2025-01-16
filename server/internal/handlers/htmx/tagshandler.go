package htmxhandlers

import (
	"net/http"
	"teledeck/internal/controllers"
	m "teledeck/internal/middleware"
	"teledeck/internal/models"
	"teledeck/internal/templates"
)

type TagsHandler struct {
	tagsController *controllers.TagsController
}

func NewTagsHandler(tagsController *controllers.TagsController) *TagsHandler {
	return &TagsHandler{tagsController: tagsController}
}

func (h *TagsHandler) GetTagsImage(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	mediaItem, ok := ctx.Value(m.MediaItemKey).(*models.MediaItemWithMetadata)
	if !ok {
		status := http.StatusUnprocessableEntity
		http.Error(w, http.StatusText(status), status)
		return
	}

	tags, err := h.tagsController.GetTags(mediaItem.ID)

	if err != nil {
		http.Error(w, "Error fetching tags", http.StatusInternalServerError)
		return
	}

	err = templates.Tags(tags).Render(r.Context(), w)

	if err != nil {
		http.Error(w, "Error rendering tags", http.StatusInternalServerError)
	}
}

func (h *TagsHandler) GenerateTagsImage(w http.ResponseWriter, r *http.Request) {
	// What are the risks to not error checking here?
	ctx := r.Context()
	mediaItem, ok := ctx.Value(m.MediaItemKey).(*models.MediaItemWithMetadata)
	if !ok {
		status := http.StatusUnprocessableEntity
		http.Error(w, http.StatusText(status), status)
		return
	}

	tags, err := h.tagsController.TagImageItem(&mediaItem.MediaItem, 0.4)

	if err != nil {
		http.Error(w, "Error tagging image", http.StatusInternalServerError)
		return
	}

	err = templates.Tags(tags).Render(r.Context(), w)

	if err != nil {
		http.Error(w, "Error rendering tags", http.StatusInternalServerError)
	}

}
