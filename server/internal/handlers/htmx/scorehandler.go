package htmxhandlers

import (
	"net/http"
	"teledeck/internal/controllers"
	m "teledeck/internal/middleware"
	"teledeck/internal/models"
	"teledeck/internal/templates"
)

type ScoreHandler struct {
	aestheticsController controllers.AestheticsController
}

func NewScoreHandler(aestheticsController controllers.AestheticsController) *ScoreHandler {
	return &ScoreHandler{aestheticsController: aestheticsController}
}

func (h *ScoreHandler) GetImageScore(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	mediaItem, ok := ctx.Value(m.MediaItemKey).(*models.MediaItemWithMetadata)
	if !ok {
		status := http.StatusUnprocessableEntity
		http.Error(w, http.StatusText(status), status)
		return
	}

	score, err := h.aestheticsController.GetImageScore(mediaItem.ID)

	if err != nil {
		http.Error(w, "Error fetching tags", http.StatusInternalServerError)
		return
	}

	err = templates.Score(score).Render(r.Context(), w)

	if err != nil {
		http.Error(w, "Error rendering tags", http.StatusInternalServerError)
	}
}

func (h *ScoreHandler) GenerateImageScore(w http.ResponseWriter, r *http.Request) {
	// What are the risks to not error checking here?
	ctx := r.Context()
	mediaItem, ok := ctx.Value(m.MediaItemKey).(*models.MediaItemWithMetadata)
	if !ok {
		status := http.StatusUnprocessableEntity
		http.Error(w, http.StatusText(status), status)
		return
	}

	tags, err := h.aestheticsController.ScoreImageItem(&mediaItem.MediaItem)

	if err != nil {
		http.Error(w, "Error tagging image", http.StatusInternalServerError)
		return
	}

	err = templates.Score(tags).Render(r.Context(), w)

	if err != nil {
		http.Error(w, "Error rendering tags", http.StatusInternalServerError)
	}

}
