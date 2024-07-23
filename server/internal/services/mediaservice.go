package services

import (
	"goth/internal/fileops"
	"goth/internal/store"
)

type MediaService struct {
	store   store.MediaStore
	fileOps fileops.LocalFileOperator
}

func NewMediaService(store store.MediaStore, fileOps fileops.LocalFileOperator) *MediaService {
	return &MediaService{
		store:   store,
		fileOps: fileOps,
	}
}

func (s *MediaService) RecycleMediaItem(mediaItem store.MediaItem) error {
	if err := s.store.MarkDeleted(&mediaItem); err != nil {
		return err
	}

	return s.fileOps.Recycle(mediaItem.FileName)
}

func (s *MediaService) GetTotalMediaItems() int64 {
	return s.store.GetTotalMediaItems()
}

func (s *MediaService) GetMediaItemCount(P store.SearchPrefs) int64 {
	return s.store.GetMediaItemCount(P)
}

func (s *MediaService) GetPaginatedMediaItems(page, itemsPerPage int, P store.SearchPrefs) ([]store.MediaItemWithChannel, error) {
	return s.store.GetPaginatedMediaItems(page, itemsPerPage, P)
}

func (s *MediaService) GetAllMediaItems() ([]store.MediaItemWithChannel, error) {
	return s.store.GetAllMediaItems()
}

func (s *MediaService) ToggleFavorite(id int64) (*store.MediaItemWithChannel, error) {
	return s.store.ToggleFavorite(id)
}

func (s *MediaService) GetMediaItem(id int64) (*store.MediaItemWithChannel, error) {
	return s.store.GetMediaItem(id)
}
