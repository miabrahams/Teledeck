package mock

import (
	"goth/internal/models"

	"github.com/stretchr/testify/mock"
)

type UserStoreMock struct {
	mock.Mock
}

func (m *UserStoreMock) CreateUser(email string, password string) error {
	args := m.Called(email, password)

	return args.Error(0)
}

func (m *UserStoreMock) GetUser(email string) (*models.User, error) {
	args := m.Called(email)
	return args.Get(0).(*models.User), args.Error(1)
}

type SessionStoreMock struct {
	mock.Mock
}

func (m *SessionStoreMock) CreateSession(session *models.Session) (*models.Session, error) {
	args := m.Called(session)
	return args.Get(0).(*models.Session), args.Error(1)
}

func (m *SessionStoreMock) GetUserFromSession(sessionID string, userID string) (*models.User, error) {
	args := m.Called(sessionID, userID)
	return args.Get(0).(*models.User), args.Error(1)
}
