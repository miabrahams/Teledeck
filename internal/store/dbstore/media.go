package dbstore

import (
	"goth/internal/store"

	"gorm.io/gorm"
)

type MediaStore struct {
	db    *gorm.DB
	total int64
}

type NewMediaStoreParams struct {
	DB *gorm.DB
}

func NewMediaStore(params NewMediaStoreParams) *MediaStore {
	var count int64
	params.DB.Model(&store.MediaItem{}).Count(&count)
	return &MediaStore{
		db:    params.DB,
		total: count,
	}
}

func (s *MediaStore) GetTotalMediaItems() int64 {
	var count int64
	s.db.Model(&store.MediaItem{}).Count(&count)
	return count
}

func (s *MediaStore) GetPaginatedMediaItems(page, itemsPerPage int) ([]store.MediaItem, error) {
	offset := (page - 1) * itemsPerPage
	var mediaItems []store.MediaItem
	// result := s.db.Order("date DESC").Limit(itemsPerPage).Offset(offset).Find(&mediaItems)
	// result := s.db.Order("id DESC").Limit(itemsPerPage).Offset(offset).Find(&mediaItems)
	result := s.db.Order("id").Limit(itemsPerPage).Offset(offset).Find(&mediaItems)
	return mediaItems, result.Error
}

func (s *MediaStore) GetAllMediaItems() ([]store.MediaItem, error) {
	var mediaItems []store.MediaItem
	result := s.db.Order("date DESC").Find(&mediaItems)
	return mediaItems, result.Error
}
