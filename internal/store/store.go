package store

import (
	"time"
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
	ID    uint `gorm:"primaryKey"`
	title string
}

type MediaItem struct {
	ID        uint `gorm:"uniqueIndex"`
	ChannelID uint
	MessageID uint
	Date      time.Time
	Text      string
	Type      string
	/* 	Path      string */
	FileName string
	FileSize int64
	URL      string
	Seen     bool
}

type MediaItemWithChannel struct {
	MediaItem
	ChannelTitle string
}

type MediaStore interface {
	GetTotalMediaItems() int64
	GetPaginatedMediaItems(page, itemsPerPage int, sort string) ([]MediaItemWithChannel, error)
	GetAllMediaItems() ([]MediaItemWithChannel, error)
}
