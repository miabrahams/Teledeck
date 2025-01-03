package controllers

import (
	"teledeck/internal/models"
	"teledeck/internal/service/files"
	"teledeck/internal/service/store"
)

type MediaController struct {
	store    store.MediaStore
	fileOps  files.LocalFileOperator
	fileRoot string
}

func NewMediaController(store store.MediaStore, fileOps files.LocalFileOperator, fileRoot string) *MediaController {
	return &MediaController{
		store:    store,
		fileOps:  fileOps,
		fileRoot: fileRoot,
	}
}

func (s *MediaController) RecycleMediaItem(mediaItem models.MediaItem) error {
	if err := s.store.MarkDeleted(&mediaItem); err != nil {
		return err
	}

	return s.fileOps.Recycle(mediaItem.FileName)
}

func (s *MediaController) RecycleAndGetNext(mediaItem *models.MediaItem, page int, P models.SearchPrefs) (*models.MediaItemWithMetadata, error) {
	// TODO: 100 items per page is hardcoded here
	nextMediaItem, err := s.store.MarkDeletedAndGetNext(mediaItem, page, 100, P)

	if err != nil {
		return nil, err
	}

	err = s.fileOps.Recycle(mediaItem.FileName)
	if err != nil {
		// TODO: Bad if an error happens here!!
		// Undelete??
	}

	return nextMediaItem, nil
}

func (s *MediaController) GetAbsolutePath(mediaItem *models.MediaItem) string {
	return s.fileRoot + "/" + mediaItem.FileName
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
