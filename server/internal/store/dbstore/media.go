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

const VIDEOS_SELECTOR = "media_items.type = 'video' OR media_items.type = 'gif' OR media_items.type = 'webm'"

func (s *MediaStore) GetTotalMediaItems(only_videos bool) int64 {
	var count int64
	query := s.db.Model(&store.MediaItem{})
	if only_videos {
		query = query.Where(VIDEOS_SELECTOR)
	}

	query.Count(&count)
	return count

}

func (s *MediaStore) GetPaginatedMediaItems(page, itemsPerPage int, sort string, only_videos bool) ([]store.MediaItemWithChannel, error) {
	offset := (page - 1) * itemsPerPage
	var mediaItems []store.MediaItemWithChannel
	query := s.db.Table("media_items").
		Select("media_items.*, channels.title as channel_title").
		Joins("LEFT JOIN channels ON media_items.channel_id = channels.id")

	switch sort {
	case "date_asc":
		query = query.Order("media_items.date ASC")
	case "date_desc":
		query = query.Order("media_items.date DESC")
	case "id_asc":
		query = query.Order("media_items.id ASC")
	case "id_desc":
		query = query.Order("media_items.id DESC")
	default:
		query = query.Order("media_items.date DESC")
	}

	query = query.Order("media_items.id").
		Limit(itemsPerPage).
		Offset(offset)

	if only_videos {
		query = query.Where(VIDEOS_SELECTOR)
	}

	result := query.Scan(&mediaItems)
	return mediaItems, result.Error
}

func (s *MediaStore) GetAllMediaItems() ([]store.MediaItemWithChannel, error) {
	var mediaItems []store.MediaItemWithChannel
	result := s.db.Order("date DESC").Joins("LEFT JOIN channels ON media_items.channel_id = channels.id").Scan(&mediaItems)
	return mediaItems, result.Error
}