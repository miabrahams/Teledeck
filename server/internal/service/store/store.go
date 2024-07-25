package store

import (
	"goth/internal/models"
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
	GetAllMediaItems() ([]models.MediaItemWithMetadata, error)
	ToggleFavorite(id string) (*models.MediaItemWithMetadata, error)
	GetMediaItem(id string) (*models.MediaItemWithMetadata, error)
	MarkDeleted(item *models.MediaItem) error
}

type TagsStore interface {
	GetTagID(name string) (models.Tag, error)
	GetTagIDs(names []string) ([]models.Tag, error)
	GetItemTags(itemid string) ([]models.TagWeight, error)
	SetItemTags(weights []models.TagWeight, itemid string) error
}
