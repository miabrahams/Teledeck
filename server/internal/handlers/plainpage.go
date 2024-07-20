package handlers

import (
	"goth/internal/templates"
	"net/http"
)

type PlainPageHandler struct{}

func NewPlainPageHandler() *PlainPageHandler {
	return &PlainPageHandler{}
}

func (h *PlainPageHandler) GetRegister(w http.ResponseWriter, r *http.Request) {
	c := templates.RegisterPage()
	err := templates.Layout(c, "My website").Render(r.Context(), w)

	if err != nil {
		http.Error(w, "Error rendering template", http.StatusInternalServerError)
		return
	}

}

func (h *PlainPageHandler) GetLogin(w http.ResponseWriter, r *http.Request) {
	c := templates.Login("Login")
	err := templates.Layout(c, "My website").Render(r.Context(), w)

	if err != nil {
		http.Error(w, "Error rendering template", http.StatusInternalServerError)
		return
	}
}
