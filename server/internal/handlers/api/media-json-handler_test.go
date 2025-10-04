package webapi

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"reflect"
	"testing"

	"teledeck/internal/controllers"
	mocks "teledeck/internal/controllers/mocks"
	"teledeck/internal/middleware"
	"teledeck/internal/models"

	"github.com/go-chi/chi/v5"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

func withMeta(item models.MediaItem) *models.MediaItemWithMetadata {
	return &models.MediaItemWithMetadata{
		MediaItem: item,
	}
}

func expectUnmarshalTo(t *testing.T, b io.Reader, expected any) {
	if expected == nil {
		assert.Empty(t, b)
		return
	}
	expectedType := reflect.TypeOf(expected)
	actualPtr := reflect.New(expectedType).Interface()
	err := json.NewDecoder(b).Decode(actualPtr)
	assert.NoError(t, err)
	actualValue := reflect.ValueOf(actualPtr).Elem().Interface()
	assert.Equal(t, expected, actualValue)
}

func TestMediaJSONHandler_GetGallery(t *testing.T) {
	tests := []struct {
		name           string
		setupContext   func(ctx context.Context) context.Context
		mockSetup      func(mockCtrl *mocks.MockMediaController)
		expectedStatus int
		expectedBody   any
	}{
		{
			name: "happy path",
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("GetPaginatedMediaItems", 1, 100, mock.AnythingOfType("models.SearchPrefs")).
					Return([]models.MediaItemWithMetadata{*withMeta(models.MediaItem{ID: "1"})}, nil)
			},
			expectedStatus: http.StatusOK,
			expectedBody: []models.MediaItemWithMetadata{{
				MediaItem: models.MediaItem{ID: "1"},
			}},
		},
		{
			name: "missing search prefs",
			setupContext: func(ctx context.Context) context.Context {
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup:      func(mockCtrl *mocks.MockMediaController) {},
			expectedStatus: http.StatusInternalServerError,
			expectedBody:   APIError{Message: "Error fetching preferences"},
		},
		{
			name: "missing page",
			setupContext: func(ctx context.Context) context.Context {
				return context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
			},
			mockSetup:      func(mockCtrl *mocks.MockMediaController) {},
			expectedStatus: http.StatusOK, // No explicit error, but fmt.Printf is called; in test, we check no response
		},
		{
			name: "controller error",
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("GetPaginatedMediaItems", 1, 100, mock.AnythingOfType("models.SearchPrefs")).Return(nil, errors.New("db error"))
			},
			expectedStatus: http.StatusInternalServerError,
			expectedBody:   APIError{Message: "Error fetching media items"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockCtrl := &mocks.MockMediaController{}
			tt.mockSetup(mockCtrl)
			handler := NewMediaJSONHandler(mockCtrl, slog.Default())

			req := httptest.NewRequest(http.MethodGet, "/gallery", nil)
			req = req.WithContext(tt.setupContext(req.Context()))
			w := httptest.NewRecorder()

			handler.GetGallery(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)
			expectUnmarshalTo(t, w.Body, tt.expectedBody)
			mockCtrl.AssertExpectations(t)
		})
	}
}

func TestMediaJSONHandler_GetThumbnail(t *testing.T) {
	tests := []struct {
		name           string
		mediaItemID    string
		mockSetup      func(mockCtrl *mocks.MockMediaController)
		expectedStatus int
		expectedBody   any
	}{
		{
			name:        "happy path",
			mediaItemID: "123",
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("GetThumbnail", "123").Return("thumb.jpg", nil)
			},
			expectedStatus: http.StatusOK,
			expectedBody:   ThumbnailResponse{FileName: "thumb.jpg"},
		},
		{
			name:        "thumbnail in progress",
			mediaItemID: "123",
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("GetThumbnail", "123").Return("", controllers.ErrThumbnailInProgress)
			},
			expectedStatus: http.StatusAccepted,
			expectedBody:   ThumbnailResponse{Message: "Thumbnail generation in progress"},
		},
		{
			name:        "controller error",
			mediaItemID: "123",
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("GetThumbnail", "123").Return("", errors.New("gen error"))
			},
			expectedStatus: http.StatusInternalServerError,
			expectedBody:   APIError{Message: "Error generating thumbnail: gen error"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockCtrl := &mocks.MockMediaController{}
			tt.mockSetup(mockCtrl)
			handler := NewMediaJSONHandler(mockCtrl, slog.Default())

			req := httptest.NewRequest(http.MethodGet, "/thumbnail/"+tt.mediaItemID, nil)
			rctx := chi.NewRouteContext()
			rctx.URLParams.Add("mediaItemID", tt.mediaItemID)
			req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
			w := httptest.NewRecorder()

			handler.GetThumbnail(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)
			expectUnmarshalTo(t, w.Body, tt.expectedBody)
			mockCtrl.AssertExpectations(t)
		})
	}
}

