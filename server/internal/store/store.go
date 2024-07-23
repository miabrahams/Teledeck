package store

import (
	. "time"
)

type User struct {
	ID       uint   `gorm:"primaryKey" json:"id"`
	Email    string `json:"email"`
	Password string `json:"-"`
}

type Session struct {
	ID        uint   `gorm:"primaryKey" json:"id"`
	SessionID string `json:"session_id"`
	UserID    uint   `json:"user_id"`
	User      User   `gorm:"foreignKey:UserID" json:"user"`
}

type UserStore interface {
	CreateUser(email string, password string) error
	GetUser(email string) (*User, error)
}

type SessionStore interface {
	CreateSession(session *Session) (*Session, error)
	GetUserFromSession(sessionID string, userID string) (*User, error)
}

type Channel struct {
	ID    int64 `gorm:"primaryKey"`
	Title string
}

type MediaItem struct {
	ID          int64   `gorm:"primaryKey"`   // id
	FileID      int     `json:"file_id"`      // file_id
	ChannelID   int     `json:"channel_id"`   // channel_id
	MessageID   int     `json:"message_id"`   // message_id
	Date        Time    `json:"date"`         // date
	Text        string  `json:"text"`         // text
	Type        string  `json:"type"`         // type
	FileName    string  `json:"file_name"`    // file_name
	FileSize    int     `json:"file_size"`    // file_size
	URL         string  `json:"url"`          // url
	Seen        float64 `json:"seen"`         // seen
	Favorite    bool    `json:"favorite"`     // favorite
	UserDeleted bool    `json:"user_deleted"` // user_deleted
	// xo fields
	_exists, _deleted bool
}

type MediaItemWithChannel struct {
	MediaItem
	ChannelTitle string
}

type SearchPrefs struct {
	Sort       string
	Favorites  string
	VideosOnly bool
	Search     string
}

type MediaStore interface {
	GetTotalMediaItems(videos bool) int64
	GetPaginatedMediaItems(page, itemsPerPage int, P SearchPrefs) ([]MediaItemWithChannel, error)
	GetAllMediaItems() ([]MediaItemWithChannel, error)
	ToggleFavorite(id int64) (*MediaItemWithChannel, error)
	GetMediaItem(id int64) (*MediaItemWithChannel, error)
	MarkDeleted(item *MediaItem) error
}
