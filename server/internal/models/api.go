package models

type SearchPrefs struct {
	Sort       string
	Favorites  string
	VideosOnly bool
	Search     string
}

type ScoreResult struct {
	Score float32 `json:"score"`
}

type MediaItemWithThumbnail struct {
	MediaItem
	Thumbnail string `json:"thumbnail"`
}
