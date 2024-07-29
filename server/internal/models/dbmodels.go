package models

import (
	"time"
)

type User struct {
	ID       uint   `gorm:"column:id;primaryKey" json:"id"`
	Email    string `gorm:"column:email;not null" json:"email"`
	Password string `gorm:"column:password;not null" json:"password"`
}

type Session struct {
	ID        uint   `gorm:"column:id;primaryKey" json:"id"`
	SessionID string `gorm:"column:session_id;not null" json:"session_id"`
	UserID    uint   `gorm:"column:user_id;primaryKey" json:"user_id"`
	User      User   `gorm:"foreignKey:UserID" json:"user"`
}

type Source struct {
	ID   int    `gorm:"column:id;type:INTEGER" json:"id"`
	Name string `gorm:"column:name;type:VARCHAR" json:"name"`
}

type MediaType struct {
	ID   int    `gorm:"column:id;type:INTEGER" json:"id"`
	Type string `gorm:"column:type;type:VARCHAR" json:"type"`
}

// https://stackoverflow.com/questions/36486511/how-do-you-do-uuid-in-golangs-gorm
type MediaItem struct {
	ID          string    `gorm:"column:id;type:VARCHAR(36)" json:"id"`
	SourceID    int       `gorm:"column:source_id;type:INTEGER" json:"source_id"`
	MediaTypeID int       `gorm:"column:media_type_id;type:INTEGER" json:"media_type_id"`
	FileName    string    `gorm:"column:file_name;type:VARCHAR" json:"file_name"`
	FileSize    int       `gorm:"column:file_size;type:INTEGER" json:"file_size"`
	CreatedAt   time.Time `gorm:"column:created_at;type:DATETIME" json:"created_at"`
	UpdatedAt   time.Time `gorm:"column:updated_at;type:DATETIME" json:"updated_at"`
	Seen        bool      `gorm:"column:seen;type:BOOLEAN" json:"seen"`
	Favorite    bool      `gorm:"column:favorite;type:BOOLEAN" json:"favorite"`
	UserDeleted bool      `gorm:"column:user_deleted;type:BOOLEAN" json:"user_deleted"`
}

type Channel struct {
	ID    int    `gorm:"column:id;primaryKey"`
	Title string `gorm:"column:title;not null"`
	Check bool   `gorm:"column:check;not null"`
}

type MediaItemDuplicate struct {
	First_ string `gorm:"column:first;type:VARCHAR(36)" json:"first"`
	Second string `gorm:"column:second;type:VARCHAR(36)" json:"second"`
}

type MediaItemTag struct {
	MediaItemID string  `gorm:"column:media_item_id;type:VARCHAR(36)" json:"media_item_id"`
	TagID       int     `gorm:"column:tag_id;type:INTEGER" json:"tag_id"`
	Weight      float32 `gorm:"column:weight;type:FLOAT" json:"weight"`
}

type TelegramMetadatum struct {
	MediaItemID string    `gorm:"column:media_item_id;type:VARCHAR(36)" json:"media_item_id"`
	ChannelID   int       `gorm:"column:channel_id;type:INTEGER" json:"channel_id"`
	MessageID   int       `gorm:"column:message_id;type:INTEGER" json:"message_id"`
	FileID      int       `gorm:"column:file_id;type:INTEGER" json:"file_id"`
	FromPreview int       `gorm:"column:from_preview;type:INTEGER" json:"from_preview"`
	Date        time.Time `gorm:"column:date;type:DATETIME" json:"date"`
	Text        string    `gorm:"column:text;type:TEXT" json:"text"`
	URL         string    `gorm:"column:url;type:VARCHAR" json:"url"`
}

// TableName TelegramMetadatum's table name
func (*TelegramMetadatum) TableName() string {
	return "telegram_metadata"
}

type Tag struct {
	ID   int    `gorm:"column:id;type:INTEGER" json:"id"`
	Name string `gorm:"column:name;type:VARCHAR" json:"name"`
}

type TwitterMetadatum struct {
	MediaItemID string    `gorm:"column:media_item_id;type:VARCHAR(36)" json:"media_item_id"`
	TweetID     string    `gorm:"column:tweet_id;type:VARCHAR(36)" json:"tweet_id"`
	Username    string    `gorm:"column:username;type:VARCHAR" json:"username"`
	Date        time.Time `gorm:"column:date;type:DATETIME" json:"date"`
	Text        string    `gorm:"column:text;type:TEXT" json:"text"`
	URL         string    `gorm:"column:url;type:VARCHAR" json:"url"`
}

// TableName TwitterMetadatum's table name
func (*TwitterMetadatum) TableName() string {
	return "twitter_metadata"
}

type ImageScore struct {
	MediaItemID string  `gorm:"column:media_item_id;type:VARCHAR(36)"`
	Score       float32 `gorm:"column:score"`
}

func (*ImageScore) TableName() string {
	return "aesthetic_score"
}
