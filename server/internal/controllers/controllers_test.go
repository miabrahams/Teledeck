package controllers

import (
	"testing"

	"teledeck/internal/models"
	external "teledeck/internal/service/external/mocks"
	files "teledeck/internal/service/files/mocks"
	store "teledeck/internal/service/store/mocks"
	thumbnailer "teledeck/internal/service/thumbnailer/mocks"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func TestMediaController_RecycleMediaItem(t *testing.T) {
	req := require.New(t)

	ms := store.NewMockMediaStore(t)
	fo := files.NewMockLocalFileOperator(t)
	tn := thumbnailer.NewMockThumbnailer(t)

	mc := NewMediaController(ms, fo, "/root/media", tn)

	item := models.MediaItem{ID: "1", FileName: "a.jpg"}

	ms.On("MarkDeleted", &item).Return(nil)
	fo.On("Recycle", "a.jpg").Return(nil)

	err := mc.RecycleMediaItem(item)
	req.NoError(err)
}

func TestMediaController_DeletePageItems(t *testing.T) {
	req := require.New(t)

	ms := store.NewMockMediaStore(t)
	fo := files.NewMockLocalFileOperator(t)
	tn := thumbnailer.NewMockThumbnailer(t)

	mc := NewMediaController(ms, fo, "/root/media", tn)

	// Prepare two items: one favorite (skipped) and one deleted
	fav := models.MediaItemWithMetadata{MediaItem: models.MediaItem{ID: "fav", FileName: "f.jpg", Favorite: true}}
	del := models.MediaItemWithMetadata{MediaItem: models.MediaItem{ID: "del", FileName: "d.jpg", Favorite: false}}

	// store.GetMediaItem will be called for each ID
	ms.On("GetMediaItem", "fav").Return(&fav, nil)
	ms.On("GetMediaItem", "del").Return(&del, nil)

	// For deletion path, expect MarkDeleted and file recycle
	ms.On("MarkDeleted", &del.MediaItem).Return(nil)
	fo.On("Recycle", "d.jpg").Return(nil)

	// After deletions, GetPaginatedMediaItems should be called
	ms.On("GetPaginatedMediaItems", 1, 100, mock.Anything).Return([]models.MediaItemWithMetadata{del}, nil)

	res, err := mc.DeletePageItems([]string{"fav", "del"}, 1, models.SearchPrefs{})
	req.NoError(err)
	req.Equal(1, res.DeletedCount)
	req.Equal(1, res.SkippedCount)
	req.Len(res.NextPage, 1)
}

func TestMediaController_GetThumbnail_Behavior(t *testing.T) {
	req := require.New(t)

	ms := store.NewMockMediaStore(t)
	fo := files.NewMockLocalFileOperator(t)
	tn := thumbnailer.NewMockThumbnailer(t)

	mc := NewMediaController(ms, fo, "/root/media", tn)

	// Non-video item
	nonvid := models.MediaItemWithMetadata{MediaItem: models.MediaItem{ID: "1", FileName: "a.jpg"}, MediaType: "image"}
	ms.On("GetMediaItem", "1").Return(&nonvid, nil)
	_, err := mc.GetThumbnail("1")
	req.Error(err)

	// Video with existing thumbnail
	vid := models.MediaItemWithMetadata{MediaItem: models.MediaItem{ID: "2", FileName: "v.mp4"}, MediaType: "video"}
	ms.On("GetMediaItem", "2").Return(&vid, nil)
	ms.On("GetThumbnail", "2").Return("thumb.jpg", nil)
	name, err := mc.GetThumbnail("2")
	req.NoError(err)
	req.Equal("thumb.jpg", name)

	// Video without thumbnail: thumbnailer called and ErrThumbnailInProgress returned
	vid2 := models.MediaItemWithMetadata{MediaItem: models.MediaItem{ID: "3", FileName: "v2.mp4"}, MediaType: "video"}
	ms.On("GetMediaItem", "3").Return(&vid2, nil)
	ms.On("GetThumbnail", "3").Return("", nil)
	// Expect thumbnailer.GenerateVideoThumbnail called with absolute path
	tn.On("GenerateVideoThumbnail", "/root/media/v2.mp4", "", "3").Return(nil)

	name2, err := mc.GetThumbnail("3")
	req.Equal("", name2)
	req.ErrorIs(err, ErrThumbnailInProgress)
}

func TestTagsController_TaggingAndCache(t *testing.T) {
	req := require.New(t)

	ts := store.NewMockTagsStore(t)
	ms := store.NewMockMediaStore(t)
	svc := external.NewMockTaggingService(t)

	tc := NewTagsController(ts, ms, svc)

	// GetAllTags should populate cache from store
	ts.On("GetAllTags").Return([]models.Tag{{ID: 1, Name: "tag1"}}, nil)
	tags, err := tc.GetAllTags()
	req.NoError(err)
	req.Len(tags, 1)

	// Second call should return cached value and not call store again
	tags2, err := tc.GetAllTags()
	req.NoError(err)
	req.Len(tags2, 1)

	// TagImageByID -> TagImageItem path
	item := models.MediaItem{ID: "i1", FileName: "file.jpg"}
	ms.On("GetMediaItem", "i1").Return(&models.MediaItemWithMetadata{MediaItem: item}, nil)
	svc.On("TagImage", "static/media/file.jpg", float32(0.5)).Return([]models.TagWeight{{Name: "tag1", Weight: 0.9}}, nil)
	ts.On("SetItemTags", mock.Anything, "i1").Return(nil)

	tw, err := tc.TagImageByID("i1", 0.5)
	req.NoError(err)
	req.Len(tw, 1)
}

func TestAestheticsController_ScoreAndPersist(t *testing.T) {
	req := require.New(t)

	ast := store.NewMockAestheticsStore(t)
	ms := store.NewMockMediaStore(t)
	svc := external.NewMockAestheticsService(t)

	mc := NewMediaController(ms, files.NewMockLocalFileOperator(t), "/root/media", thumbnailer.NewMockThumbnailer(t))
	ac := NewAestheticsController(ast, mc, svc)

	item := models.MediaItem{ID: "s1", FileName: "img.jpg"}
	ms.On("GetMediaItem", "s1").Return(&models.MediaItemWithMetadata{MediaItem: item}, nil)
	svc.On("ScoreImage", "/root/media/img.jpg").Return(float32(0.77), nil)
	ast.On("SetImageScore", "s1", float32(0.77)).Return(nil)

	score, err := ac.ScoreImageByID("s1")
	req.NoError(err)
	req.Equal(float32(0.77), score)
}
