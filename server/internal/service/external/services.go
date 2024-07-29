package external

import (
	"goth/internal/models"
	"image"
)

type TelegramService interface {
	GetVersion()
	GetMe()
	listenForUpdates()
}

type TaggingService interface {
	TagImage(imagePath string, cutoff float32) ([]models.TagWeight, error)
	TagImageData(image image.Image, cutoff float32) ([]models.TagWeight, error)
}

type AestheticsService interface {
	ScoreImage(imagePath string) (float32, error)
	ScoreImageData(image image.Image) (float32, error)
}
