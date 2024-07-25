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
}

func NewTagsController(tagsStore store.TagsStore, mediaStore store.MediaStore, tagsService external.TaggingService) *TagsController {
	return &TagsController{
		tagsStore:   tagsStore,
		mediaStore:  mediaStore,
		tagsService: tagsService,
	}
}
func (c *TagsController) TagImageByID(itemid string, cutoff float32) ([]models.TagWeight, error) {
	mediaItem, err := c.mediaStore.GetMediaItem(itemid)

	if err != nil {
		return nil, err
	}
	return c.TagImageItem(&mediaItem.MediaItem, cutoff)
}

func (c *TagsController) TagImageItem(item *models.MediaItem, cutoff float32) ([]models.TagWeight, error) {

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
