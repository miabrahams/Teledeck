package services

import (
	"io"
	"log/slog"
	"os"
	"testing"
)

func setupTaggingService() *TaggingService {
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	return NewTaggingService(logger)
}

var taggingService *TaggingService

func TestMain(m *testing.M) {
	taggingService = setupTaggingService()
	os.Exit(m.Run())
}

func TestTagImage(t *testing.T) {
	tests := []struct {
		name      string
		imagePath string
		cutoff    float64
		wantTag   string
		wantProb  float64
		wantErr   bool
	}{
		{
			name:      "Test Image",
			imagePath: "static/media/photo_2019-09-17_07-43-27.jpg",
			cutoff:    0.3,
			wantTag:   "tiger",
			wantProb:  0.90,
		},
	}

	// TODO: Add testing images
	result, err := taggingService.TagImage(tests[0].imagePath, tests[0].cutoff)
	if err != nil {
		t.Fatalf("Error tagging image: %v", err)
	}

	rating := -1.0
	for _, r := range result {
		t.Logf("Tag: %s, Probability: %.2f", r.Tag, r.Probability)
		if r.Tag == tests[0].wantTag {
			rating = r.Probability
		}
	}
	if rating < tests[0].wantProb {
		if rating == -1.0 {
			t.Errorf("Tag probability less than expected: rating < 0.3 < %f", tests[0].wantProb)
		} else {
			t.Errorf("Tag probability less than expected: %f < %f", rating, tests[0].wantProb)
		}
	}
}
