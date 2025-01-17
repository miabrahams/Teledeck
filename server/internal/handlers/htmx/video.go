package htmxhandlers

import (
	"fmt"
	"net/http"
	"teledeck/internal/templates"

	"teledeck/internal/models"
)

type VideoTestHandler struct{}

func (h *VideoTestHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	fmt.Println("HELLOOOO")
	m := models.MediaItemWithMetadata{
		MediaItem: models.MediaItem{
			ID:       "test",
			FileName: "",
		},

		TelegramText: "hi",
		MediaType:    "video",
		ChannelTitle: "test",
	}

	component := templates.VideoTest(&m, "hello.jpg")
	err := templates.VideoLayout(component, "Video Test").Render(r.Context(), w)
	if err != nil {
		http.Error(w, "Error rendering video layout", http.StatusInternalServerError)
	}
}
