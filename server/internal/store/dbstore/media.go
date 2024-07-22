package dbstore

import (
	"goth/internal/store"

	"log/slog"
	"strconv"

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

type ErrFavorite struct{}

func (e ErrFavorite) Error() string {
	return "Cannot delete a favorite item"
}

const VIDEOS_SELECTOR = "media_items.type = 'video' OR media_items.type = 'gif' OR media_items.type = 'webm'"

func (s *MediaStore) GetTotalMediaItems(only_videos bool) int64 {
	var count int64
	query := s.db.Model(&store.MediaItem{})
	if only_videos {
		query = query.Where(VIDEOS_SELECTOR)
	}
	query = query.Where("media_items.user_deleted = false")
	query.Count(&count)
	return count
}

func (s *MediaStore) GetMediaItem(id uint64) (*store.MediaItemWithChannel, error) {
	query := s.db.Model(&store.MediaItem{}).
		Joins("LEFT JOIN channels ON media_items.channel_id = channels.id")
	query = query.Where("media_items.id = ?", id)
	item := store.MediaItemWithChannel{}
	result := query.Scan(&item)
	return &item, result.Error
}

func (s *MediaStore) ToggleFavorite(id uint64) (*store.MediaItemWithChannel, error) {
	logger := slog.Default()
	var itemWithChannel store.MediaItemWithChannel
	result := s.db.Model(&store.MediaItem{}).Where("media_items.id = ?", id).Joins("LEFT JOIN channels ON media_items.channel_id = channels.id").Scan(&itemWithChannel)
	if result.Error != nil {
		return nil, result.Error
	}

	itemWithChannel.Favorite = !itemWithChannel.Favorite

	var item store.MediaItem = itemWithChannel.MediaItem
	logger.Info("New fav status: ", "New status:", strconv.FormatBool(item.Favorite), "File", item.FileName)
	err := s.db.Save(&item).Error
	if err != nil {
		return nil, err
	}

	return &itemWithChannel, nil
}

func (s *MediaStore) GetPaginatedMediaItems(page, itemsPerPage int, P store.SearchPrefs) ([]store.MediaItemWithChannel, error) {
	offset := (page - 1) * itemsPerPage
	var mediaItems []store.MediaItemWithChannel
	query := s.db.Table("media_items").
		Select("media_items.*, channels.title as channel_title").
		Joins("LEFT JOIN channels ON media_items.channel_id = channels.id")

	switch P.Sort {
	case "date_asc":
		query = query.Order("media_items.date ASC")
	case "date_desc":
		query = query.Order("media_items.date DESC")
	case "id_asc":
		query = query.Order("media_items.id ASC")
	case "id_desc":
		query = query.Order("media_items.id DESC")
	case "random":
		query = query.Order("RANDOM()")
	default:
		query = query.Order("media_items.date DESC")
	}

	query = query.Order("media_items.id").Offset(offset)

	if P.VideosOnly {
		query = query.Where(VIDEOS_SELECTOR)
	}
	if P.FavoritesOnly {
		query = query.Where("media_items.favorite = true")
	}

	if P.Search != "" {
		query = query.Where("media_items.text LIKE ?", "%"+P.Search+"%")
	}

	query = query.Where("media_items.user_deleted = false")

	query = query.Limit(itemsPerPage)

	result := query.Scan(&mediaItems)
	return mediaItems, result.Error
}

func (s *MediaStore) GetAllMediaItems() ([]store.MediaItemWithChannel, error) {
	var mediaItems []store.MediaItemWithChannel
	result := s.db.Order("date DESC").Joins("LEFT JOIN channels ON media_items.channel_id = channels.id").Where("user_deleted = false").Scan(&mediaItems)
	return mediaItems, result.Error
}

func (s *MediaStore) MarkDeleted(item *store.MediaItem) error {
	if item.Favorite {
		return ErrFavorite{}
	}
	result := s.db.Model(item).Update("user_deleted", true)
	return result.Error
}
