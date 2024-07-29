package controllers

import (
	"goth/internal/models"
	"goth/internal/service/external"
	"goth/internal/service/store"
)

type TagsController struct {
	tagsStore   store.TagsStore
	mediaStore  store.MediaStore
	tagsService external.TaggingService
	allTags     []models.Tag
}

func NewTagsController(tagsStore store.TagsStore, mediaStore store.MediaStore, tagsService external.TaggingService) *TagsController {
	return &TagsController{
		tagsStore:   tagsStore,
		mediaStore:  mediaStore,
		tagsService: tagsService,
		allTags:     nil,
	}
}

func (c *TagsController) GetAllTags() ([]models.Tag, error) {
	if c.allTags != nil {
		return c.allTags, nil
	}
	allTags, error := c.tagsStore.GetAllTags()
	c.allTags = allTags
	return c.allTags, error
}

func (c *TagsController) TagImageByID(itemid string, cutoff float32) ([]models.TagWeight, error) {
	mediaItem, err := c.mediaStore.GetMediaItem(itemid)

	if err != nil {
		return nil, err
	}
	c.allTags = nil
	return c.TagImageItem(&mediaItem.MediaItem, cutoff)
}

func (c *TagsController) TagImageItem(item *models.MediaItem, cutoff float32) ([]models.TagWeight, error) {
	c.allTags = nil

	// TODO: Configure file paths
	tags, err := c.tagsService.TagImage("static/media/"+item.FileName, cutoff)

	if err != nil {
		return nil, err
	}

	if err = c.tagsStore.SetItemTags(tags, item.ID); err != nil {
		return nil, err
	}

	return tags, err
}

func (c *TagsController) GetTags(itemid string) ([]models.TagWeight, error) {
	return c.tagsStore.GetItemTags(itemid)
}
