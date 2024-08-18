package controllers

import (
	"teledeck/internal/models"
	"teledeck/internal/service/external"
	"teledeck/internal/service/store"
)

type AestheticsController struct {
	aestheticsStore   store.AestheticsStore
	mediaController   MediaController
	aestheticsService external.AestheticsService
}

func NewAestheticsController(aethsticsStore store.AestheticsStore, mediaController *MediaController, aestheticsService external.AestheticsService) *AestheticsController {
	return &AestheticsController{
		aestheticsStore:   aethsticsStore,
		mediaController:   *mediaController,
		aestheticsService: aestheticsService,
	}
}

func (c *AestheticsController) ScoreImageByID(itemid string) (float32, error) {
	mediaItem, err := c.mediaController.GetMediaItem(itemid)

	if err != nil {
		return 0, err
	}
	return c.ScoreImageItem(&mediaItem.MediaItem)
}

func (c *AestheticsController) ScoreImageItem(item *models.MediaItem) (float32, error) {

	absPath := c.mediaController.GetAbsolutePath(item)

	score, err := c.aestheticsService.ScoreImage(absPath)

	if err != nil {
		return 0, err
	}

	if err = c.aestheticsStore.SetImageScore(item.ID, score); err != nil {
		return 0, err
	}

	return score, nil
}

func (c *AestheticsController) GetImageScore(itemid string) (float32, error) {
	return c.aestheticsStore.GetImageScore(itemid)
}
