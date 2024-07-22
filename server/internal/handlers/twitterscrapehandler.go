package handlers

import (
	"encoding/json"
	"goth/internal/services"
	"net/http"
)

type TwitterScrapeHandler struct {
	scraper *services.TwitterScraper
}

func NewTwitterScrapeHandler(scraper *services.TwitterScraper) *TwitterScrapeHandler {
	return &TwitterScrapeHandler{scraper: scraper}
}

func (h *TwitterScrapeHandler) ScrapeUser(w http.ResponseWriter, r *http.Request) {
	data := h.scraper.ScrapeUser("x")

	w.Header().Set("Content-Type", "application/json")

	json.NewEncoder(w).Encode(data)
}
