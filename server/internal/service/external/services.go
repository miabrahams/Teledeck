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
