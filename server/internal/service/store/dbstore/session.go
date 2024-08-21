package dbstore

import (
	"fmt"
	"teledeck/internal/models"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

type SessionStore struct {
	db *gorm.DB
}

type NewSessionStoreParams struct {
	DB *gorm.DB
}

func NewSessionStore(params NewSessionStoreParams) *SessionStore {
	return &SessionStore{
		db: params.DB,
	}
}

func (s *SessionStore) CreateSession(session *models.Session) (*models.Session, error) {

	session.SessionID = uuid.New().String()

	result := s.db.Create(session)

	if result.Error != nil {
		return nil, result.Error
	}
	return session, nil
}

func (s *SessionStore) GetUserFromSession(sessionID string, userID string) (*models.User, error) {
	var session models.Session

	err := s.db.Preload("User", func(db *gorm.DB) *gorm.DB {
		return db.Select("ID", "Email")
	}).Where("session_id = ? AND user_id = ?", sessionID, userID).First(&session).Error

	if err != nil {
		return nil, err
	}

	if session.User.ID == 0 {
		return nil, fmt.Errorf("no user associated with the session")
	}

	return &session.User, nil
}
