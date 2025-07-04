package external

import (
	"log/slog"
	"os"
	"teledeck/internal/config"
	"testing"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// TODO: Configurable
func setupTaggingService() (*TaggingService, error) {
	logger := slog.Default()
	cfg, err := config.LoadConfig()
	if err != nil {
		logger.Error("Error loading config", "error", err)
		return nil, err
	}

	conn, err := grpc.NewClient(cfg.TaggerURL, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		logger.Info("Could not connect to AI services.")
		return nil, err
	}
	return NewTaggingService(logger, conn), nil
}

var taggingService *TaggingService

func TestMain(m *testing.M) {
	var err error
	taggingService, err = setupTaggingService()
	if err != nil {
		slog.Error("Failed to setup tagging service", "error", err)
		return
	}
	os.Exit(m.Run())
}

func TestTagImage(t *testing.T) {
	tests := []struct {
		name      string
		imagePath string
		cutoff    float32
		wantTag   string
		wantProb  float32
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

	rating := float32(-1.0)
	for _, r := range result {
		t.Logf("Tag: %s, Probability: %.2f", r.Name, r.Weight)
		if r.Name == tests[0].wantTag {
			rating = r.Weight
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
