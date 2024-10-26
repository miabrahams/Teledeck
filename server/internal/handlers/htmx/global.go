package htmxhandlers

import (
	"net/http"
	"teledeck/internal/templates"
)

type GlobalHandler struct{}

func NewGlobalHandler() *GlobalHandler {
	return &GlobalHandler{}
}

func (h *GlobalHandler) GetRegister(w http.ResponseWriter, r *http.Request) {
	c := templates.RegisterPage()
	err := templates.Layout(c, "My website").Render(r.Context(), w)

	if err != nil {
		http.Error(w, "Error rendering template", http.StatusInternalServerError)
		return
	}

}

func (h *GlobalHandler) GetLogin(w http.ResponseWriter, r *http.Request) {
	c := templates.Login("Login")
	err := templates.Layout(c, "My website").Render(r.Context(), w)

	if err != nil {
		http.Error(w, "Error rendering template", http.StatusInternalServerError)
		return
	}
}

func (h *GlobalHandler) GetAbout(w http.ResponseWriter, r *http.Request) {
	c := templates.About()
	err := templates.Layout(c, "Telegram Media Gallery").Render(r.Context(), w)

	if err != nil {
		// There may be a better way to handle this error.
		http.Error(w, "Error rendering template", http.StatusInternalServerError)
		return
	}
}
