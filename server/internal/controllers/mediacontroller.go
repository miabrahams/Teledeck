package controllers

import (
	"errors"
	"fmt"
	"log/slog"
	"slices"
	"teledeck/internal/models"
	"teledeck/internal/service/files"
	"teledeck/internal/service/store"
	"teledeck/internal/service/thumbnailer"
)

var (
	ErrThumbnailInProgress = errors.New("thumbnail generation in progress")
	vidTypes               = []string{"video", "webp", "gif"}
)

// MediaController is the interface used by handlers/other controllers.
type MediaController interface {
	RecycleMediaItem(mediaItem models.MediaItem) error
	UndoLastDeleted() (*models.MediaItemWithMetadata, error)
	RecycleAndGetNext(mediaItem *models.MediaItem, page int, P models.SearchPrefs) (*models.MediaItemWithMetadata, error)
	GetAbsolutePath(mediaItem *models.MediaItem) string
	GetTotalMediaItems() int64
	GetMediaItemCount(P models.SearchPrefs) int64
	GetPaginatedMediaItems(page, itemsPerPage int, P models.SearchPrefs) ([]models.MediaItemWithMetadata, error)
	GetPaginatedMediaItemIds(page, itemsPerPage int, P models.SearchPrefs) ([]models.MediaItemID, error)
	GetAllMediaItems() ([]models.MediaItemWithMetadata, error)
	ToggleFavorite(id string) (*models.MediaItemWithMetadata, error)
	GetMediaItem(id string) (*models.MediaItemWithMetadata, error)
	DeletePageItems(itemIDs []string, page int, searchPrefs models.SearchPrefs) (*DeletePageResult, error)
	GetThumbnail(mediaItemID string) (string, error)
}

// LocalMediaController is the concrete implementation formerly named MediaController.
type LocalMediaController struct {
	store       store.MediaStore
	thumbnailer thumbnailer.Thumbnailer
	fileOps     files.LocalFileOperator
	fileRoot    string
}

func NewMediaController(store store.MediaStore, fileOps files.LocalFileOperator,
	fileRoot string, tn thumbnailer.Thumbnailer,
) MediaController {
	c := &LocalMediaController{
		store:       store,
		fileOps:     fileOps,
		fileRoot:    fileRoot,
		thumbnailer: tn,
	}
	tn.SetHandler(c.onThumbnailGen)
	return c
}

func (s *LocalMediaController) RecycleMediaItem(mediaItem models.MediaItem) error {
	if err := s.store.MarkDeleted(&mediaItem); err != nil {
		return err
	}

	return s.fileOps.Recycle(mediaItem.FileName)
}

func (s *LocalMediaController) UndoLastDeleted() (*models.MediaItemWithMetadata, error) {
	restoredItem, err := s.store.UndoLastDeleted()
	if err != nil {
		return nil, err
	}

	err = s.fileOps.Restore(restoredItem.FileName)
	if err != nil {
		return nil, err
	}

	return restoredItem, nil
}

func (s *LocalMediaController) RecycleAndGetNext(mediaItem *models.MediaItem, page int, P models.SearchPrefs) (*models.MediaItemWithMetadata, error) {
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

func (s *LocalMediaController) GetAbsolutePath(mediaItem *models.MediaItem) string {
	return s.fileRoot + "/" + mediaItem.FileName
}

func (s *LocalMediaController) GetTotalMediaItems() int64 {
	return s.store.GetTotalMediaItems()
}

func (s *LocalMediaController) GetMediaItemCount(P models.SearchPrefs) int64 {
	return s.store.GetMediaItemCount(P)
}

func (s *LocalMediaController) GetPaginatedMediaItems(page, itemsPerPage int, P models.SearchPrefs) ([]models.MediaItemWithMetadata, error) {
	return s.store.GetPaginatedMediaItems(page, itemsPerPage, P)
}

func (s *LocalMediaController) GetPaginatedMediaItemIds(page, itemsPerPage int, P models.SearchPrefs) ([]models.MediaItemID, error) {
	return s.store.GetPaginatedMediaItemIds(page, itemsPerPage, P)
}

func (s *LocalMediaController) GetAllMediaItems() ([]models.MediaItemWithMetadata, error) {
	return s.store.GetAllMediaItems()
}

func (s *LocalMediaController) ToggleFavorite(id string) (*models.MediaItemWithMetadata, error) {
	return s.store.ToggleFavorite(id)
}

func (s *LocalMediaController) GetMediaItem(id string) (*models.MediaItemWithMetadata, error) {
	return s.store.GetMediaItem(id)
}

type DeletePageResult struct {
	DeletedCount int                            `json:"deletedCount"`
	SkippedCount int                            `json:"skippedCount"`
	Errors       []string                       `json:"errors,omitempty"`
	NextPage     []models.MediaItemWithMetadata `json:"nextPage,omitempty"`
}

func (s *LocalMediaController) DeletePageItems(itemIDs []string, page int, searchPrefs models.SearchPrefs) (*DeletePageResult, error) {
	const itemsPerPage = 100 // Match the constant from the handler

	result := &DeletePageResult{
		Errors: make([]string, 0),
	}

	// Delete each item
	for _, itemID := range itemIDs {
		mediaItem, err := s.store.GetMediaItem(itemID)
		if err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("Failed to get item %s: %v", itemID, err))
			continue
		}

		if mediaItem.Favorite {
			result.SkippedCount++
			result.Errors = append(result.Errors, fmt.Sprintf("Skipped favorite item %s", itemID))
			continue
		}

		err = s.RecycleMediaItem(mediaItem.MediaItem)
		if err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("Failed to delete item %s: %v", itemID, err))
			continue
		}

		result.DeletedCount++
	}

	// Get the next page of items to fill the gap
	remainingItems, err := s.store.GetPaginatedMediaItems(page, itemsPerPage, searchPrefs)
	if err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("Failed to get replacement items: %v", err))
	} else {
		result.NextPage = remainingItems
	}

	return result, nil
}

// Note: May not have a way to handle failed thumbnail generations
func (s *LocalMediaController) GetThumbnail(mediaItemID string) (string, error) {
	mediaItem, err := s.store.GetMediaItem(mediaItemID)
	if err != nil {
		slog.Info("cannot find video item")
		return "", err
	}

	if !slices.Contains(vidTypes, mediaItem.MediaType) {
		slog.Info("non-video thumbnail")
		return "", fmt.Errorf("media item is not a video or gif")
	}

	fileName, err := s.store.GetThumbnail(mediaItemID)
	if fileName != "" {
		return fileName, err
	}

	// Start thumbnail generation
	err = s.thumbnailer.GenerateVideoThumbnail(s.GetAbsolutePath(&mediaItem.MediaItem), "", mediaItemID)
	if err != nil {
		return "", err
	}

	return "", ErrThumbnailInProgress
}

// Save results
func (s *LocalMediaController) onThumbnailGen(result thumbnailer.Result) {
	if result.Err != nil {
		slog.Error("Error generating thumbnail", "err", result.Err)
		return
	}

	mediaItemID, ok := result.CorrelationID.(string)
	if !ok {
		slog.Error("Error casting correlation ID to string", "correlationID", result.CorrelationID)
		return
	}

	s.store.SetThumbnail(mediaItemID, result.Outpath)
	// TODO: Server-Sent Events
}
