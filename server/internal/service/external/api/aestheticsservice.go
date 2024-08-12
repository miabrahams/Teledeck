package external

import (
	"context"
	"fmt"
	"image"
	"log/slog"
	"teledeck/internal/genproto/ai_server"

	"google.golang.org/grpc"
)

type AestheticsService struct {
	logger *slog.Logger
	client ai_server.ImageScorerClient
}

func NewAestheticsService(logger *slog.Logger, conn *grpc.ClientConn) *AestheticsService {
	return &AestheticsService{
		logger: logger,
		client: ai_server.NewImageScorerClient(conn),
	}
}

func (s *AestheticsService) ScoreImage(imagePath string) (float32, error) {
	req := &ai_server.ImageUrlRequest{ImageUrl: imagePath}

	ctx := context.Background()
	res, err := s.client.PredictUrl(ctx, req)
	if err != nil {
		s.logger.Error("Error calling PredictUrl", "Error", err)
		return 0, err
	}

	return res.Score, nil
}

func (s *AestheticsService) ScoreImageData(image image.Image) (float32, error) {
	return 0, fmt.Errorf("not implemented")
}
