package dbstore

import (
	"goth/internal/store"

	"gorm.io/gorm"
)

type MediaStore struct {
	db *gorm.DB
}

type NewMediaStoreParams struct {
	DB *gorm.DB
}

func NewMediaStore(params NewMediaStoreParams) *MediaStore {
	return &MediaStore{
		db: params.DB,
	}
}


func (s *MediaStore) GetAllMediaItems() ([]store.MediaItem, error) {
	var mediaItems []store.MediaItem
	result := s.db.Find(&mediaItems)
    return mediaItems, result.Error
}
