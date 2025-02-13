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

type MediaController struct {
	store       store.MediaStore
	thumbnailer *thumbnailer.Thumbnailer
	fileOps     files.LocalFileOperator
	fileRoot    string
}

var (
	ErrThumbnailInProgress = errors.New("thumbnail generation in progress")
	vidTypes               = []string{"video", "webp", "gif"}
)

func NewMediaController(store store.MediaStore, fileOps files.LocalFileOperator,
	fileRoot string, tn *thumbnailer.Thumbnailer,
) *MediaController {
	c := MediaController{
		store:       store,
		fileOps:     fileOps,
		fileRoot:    fileRoot,
		thumbnailer: tn,
	}
	tn.SetHandler(c.onThumbnailGen)
	return &c
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

func (s *MediaController) GetPaginatedMediaItemIds(page, itemsPerPage int, P models.SearchPrefs) ([]models.MediaItemID, error) {
	return s.store.GetPaginatedMediaItemIds(page, itemsPerPage, P)
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

// Note: May not have a way to handle failed thumbnail generations
func (s *MediaController) GetThumbnail(mediaItemID string) (string, error) {
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
func (s *MediaController) onThumbnailGen(result thumbnailer.Result) {
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
