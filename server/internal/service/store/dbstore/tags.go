package dbstore

import (
	"goth/internal/models"
	"log/slog"

	"gorm.io/gorm"
)

type TagsStore struct {
	db     *gorm.DB
	logger *slog.Logger
}

func NewTagsStore(db *gorm.DB, logger *slog.Logger) *TagsStore {
	return &TagsStore{
		db:     db,
		logger: logger,
	}
}

func (s *TagsStore) GetTagID(name string) (models.Tag, error) {
	tag := models.Tag{}
	result := s.db.Model(&models.Tag{}).Where(models.Tag{Name: name}).Find(&tag)
	return tag, result.Error
}

func (s *TagsStore) GetTagIDs(names []string) ([]models.Tag, error) {
	tags := []models.Tag{}
	result := s.db.Model(&models.Tag{}).Where("name IN ?", names).Find(&tags)
	return tags, result.Error
}

func (s *TagsStore) GetItemTags(itemid string) ([]models.TagWeight, error) {
	var tags []models.TagWeight
	query := s.db.Model(&models.MediaItemTag{}).
		Select("tags.name as tag, media_item_tags.weight").
		Joins("LEFT JOIN tags ON media_item_tags.tag_id = tags.id").
		Where("media_item_id = ?", itemid).
		Scan(tags)

	if query.Error != nil {
		return nil, query.Error
	}
	return tags, nil
}

func (s *TagsStore) SetItemTags(tags []models.TagWeight, itemid string) error {

	for _, tag := range tags {
		DBTag, err := s.GetTagID(tag.Name)
		if err != nil {
			return err
		}
		MediaTag := models.MediaItemTag{
			MediaItemID: itemid,
			TagID:       DBTag.ID,
			Weight:      tag.Weight,
		}
		result := s.db.Create(&MediaTag)
		if result.Error != nil {
			return result.Error
		}
	}
	return nil
}