func TestMediaJSONHandler_GetGalleryIds(t *testing.T) {
	tests := []struct {
		name           string
		setupContext   func(ctx context.Context) context.Context
		mockSetup      func(mockCtrl *mocks.MockMediaController)
		expectedStatus int
		expectedBody   any
	}{
		{
			name: "happy path",
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("GetPaginatedMediaItemIds", 1, 100, mock.AnythingOfType("models.SearchPrefs")).Return([]models.MediaItemID{{ID: "1"}}, nil)
			},
			expectedStatus: http.StatusOK,
			expectedBody:   []models.MediaItemID{{ID: "1"}},
		},
		{
			name: "controller error",
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("GetPaginatedMediaItemIds", 1, 100, mock.AnythingOfType("models.SearchPrefs")).Return(nil, errors.New("db error"))
			},
			expectedStatus: http.StatusInternalServerError,
			expectedBody:   APIError{Message: "Error fetching media items"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockCtrl := &mocks.MockMediaController{}
			tt.mockSetup(mockCtrl)
			handler := NewMediaJSONHandler(mockCtrl, slog.Default())

			req := httptest.NewRequest(http.MethodGet, "/gallery-ids", nil)
			req = req.WithContext(tt.setupContext(req.Context()))
			w := httptest.NewRecorder()

			handler.GetGalleryIds(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)
			expectUnmarshalTo(t, w.Body, tt.expectedBody)
			mockCtrl.AssertExpectations(t)
		})
	}
}

func TestMediaJSONHandler_GetMediaItem(t *testing.T) {
	tests := []struct {
		name           string
		setupContext   func(ctx context.Context) context.Context
		mockSetup      func(mockCtrl *mocks.MockMediaController)
		expectedStatus int
		expectedBody   any
	}{
		{
			name: "happy path",
			setupContext: func(ctx context.Context) context.Context {
				return context.WithValue(ctx, middleware.MediaItemKey, &models.MediaItemWithMetadata{MediaItem: models.MediaItem{ID: "1"}})
			},
			mockSetup:      func(mockCtrl *mocks.MockMediaController) {},
			expectedStatus: http.StatusOK,
			expectedBody:   &models.MediaItemWithMetadata{MediaItem: models.MediaItem{ID: "1"}},
		},
		{
			name:           "missing media item",
			setupContext:   func(ctx context.Context) context.Context { return ctx },
			mockSetup:      func(mockCtrl *mocks.MockMediaController) {},
			expectedStatus: http.StatusUnprocessableEntity,
			expectedBody:   APIError{Message: "Media item not found"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockCtrl := &mocks.MockMediaController{}
			tt.mockSetup(mockCtrl)
			handler := NewMediaJSONHandler(mockCtrl, slog.Default())

			req := httptest.NewRequestWithContext(t.Context(), http.MethodGet, "/media/1", nil)
			req = req.WithContext(tt.setupContext(req.Context()))
			w := httptest.NewRecorder()

			handler.GetMediaItem(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)
			expectUnmarshalTo(t, w.Body, tt.expectedBody)
			mockCtrl.AssertExpectations(t)
		})
	}
}

func TestMediaJSONHandler_GetNumPages(t *testing.T) {
	tests := []struct {
		name           string
		setupContext   func(ctx context.Context) context.Context
		mockSetup      func(mockCtrl *mocks.MockMediaController)
		expectedStatus int
		expectedBody   NumPagesResponse
	}{
		{
			name: "happy path",
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("GetMediaItemCount", mock.AnythingOfType("models.SearchPrefs")).Return(int64(250))
			},
			expectedStatus: http.StatusOK,
			expectedBody:   NumPagesResponse{TotalPages: 3}, // 250 / 100 = 2.5 -> 3
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockCtrl := &mocks.MockMediaController{}
			tt.mockSetup(mockCtrl)
			handler := NewMediaJSONHandler(mockCtrl, slog.Default())

			req := httptest.NewRequest(http.MethodGet, "/num-pages", nil)
			req = req.WithContext(tt.setupContext(req.Context()))
			w := httptest.NewRecorder()

			handler.GetNumPages(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)
			var actual NumPagesResponse
			json.Unmarshal(w.Body.Bytes(), &actual)
			assert.Equal(t, tt.expectedBody, actual)
			mockCtrl.AssertExpectations(t)
		})
	}
}

