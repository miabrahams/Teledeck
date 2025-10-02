package main

import (
	"errors"
	"fmt"
	"log/slog"
	"os"
	"teledeck/internal/config"
	"teledeck/internal/controllers"
	"teledeck/internal/models"
	external "teledeck/internal/service/external/api"
	"teledeck/internal/service/store/db"
	"teledeck/internal/service/store/dbstore"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	if err := runMain(); err != nil {
		slog.Default().Error("Error running main", "error", err)
		os.Exit(1)
	}
}

func runMain() error {
	cfg, cfgErr := config.LoadConfig()
	db, dbErr := db.Open(cfg.DatabasePath())
	if err := errors.Join(cfgErr, dbErr); err != nil {
		return err
	}

	logger := slog.Default()
	tagsStore := dbstore.NewTagsStore(db, logger)
	mediaStore := dbstore.NewMediaStore(db, logger)

	conn, err := grpc.NewClient(cfg.GRPCAddress(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return fmt.Errorf("connecting to tagging service: %w", err)
	}
	taggingService := external.NewTaggingService(logger, conn)

	tagsController := controllers.NewTagsController(tagsStore, mediaStore, taggingService)

	allItems, err := mediaStore.GetAllMediaItems()
	if err != nil {
		return fmt.Errorf("getting all media items: %w", err)
	}

	for _, item := range allItems {
		if models.IsPhoto(item.MediaType) {
			tags, err := tagsController.TagImageItem(&item.MediaItem, 0.4)
			if err != nil {
				return fmt.Errorf("tagging image: Filename %s  ID: %s  err: %w", item.FileName, item.ID, err)
			}
			logger.Info("Tagged image", "Filename", item.FileName, "Tags", tags)
		}
	}
	return nil
}
