package handlers

import (
	"math"
	"net/http"
	"strconv"
	"teledeck/internal/middleware"
	"teledeck/internal/models"
	store "teledeck/internal/service/store"
	"teledeck/internal/templates"

	"log/slog"

	"github.com/a-h/templ"
)

type HomeHandler struct {
	MediaStore store.MediaStore
	logger     *slog.Logger
}

type NewHomeHandlerParams struct {
	MediaStore store.MediaStore
	Logger     *slog.Logger
}

func NewHomeHandler(params NewHomeHandlerParams) *HomeHandler {
	return &HomeHandler{MediaStore: params.MediaStore, logger: params.Logger}
}

func (h *HomeHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	user, _ := r.Context().Value(middleware.UserKey).(*models.User)
	h.logger.Info("Handling request: ", "URL", r.URL, "Query", r.URL.Query())

	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}

	itemsPerPage := 100

	sort := r.URL.Query().Get("sort")
	if sort == "" {
		err := templates.Layout(templates.IndexEmpty(), "Media Gallery").Render(r.Context(), w)
		if err != nil {
			http.Error(w, "Error rendering page", http.StatusInternalServerError)
		}
		return
	}

	videosOnly := r.URL.Query().Get("videos") == "true"
	favorites := r.URL.Query().Get("favorites")
	search := r.URL.Query().Get("search")

	searchPrefs := models.SearchPrefs{
		Sort:       sort,
		VideosOnly: videosOnly,
		Favorites:  favorites,
		Search:     search,
	}

	mediaItems, err := h.MediaStore.GetPaginatedMediaItems(page, itemsPerPage, searchPrefs)

	if err != nil {
		http.Error(w, "Error fetching media items", http.StatusInternalServerError)
		return
	}

	totalPages := int(math.Ceil(float64(h.MediaStore.GetMediaItemCount(searchPrefs)) / float64(itemsPerPage)))

	gallery := templates.Gallery(mediaItems, page, totalPages)

	var index templ.Component
	if user != nil {
		index = templates.Index(user.Email, gallery)
	} else {
		index = templates.GuestIndex(gallery)
	}

	if r.Header.Get("HX-Request") == "true" {
		err = index.Render(r.Context(), w)
	} else {
		err = templates.Layout(index, "Media Gallery").Render(r.Context(), w)
	}
	if err != nil {
		http.Error(w, "Error rendering page", http.StatusInternalServerError)
		return
	}
}
