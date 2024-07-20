package handlers

import (
	"goth/internal/templates"

	"net/http"
)

type NotFoundHandler struct{}

func NewNotFoundHandler() *NotFoundHandler {
	return &NotFoundHandler{}
}

func (h *NotFoundHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	err := templates.NotFound().Render(r.Context(), w)
	if err != nil {
		http.Error(w, "Page not found.", http.StatusNotFound)
		return
	}
}
