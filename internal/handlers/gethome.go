package handlers

import (
	"goth/internal/middleware"
	"goth/internal/store"
	"goth/internal/templates"
	"net/http"
    "github.com/a-h/templ"
)

type HomeHandler struct {
    MediaItems []store.MediaItem
}

func NewHomeHandler(mediaItems []store.MediaItem) *HomeHandler {
    return &HomeHandler{MediaItems: mediaItems}
}

func (h *HomeHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    user, _ := r.Context().Value(middleware.UserKey).(*store.User)

    var c templ.Component
    if user != nil {
        c = templates.Index(user.Email, h.MediaItems)
    } else {
        c = templates.GuestIndex(h.MediaItems)
    }

    err := templates.Layout(c, "Media Gallery").Render(r.Context(), w)
    if err != nil {
        http.Error(w, "Error rendering template", http.StatusInternalServerError)
        return
    }
}
