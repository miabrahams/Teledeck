package dbstore

import (
	"fmt"
	"teledeck/internal/models"

	"log/slog"
	"strconv"

	"gorm.io/gorm"
)

type MediaStore struct {
	db     *gorm.DB
	logger *slog.Logger
	total  int64
}

func NewMediaStore(DB *gorm.DB, logger *slog.Logger) *MediaStore {
	var count int64
	DB.Model(&models.MediaItem{}).Count(&count)
	return &MediaStore{
		db:     DB,
		logger: logger,
		total:  count,
	}
}

type ErrFavorite struct{}

func (e ErrFavorite) Error() string {
	return "Cannot delete a favorite item"
}

func (s *MediaStore) GetTotalMediaItems() int64 {
	var count int64
	query := s.db.Model(&models.MediaItem{})
	query = query.Where("media_items.user_deleted = false")
	query.Count(&count)
	return count
}

func (s *MediaStore) applySearchFilters(P models.SearchPrefs, query *gorm.DB) *gorm.DB {

	query = query.Where("media_items.user_deleted = false")

	if P.VideosOnly {
		query = query.Where("media_types.type = 'video' OR media_types.type = 'gif' OR media_types.type = 'webm'")
	}

	switch P.Favorites {
	case "favorites":
		query = query.Where("media_items.favorite = true")
	case "non-favorites":
		query = query.Where("media_items.favorite = false")
	default:
	}

	if P.Search != "" {
		// query = query.Where("media_items.text LIKE ?", "%"+P.Search+"%")

		matching_tags := s.db.Select("id").Model(&models.Tag{}).Where("name LIKE ?", P.Search+"%")
		matching_ids := s.db.Select("media_item_id").Model(&models.MediaItemTag{}).Where("tag_id IN (?)", matching_tags).Distinct()
		query = query.Where("media_items.id IN (?)", matching_ids)
	}

	return query
}

func (s *MediaStore) GetMediaItemCount(P models.SearchPrefs) int64 {
	var count int64
	query := s.db.Model(&models.MediaItem{})
	query = s.applySearchFilters(P, query)
	query.Count(&count)
	fmt.Printf("Count: %d\n", count)
	return count
}

func (s *MediaStore) GetMediaWithMetadataQuery() *gorm.DB {
	query := s.db.Model(&models.MediaItem{}).
		Select("media_items.*, telegram_metadata.*, sources.name as source_name, media_types.type as media_type, channels.title as channel_title").
		Joins("LEFT JOIN media_types ON media_items.media_type_id = media_types.id").
		Joins("LEFT JOIN sources ON media_items.source_id = sources.id").
		Joins("LEFT JOIN telegram_metadata ON media_items.id = telegram_metadata.media_item_id").
		Joins("LEFT JOIN channels ON telegram_metadata.channel_id = channels.id").
		Where("user_deleted = false")
	return query
}

func (s *MediaStore) GetMediaItem(id string) (*models.MediaItemWithMetadata, error) {
	// TODO: Handle multiple data sources
	result := models.MediaItemWithMetadata{}
	query := s.GetMediaWithMetadataQuery().Where(&models.MediaItem{ID: id})
	err := query.Scan(&result).Error
	return &result, err
}

func (s *MediaStore) ToggleFavorite(id string) (*models.MediaItemWithMetadata, error) {
	item, err := s.GetMediaItem(id)
	if err != nil {
		return nil, err
	}

	item.Favorite = !item.Favorite

	s.logger.Info("New fav status: ", "New status:", strconv.FormatBool(item.Favorite), "File", item.FileName)
	err = s.db.Save(&item.MediaItem).Error
	if err != nil {
		return nil, err
	}

	return item, nil
}

func (s *MediaStore) GetPaginatedMediaItems(page, itemsPerPage int, P models.SearchPrefs) ([]models.MediaItemWithMetadata, error) {
	offset := (page - 1) * itemsPerPage
	var mediaItems []models.MediaItemWithMetadata
	query := s.GetMediaWithMetadataQuery()

	switch P.Sort {
	case "date_asc":
		query = query.Order("media_items.created_at ASC")
	case "date_desc":
		query = query.Order("media_items.created_at DESC")
	case "id_asc":
		query = query.Order("telegram_metadata.message_id ASC")
	case "id_desc":
		query = query.Order("telegram_metadata.message_id DESC")
	case "size_asc":
		query = query.Order("media_items.file_size ASC")
	case "size_desc":
		query = query.Order("media_items.file_size DESC")
	case "random":
		query = query.Order("RANDOM()")
	default:
		query = query.Order("media_items.date DESC")
	}

	query = query.Order("media_items.id").Offset(offset)

	query = s.applySearchFilters(P, query)

	query = query.Limit(itemsPerPage)

	err := query.Scan(&mediaItems).Error
	s.logger.Info("Media items", "Items", mediaItems[0])
	return mediaItems, err
}

func (s *MediaStore) GetAllMediaItems() ([]models.MediaItemWithMetadata, error) {
	var mediaItems []models.MediaItemWithMetadata
	query := s.GetMediaWithMetadataQuery()
	err := query.Scan(&mediaItems).Error
	return mediaItems, err
}

func (s *MediaStore) MarkDeleted(item *models.MediaItem) error {
	if item.Favorite {
		return ErrFavorite{}
	}
	result := s.db.Model(item).Update("user_deleted", true)
	return result.Error
}
