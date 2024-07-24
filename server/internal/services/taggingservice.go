package services

import (
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
)

type PredictionResult struct {
	Tag         string  `json:"tag"`
	Probability float64 `json:"prob"`
}

type TaggingService struct {
	logger *slog.Logger
	client *http.Client
}

func NewTaggingService(logger *slog.Logger) *TaggingService {
	return &TaggingService{
		logger: logger,
		client: &http.Client{},
	}
}

func (s *TaggingService) TagImage(imagePath string, cutoff float64) ([]PredictionResult, error) {

	// TODO: Allow configurable server address
	req, _ := http.NewRequest("POST", "http://localhost:8081/predict/url", nil)

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

	s.logger.Info("Received response", "Body:", rawBody)
	var result []PredictionResult
	err = json.Unmarshal(rawBody, &result)
	if err != nil {
		s.logger.Error("Error decoding response body: %v", "Error", err)
		return nil, err
	}

	return result, nil
}
