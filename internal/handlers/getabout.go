package handlers

import (
	"goth/internal/templates"
	"net/http"
)

type AboutHandLer struct{}

func NewAboutHandler() *AboutHandLer {
	return &AboutHandLer{}
}

func (h *AboutHandLer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	c := templates.About()
	err := templates.Layout(c, "Telegram Media Gallery").Render(r.Context(), w)

	if err != nil {
		// There may be a better way to handle this error.
		http.Error(w, "Error rendering template", http.StatusInternalServerError)
		return
	}
}
