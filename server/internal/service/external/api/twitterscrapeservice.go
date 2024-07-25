package external

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	twitterscraper "github.com/imperatrona/twitter-scraper"
	"golang.org/x/time/rate"
)

type TwitterScrapeConfig struct {
	OutputDir              string
	Update                 bool
	RateLimit              float64
	MaxConcurrentDownloads int
	DownloadTimeout        time.Duration
	OverallTimeout         time.Duration
}

type TwitterScrapeService struct {
	scraper    *twitterscraper.Scraper
	logger     *slog.Logger
	httpClient *http.Client
	config     TwitterScrapeConfig
}

func NewTwitterScrapeConfig(outputDir string, update bool) TwitterScrapeConfig {
	return TwitterScrapeConfig{
		OutputDir:              outputDir,
		Update:                 update,
		RateLimit:              0.2,
		MaxConcurrentDownloads: 5,
		DownloadTimeout:        30 * time.Second,
		OverallTimeout:         10 * time.Minute,
	}
}

func NewTwitterScrapeService(logger *slog.Logger, config TwitterScrapeConfig) *TwitterScrapeService {
	return &TwitterScrapeService{
		scraper:    twitterscraper.New(),
		httpClient: &http.Client{},
		logger:     logger,
		config:     config,
	}
}

func (s *TwitterScrapeService) Login(AuthToken, CSRFToken string) error {
	s.scraper.SetAuthToken(twitterscraper.AuthToken{Token: AuthToken, CSRFToken: CSRFToken})
	if !s.scraper.IsLoggedIn() {
		return errors.New("login failed")
	}
	return nil
}

func (s *TwitterScrapeService) Run(ctx context.Context, username string, numberOfTweets int) error {
	ctx, cancel := context.WithTimeout(ctx, s.config.OverallTimeout)
	defer cancel()

	limiter := rate.NewLimiter(rate.Limit(s.config.RateLimit), 1)
	tweets := make(chan *twitterscraper.Tweet)
	errors := make(chan error, 1)
	var wg sync.WaitGroup

	// Start tweet fetcher
	go s.fetchMediaTweets(ctx, username, numberOfTweets, tweets, errors)

	// Start tweet processors
	for i := 0; i < s.config.MaxConcurrentDownloads; i++ {
		wg.Add(1)
		go s.processTweets(ctx, &wg, limiter, tweets, errors)
	}

	// Wait for all processors to finish
	go func() {
		wg.Wait()
		close(errors)
	}()

	// Collect errors
	var hadErr error = nil
	for err := range errors {
		if err != nil {
			s.logger.Error("Error processing tweet", "error", err)
			hadErr = err
		}
	}

	return hadErr
}

func (s *TwitterScrapeService) fetchMediaTweets(ctx context.Context, username string, numberOfTweets int, tweets chan<- *twitterscraper.Tweet, errors chan<- error) {
	defer close(tweets)
	// Collect tweets until timeout with ctx.Done() or channel is empty
	for tweet := range s.scraper.GetMediaTweets(ctx, username, numberOfTweets) {
		if tweet.Error != nil {
			errors <- tweet.Error
			return
		}
		select {
		case <-ctx.Done():
			return
		case tweets <- &tweet.Tweet:
			continue
		}
	}
}

func (s *TwitterScrapeService) processTweets(ctx context.Context, wg *sync.WaitGroup, limiter *rate.Limiter, tweets <-chan *twitterscraper.Tweet, errors chan<- error) {
	defer wg.Done()
	for tweet := range tweets {
		if tweet.IsRetweet {
			s.logger.Info("Skipping retweet", "Username", tweet.Username, "URL", tweet.PermanentURL, "ID", tweet.ID)
			continue
		}
		if err := limiter.Wait(ctx); err != nil {
			errors <- err
			return
		}
		s.downloadTweet(tweet, errors)
	}
}

func (s *TwitterScrapeService) downloadTweet(tweet *twitterscraper.Tweet, errors chan<- error) {
	var wg sync.WaitGroup
	wg.Add(2)

	go func() {
		defer wg.Done()
		s.downloadVideos(tweet, errors)
	}()

	go func() {
		defer wg.Done()
		s.downloadPhotos(tweet, errors)
	}()

	wg.Wait()
}

func (s *TwitterScrapeService) downloadVideos(tweet *twitterscraper.Tweet, errors chan<- error) {
	var wg sync.WaitGroup
	for _, video := range tweet.Videos {
		wg.Add(1)
		go func(v twitterscraper.Video) {
			defer wg.Done()
			url := strings.Split(v.URL, "?")[0]
			err := s.download(tweet, url, "video")
			if err != nil {
				errors <- err
			}
		}(video)
	}
	wg.Wait()
}

func (s *TwitterScrapeService) downloadPhotos(tweet *twitterscraper.Tweet, errors chan<- error) {
	var wg sync.WaitGroup

	for _, photo := range tweet.Photos {
		if !strings.Contains(photo.URL, "video_thumb/") {
			wg.Add(1)
			go func(p twitterscraper.Photo) {
				defer wg.Done()
				url := p.URL + "?name=orig"
				err := s.download(tweet, url, "img")
				if err != nil {
					errors <- err
				}
			}(photo)
		}
	}
	wg.Wait()
}

func (s *TwitterScrapeService) download(tweet *twitterscraper.Tweet, url, fileType string) error {
	name := s.FormatFileName(tweet)

	s.logger.Info("Downloading Tweet", "url", url)

	resp, err := s.makeRequest(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	filePath, err := s.determineFilePath(s.config.OutputDir, fileType, name)
	if err != nil {
		return err
	}

	if err := s.saveFile(filePath, resp.Body); err != nil {
		return err
	}

	s.logger.Info("Download successful", "filepath", filePath)
	return nil
}

func (s *TwitterScrapeService) FormatFileName(tweet *twitterscraper.Tweet) string {
	dateStr := time.Unix(tweet.Timestamp, 0).Format("02-01-2006")
	return fmt.Sprintf("%s_%s_%s", tweet.Username, tweet.ID, dateStr)
}

func (s *TwitterScrapeService) makeRequest(url string) (*http.Response, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("error creating request: %w", err)
	}
	req.Header.Add("User-Agent", "Mozilla/5.0 (X11; Linux x86_64)")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error downloading: %w", err)
	}

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("error: status code %d", resp.StatusCode)
	}

	return resp, nil
}

func (s *TwitterScrapeService) determineFilePath(output, fileType, name string) (string, error) {
	var filePath string
	filePath = filepath.Join(output, fileType, name)
	if s.config.Update {
		if _, err := os.Stat(filePath); !os.IsNotExist(err) {
			return "", fmt.Errorf("%s: already exists", name)
		}
	}
	if fileType == "rtimg" || fileType == "rtvideo" {
		filePath = filepath.Join(output, strings.TrimPrefix(fileType, "rt"), "RE-"+name)
	}
	return filePath, nil
}

func (s *TwitterScrapeService) saveFile(filePath string, content io.Reader) error {
	if err := os.MkdirAll(filepath.Dir(filePath), os.ModePerm); err != nil {
		return fmt.Errorf("error creating directory: %w", err)
	}

	f, err := os.Create(filePath)
	if err != nil {
		return fmt.Errorf("error creating file: %w", err)
	}
	defer f.Close()

	if _, err = io.Copy(f, content); err != nil {
		return fmt.Errorf("error writing file: %w", err)
	}

	return nil
}
