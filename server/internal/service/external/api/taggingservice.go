package external

import (
	"context"
	"fmt"
	"image"
	"log"
	"log/slog"
	"teledeck/internal/models"
	"time"

	"google.golang.org/grpc"

	"teledeck/internal/genproto/ai_server"
)

type TaggingService struct {
	logger *slog.Logger
	client ai_server.ImageScorerClient
}

func NewTaggingService(logger *slog.Logger, conn *grpc.ClientConn) *TaggingService {

	client := ai_server.NewImageScorerClient(conn)

	return &TaggingService{
		logger: logger,
		client: client,
	}
}

func (s *TaggingService) TagImage(imagePath string, cutoff float32) ([]models.TagWeight, error) {

	// TODO: Allow configurable server address
	q := &ai_server.TagImageUrlRequest{ImageUrl: imagePath, Cutoff: cutoff}

	ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
	defer cancel()

	// Call the TagUrl RPC
	resp, err := s.client.TagUrl(ctx, q)
	if err != nil {
		log.Fatalf("could not tag image: %v", err)
	}

	// Process and print the tags
	var result []models.TagWeight
	for _, tag := range resp.Tags {
		result = append(result, models.TagWeight{Name: tag.Tag, Weight: tag.Weight})
	}

	return result, nil
}

func (s *TaggingService) TagImageData(image image.Image, cutoff float32) ([]models.TagWeight, error) {
	return nil, fmt.Errorf("not implemented")
}
