package store

import (
	"teledeck/internal/models"
)

type UserStore interface {
	CreateUser(email string, password string) error
	GetUser(email string) (*models.User, error)
}

type SessionStore interface {
	CreateSession(session *models.Session) (*models.Session, error)
	GetUserFromSession(sessionID string, userID string) (*models.User, error)
}

type MediaStore interface {
	GetTotalMediaItems() int64
	GetMediaItemCount(P models.SearchPrefs) int64
	GetPaginatedMediaItems(page, itemsPerPage int, P models.SearchPrefs) ([]models.MediaItemWithMetadata, error)
	GetPaginatedMediaItemIds(page, itemsPerPage int, P models.SearchPrefs) ([]models.MediaItemID, error)
	GetAllMediaItems() ([]models.MediaItemWithMetadata, error)
	ToggleFavorite(id string) (*models.MediaItemWithMetadata, error)
	GetMediaItem(id string) (*models.MediaItemWithMetadata, error)
	MarkDeleted(item *models.MediaItem) error
	MarkDeletedAndGetNext(item *models.MediaItem, page int, itemsPerPage int, P models.SearchPrefs) (*models.MediaItemWithMetadata, error)
	GetThumbnail(mediaItemID string) (string, error)
	SetThumbnail(mediaItemID, fileName string) error
	UndoLastDeleted() (*models.MediaItemWithMetadata, error)
}

type TagsStore interface {
	GetAllTags() ([]models.Tag, error)
	GetTagID(name string) (models.Tag, error)
	GetTagIDs(names []string) ([]models.Tag, error)
	GetItemTags(itemid string) ([]models.TagWeight, error)
	SetItemTags(weights []models.TagWeight, itemid string) error
}

type AestheticsStore interface {
	GetImageScore(id string) (float32, error)
	SetImageScore(id string, score float32) error
}