func TestMediaJSONHandler_ToggleFavorite(t *testing.T) {
	tests := []struct {
		name           string
		setupContext   func(ctx context.Context) context.Context
		mockSetup      func(mockCtrl *mocks.MockMediaController)
		expectedStatus int
		expectedBody   any
	}{
		{
			name: "happy path",
			setupContext: func(ctx context.Context) context.Context {
				return context.WithValue(ctx, middleware.MediaItemKey, withMeta(models.MediaItem{ID: "1"}))
			},
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("ToggleFavorite", "1").Return(withMeta(models.MediaItem{ID: "1", Favorite: true}), nil)
			},
			expectedStatus: http.StatusOK,
			expectedBody:   withMeta(models.MediaItem{ID: "1", Favorite: true}),
		},
		{
			name: "controller error",
			setupContext: func(ctx context.Context) context.Context {
				return context.WithValue(ctx, middleware.MediaItemKey, withMeta(models.MediaItem{ID: "1"}))
			},
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("ToggleFavorite", "1").Return(nil, errors.New("db error"))
			},
			expectedStatus: http.StatusInternalServerError,
			expectedBody:   APIError{Message: "Error toggling favorite"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockCtrl := &mocks.MockMediaController{}
			tt.mockSetup(mockCtrl)
			handler := NewMediaJSONHandler(mockCtrl, slog.Default())

			req := httptest.NewRequest(http.MethodPost, "/toggle-favorite", nil)
			req = req.WithContext(tt.setupContext(req.Context()))
			w := httptest.NewRecorder()

			handler.ToggleFavorite(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)
			expectUnmarshalTo(t, w.Body, tt.expectedBody)
			mockCtrl.AssertExpectations(t)
		})
	}
}

func TestMediaJSONHandler_DeleteMedia(t *testing.T) {
	tests := []struct {
		name           string
		setupContext   func(ctx context.Context) context.Context
		mockSetup      func(mockCtrl *mocks.MockMediaController)
		expectedStatus int
		expectedBody   any
	}{
		{
			name: "happy path",
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.MediaItemKey, withMeta(models.MediaItem{ID: "1", Favorite: false}))
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("RecycleAndGetNext", mock.AnythingOfType("*models.MediaItem"), 1, mock.AnythingOfType("models.SearchPrefs")).Return(withMeta(models.MediaItem{ID: "2"}), nil)
			},
			expectedStatus: http.StatusOK,
			expectedBody:   withMeta(models.MediaItem{ID: "2"}),
		},
		{
			name: "favorite item",
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.MediaItemKey, withMeta(models.MediaItem{ID: "1", Favorite: true}))
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup:      func(mockCtrl *mocks.MockMediaController) {},
			expectedStatus: http.StatusBadRequest,
			expectedBody:   APIError{Message: "Cannot delete a favorite item"},
		},
		{
			name: "controller error",
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.MediaItemKey, withMeta(models.MediaItem{ID: "1", Favorite: false}))
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("RecycleAndGetNext", mock.AnythingOfType("*models.MediaItem"), 1, mock.AnythingOfType("models.SearchPrefs")).Return(nil, errors.New("db error"))
			},
			expectedStatus: http.StatusInternalServerError,
			expectedBody:   APIError{Message: "Error deleting item"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockCtrl := &mocks.MockMediaController{}
			tt.mockSetup(mockCtrl)
			handler := NewMediaJSONHandler(mockCtrl, slog.Default())

			req := httptest.NewRequest(http.MethodDelete, "/delete", nil)
			req = req.WithContext(tt.setupContext(req.Context()))
			w := httptest.NewRecorder()

			handler.DeleteMedia(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)
			expectUnmarshalTo(t, w.Body, tt.expectedBody)
			mockCtrl.AssertExpectations(t)
		})
	}
}

