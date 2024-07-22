package services

import (
	"fmt"
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
	fmt.Println("Deleting media item: %S", mediaItem.FileName)
	if err := s.store.MarkDeleted(&mediaItem); err != nil {
		fmt.Printf("Error: %v\n", err)
		return err
	}

	return s.fileOps.Recycle(mediaItem.FileName)
}

func (s *MediaService) GetTotalMediaItems(videos bool) int64 {
	return s.store.GetTotalMediaItems(videos)
}

func (s *MediaService) GetPaginatedMediaItems(page, itemsPerPage int, P store.SearchPrefs) ([]store.MediaItemWithChannel, error) {
	return s.store.GetPaginatedMediaItems(page, itemsPerPage, P)
}

func (s *MediaService) GetAllMediaItems() ([]store.MediaItemWithChannel, error) {
	return s.store.GetAllMediaItems()
}

func (s *MediaService) ToggleFavorite(id uint64) (*store.MediaItemWithChannel, error) {
	return s.store.ToggleFavorite(id)
}

func (s *MediaService) GetMediaItem(id uint64) (*store.MediaItemWithChannel, error) {
	return s.store.GetMediaItem(id)
}
