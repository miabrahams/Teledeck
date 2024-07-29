package dbstore

import (
	"goth/internal/models"
	"log/slog"

	"gorm.io/gorm"
)

type AestheticsStore struct {
	db     *gorm.DB
	logger *slog.Logger
}

func NewAestheticsStore(db *gorm.DB, logger *slog.Logger) *AestheticsStore {
	return &AestheticsStore{
		db:     db,
		logger: logger,
	}
}

func (s *AestheticsStore) GetImageScore(itemid string) (float32, error) {
	var score models.ImageScore
	query := s.db.Model(&models.ImageScore{}).Where("media_item_id = ?", itemid).Find(&score)

	if query.Error != nil {
		return 0, query.Error
	}
	return score.Score, nil
}

func (s *AestheticsStore) SetImageScore(itemid string, score float32) error {

	Score := models.ImageScore{
		Score:       score,
		MediaItemID: itemid,
	}
	// Create or update
	query := s.db.Model(&models.ImageScore{}).Where("media_item_id = ?", itemid).Assign(Score).FirstOrCreate(&Score)
	return query.Error
}
