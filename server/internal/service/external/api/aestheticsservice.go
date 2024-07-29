package external

import (
	"encoding/json"
	"fmt"
	"goth/internal/models"
	"image"
	"io"
	"log/slog"
	"net/http"
)

type AestheticsService struct {
	logger *slog.Logger
	client *http.Client
	host   string
}

func NewAestheticsService(logger *slog.Logger, port string) *AestheticsService {

	return &AestheticsService{
		logger: logger,
		client: &http.Client{},
		host:   "http://localhost:" + port,
	}
}

func (s *AestheticsService) ScoreImage(imagePath string) (float32, error) {

	req, _ := http.NewRequest("POST", s.host+"/score/url", nil)

	q := req.URL.Query()
	q.Add("image_path", imagePath)

	req.URL.RawQuery = q.Encode()
	req.Header.Add("Accept", "application/json")

	res, err := s.client.Do(req)
	if err != nil {
		return 0, err
	}

	rawBody, err := io.ReadAll(res.Body)
	if err != nil {
		s.logger.Error("Error reading response body", "Error", err)
		return 0, err
	}

	var result models.ScoreResult
	err = json.Unmarshal(rawBody, &result)
	if err != nil {
		s.logger.Error("Error decoding response body: %v", "Error", err)
		return 0, err
	}

	return result.Score, nil
}

func (s *AestheticsService) ScoreImageData(image image.Image) (float32, error) {
	return 0, fmt.Errorf("not implemented")
}
