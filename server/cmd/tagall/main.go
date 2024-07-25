package main

import (
	"goth/internal/config"
	"goth/internal/controllers"
	"goth/internal/models"
	external "goth/internal/service/external/api"
	"goth/internal/service/store/db"
	"goth/internal/service/store/dbstore"
	"log/slog"
)

func main() {
	cfg := config.MustLoadConfig()
	db := db.MustOpen(cfg.DatabaseName)
	logger := slog.Default()
	tagsStore := dbstore.NewTagsStore(db, logger)
	mediaStore := dbstore.NewMediaStore(db, logger)
	taggingService := external.NewTaggingService(logger, cfg.TagServicePort)

	tagsController := controllers.NewTagsController(tagsStore, mediaStore, taggingService)

	allItems, err := mediaStore.GetAllMediaItems()
	if err != nil {
		logger.Error("Error getting all media items", "Error", err)
		return
	}

	for _, item := range allItems {
		if models.IsPhoto(item.MediaType) {
			tags, err := tagsController.TagImageItem(&item.MediaItem, 0.4)
			if err != nil {
				logger.Error("Error tagging image", "Filename", item.FileName, "ID", item.ID, "Error", err)
			}
			logger.Info("Tagged image", "Filename", item.FileName, "Tags", tags)
		}
	}
}
