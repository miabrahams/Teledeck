package handlers

import (
	"bytes"
	"encoding/base64"

	"goth/internal/models"
	hashmock "goth/internal/service/hash/mock"
	storemock "goth/internal/service/store/mock"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"gorm.io/gorm"
)

func TestLogin(t *testing.T) {

	user := &models.User{ID: 1, Email: "test@example.com", Password: "password"}

	testCases := []struct {
		name                         string
		email                        string
		password                     string
		expectedStatusCode           int
		getUserResult                *models.User
		comparePasswordAndHashResult bool
		getUserError                 error
		createSessionResult          *models.Session
		expectedCookie               *http.Cookie
	}{
		{
			name:                         "success",
			email:                        user.Email,
			password:                     user.Password,
			comparePasswordAndHashResult: true,
			getUserResult:                user,
			createSessionResult:          &models.Session{UserID: 1, SessionID: "sessionId"},
			expectedStatusCode:           http.StatusOK,
			expectedCookie: &http.Cookie{
				Name:     "session",
				Value:    base64.StdEncoding.EncodeToString([]byte("sessionId:1")),
				HttpOnly: true,
			},
		},
		{
			name:               "fail - user not found",
			email:              user.Email,
			password:           user.Password,
			getUserResult:      nil,
			getUserError:       gorm.ErrRecordNotFound,
			expectedStatusCode: http.StatusUnauthorized,
		},
		{
			name:                         "fail - invalid password",
			email:                        user.Email,
			password:                     user.Password,
			getUserResult:                user,
			comparePasswordAndHashResult: false,
			expectedStatusCode:           http.StatusUnauthorized,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			assert := assert.New(t)
			userStore := &storemock.UserStoreMock{}
			sessionStore := &storemock.SessionStoreMock{}
			passwordHash := &hashmock.PasswordHashMock{}

			userStore.On("GetUser", tc.email).Return(tc.getUserResult, tc.getUserError)

			if tc.getUserResult != nil {
				passwordHash.On("ComparePasswordAndHash", tc.password, tc.getUserResult.Password).Return(tc.comparePasswordAndHashResult, nil)
			}

			if tc.getUserResult != nil && tc.comparePasswordAndHashResult {
				sessionStore.On("CreateSession", &models.Session{UserID: tc.getUserResult.ID}).Return(tc.createSessionResult, nil)
			}

			handler := NewPostLoginHandler(PostLoginHandlerParams{
				UserStore:         userStore,
				SessionStore:      sessionStore,
				PasswordHash:      passwordHash,
				SessionCookieName: "session",
			})
			body := bytes.NewBufferString("email=" + tc.email + "&password=" + tc.password)
			req, _ := http.NewRequest("POST", "/", body)
			req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
			rr := httptest.NewRecorder()

			handler.ServeHTTP(rr, req)

			assert.Equal(tc.expectedStatusCode, rr.Code, "handler returned wrong status code: got %v want %v", rr.Code, tc.expectedStatusCode)

			cookies := rr.Result().Cookies()
			if tc.expectedCookie != nil {

				sessionCookie := cookies[0]

				assert.Equal(tc.expectedCookie.Name, sessionCookie.Name, "handler returned wrong cookie name: got %v want %v", sessionCookie.Name, tc.expectedCookie.Name)
				assert.Equal(tc.expectedCookie.Value, sessionCookie.Value, "handler returned wrong cookie value: got %v want %v", sessionCookie.Value, tc.expectedCookie.Value)
				assert.Equal(tc.expectedCookie.HttpOnly, sessionCookie.HttpOnly, "handler returned wrong cookie HttpOnly: got %v want %v", sessionCookie.HttpOnly, tc.expectedCookie.HttpOnly)
			} else {
				assert.Empty(cookies, "handler returned unexpected cookie: got %v want %v", cookies, tc.expectedCookie)
			}

			userStore.AssertExpectations(t)
			passwordHash.AssertExpectations(t)
			sessionStore.AssertExpectations(t)
		})
	}
}
