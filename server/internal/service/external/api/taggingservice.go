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

type TaggingService struct {
	logger *slog.Logger
	client *http.Client
	host   string
}

func NewTaggingService(logger *slog.Logger, port string) *TaggingService {

	return &TaggingService{
		logger: logger,
		client: &http.Client{},
		host:   "http://localhost:" + port,
	}
}

func (s *TaggingService) TagImage(imagePath string, cutoff float32) ([]models.TagWeight, error) {

	// TODO: Allow configurable server address

	req, _ := http.NewRequest("POST", s.host+"/predict/url", nil)

	q := req.URL.Query()
	q.Add("image_path", imagePath)

	q.Add("cutoff", fmt.Sprintf("%.2f", cutoff))
	req.URL.RawQuery = q.Encode()
	req.Header.Add("Accept", "application/json")

	res, err := s.client.Do(req)
	if err != nil {
		return nil, err
	}

	rawBody, err := io.ReadAll(res.Body)
	if err != nil {
		s.logger.Error("Error reading response body", "Error", err)
		return nil, err
	}

	// s.logger.Info("Received response", "Body:", rawBody)
	var result []models.TagWeight
	err = json.Unmarshal(rawBody, &result)
	if err != nil {
		s.logger.Error("Error decoding response body: %v", "Error", err)
		return nil, err
	}

	return result, nil
}

func (s *TaggingService) TagImageData(image image.Image, cutoff float32) ([]models.TagWeight, error) {
	return nil, fmt.Errorf("not implemented")
}
