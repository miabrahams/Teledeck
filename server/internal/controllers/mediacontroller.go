package controllers

import (
	"goth/internal/models"
	"goth/internal/service/files"
	"goth/internal/service/store"
)

type MediaController struct {
	store   store.MediaStore
	fileOps files.LocalFileOperator
}

func NewMediaController(store store.MediaStore, fileOps files.LocalFileOperator) *MediaController {
	return &MediaController{
		store:   store,
		fileOps: fileOps,
	}
}

func (s *MediaController) RecycleMediaItem(mediaItem models.MediaItem) error {
	if err := s.store.MarkDeleted(&mediaItem); err != nil {
		return err
	}

	return s.fileOps.Recycle(mediaItem.FileName)
}

func (s *MediaController) GetTotalMediaItems() int64 {
	return s.store.GetTotalMediaItems()
}

func (s *MediaController) GetMediaItemCount(P models.SearchPrefs) int64 {
	return s.store.GetMediaItemCount(P)
}

func (s *MediaController) GetPaginatedMediaItems(page, itemsPerPage int, P models.SearchPrefs) ([]models.MediaItemWithMetadata, error) {
	return s.store.GetPaginatedMediaItems(page, itemsPerPage, P)
}

func (s *MediaController) GetAllMediaItems() ([]models.MediaItemWithMetadata, error) {
	return s.store.GetAllMediaItems()
}

func (s *MediaController) ToggleFavorite(id string) (*models.MediaItemWithMetadata, error) {
	return s.store.ToggleFavorite(id)
}

func (s *MediaController) GetMediaItem(id string) (*models.MediaItemWithMetadata, error) {
	return s.store.GetMediaItem(id)
}