func TestMediaJSONHandler_DeletePage(t *testing.T) {
	tests := []struct {
		name           string
		requestBody    DeletePageRequest
		setupContext   func(ctx context.Context) context.Context
		mockSetup      func(mockCtrl *mocks.MockMediaController)
		expectedStatus int
		expectedBody   any
	}{
		{
			name:        "happy path",
			requestBody: DeletePageRequest{ItemIDs: []string{"1", "2"}},
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.EXPECT().GetPaginatedMediaItems(1, 100, mock.AnythingOfType("models.SearchPrefs")).
					Return([]models.MediaItemWithMetadata{
						*withMeta(models.MediaItem{ID: "1"}),
						*withMeta(models.MediaItem{ID: "2"}),
					}, nil)
				mockCtrl.EXPECT().
					DeletePageItems([]string{"1", "2"}, 1, models.SearchPrefs{}).
					Return(&controllers.DeletePageResult{
						DeletedCount: 2,
						NextPage:     []models.MediaItemWithMetadata{*withMeta(models.MediaItem{ID: "3"})},
					}, nil)
			},
			expectedStatus: http.StatusOK,
			expectedBody: &controllers.DeletePageResult{
				DeletedCount: 2,
				SkippedCount: 0,
				NextPage:     []models.MediaItemWithMetadata{*withMeta(models.MediaItem{ID: "3"})}},
		},
		{
			name:        "invalid request body",
			requestBody: DeletePageRequest{},
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup:      func(mockCtrl *mocks.MockMediaController) {},
			expectedStatus: http.StatusBadRequest,
			expectedBody:   APIError{Message: "No item IDs provided"},
		},
		{
			name:        "no item IDs",
			requestBody: DeletePageRequest{ItemIDs: []string{}},
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup:      func(mockCtrl *mocks.MockMediaController) {},
			expectedStatus: http.StatusBadRequest,
			expectedBody:   APIError{Message: "No item IDs provided"},
		},
		{
			name:        "item not on page",
			requestBody: DeletePageRequest{ItemIDs: []string{"999"}},
			setupContext: func(ctx context.Context) context.Context {
				ctx = context.WithValue(ctx, middleware.SearchPrefKey, models.SearchPrefs{})
				return context.WithValue(ctx, middleware.PageKey, 1)
			},
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("GetPaginatedMediaItems", 1, 100, mock.AnythingOfType("models.SearchPrefs")).
					Return([]models.MediaItemWithMetadata{*withMeta(models.MediaItem{ID: "1"})}, nil)
			},
			expectedStatus: http.StatusBadRequest,
			expectedBody:   APIError{Message: "Item ID 999 is not on the current page"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockCtrl := &mocks.MockMediaController{}
			tt.mockSetup(mockCtrl)
			handler := NewMediaJSONHandler(mockCtrl, slog.Default())

			body, _ := json.Marshal(tt.requestBody)
			req := httptest.NewRequest(http.MethodPost, "/delete-page", bytes.NewReader(body))
			req = req.WithContext(tt.setupContext(req.Context()))
			w := httptest.NewRecorder()

			handler.DeletePage(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)
			expectUnmarshalTo(t, w.Body, tt.expectedBody)
			mockCtrl.AssertExpectations(t)
		})
	}
}

func TestMediaJSONHandler_UndoDelete(t *testing.T) {
	tests := []struct {
		name           string
		mockSetup      func(mockCtrl *mocks.MockMediaController)
		expectedStatus int
		expectedBody   any
	}{
		{
			name: "happy path",
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("UndoLastDeleted").Return(withMeta(models.MediaItem{ID: "1"}), nil)
			},
			expectedStatus: http.StatusOK,
			expectedBody:   withMeta(models.MediaItem{ID: "1"}),
		},
		{
			name: "no deleted items",
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("UndoLastDeleted").Return(nil, nil)
			},
			expectedStatus: http.StatusNotFound,
			expectedBody:   APIError{Message: "No deleted items to restore"},
		},
		{
			name: "controller error",
			mockSetup: func(mockCtrl *mocks.MockMediaController) {
				mockCtrl.On("UndoLastDeleted").Return(nil, errors.New("db error"))
			},
			expectedStatus: http.StatusInternalServerError,
			expectedBody:   APIError{Message: "Error undoing delete"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockCtrl := &mocks.MockMediaController{}
			tt.mockSetup(mockCtrl)
			handler := NewMediaJSONHandler(mockCtrl, slog.Default())

			req := httptest.NewRequest(http.MethodPost, "/undo-delete", nil)
			w := httptest.NewRecorder()

			handler.UndoDelete(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)
			expectUnmarshalTo(t, w.Body, tt.expectedBody)
			mockCtrl.AssertExpectations(t)
		})
	}
}
