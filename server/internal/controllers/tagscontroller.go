package controllers

import (
	"goth/internal/models"
	"goth/internal/service/external"
	"goth/internal/service/store"
)

type TagsController struct {
	store       store.TagsStore
	tagsService external.TaggingService
}

func NewTagsController(store store.TagsStore, service external.TaggingService) *TagsController {
	return &TagsController{
		store:       store,
		tagsService: service,
	}
}

func (c *TagsController) GetTags(itemid string) []models.MediaItemTag {
	return c.store.GetTags(itemid)
}
