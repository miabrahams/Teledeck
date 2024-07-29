package models

import "time"

type SearchPrefs struct {
	Sort       string
	Favorites  string
	VideosOnly bool
	Search     string
}

// TODO: Figure out better handling; look into struct embedding
type MediaItemWithMetadata struct {
	MediaItem
	ChannelID      int       `gorm:"column:channel_id"`
	MessageID      int       `gorm:"column:message_id"`
	TelegramFileID int       `gorm:"column:file_id"`
	FromPreview    int       `gorm:"column:from_preview"`
	TelegramDate   time.Time `gorm:"column:date"`
	TelegramText   string    `gorm:"column:text"`
	TelegramURL    string    `gorm:"column:url"`
	MediaType      string    `gorm:"column:media_type"`
	ChannelTitle   string    `gorm:"column:channel_title"`
}

type TagWeight struct {
	Name   string  `gorm:"column:name" json:"tag"`
	Weight float32 `gorm:"column:weight" json:"prob"`
}

type ScoreResult struct {
	Score float32 `json:"score"`
}
