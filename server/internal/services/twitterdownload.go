package services

import (
	"context"
	"log/slog"
	"net"
	"net/http"
	"os"
	"time"

	twitterscraper "github.com/imperatrona/twitter-scraper"
)

type TwitterScraper struct {
	runner *twitterscraper.Scraper
	client *http.Client
	logger *slog.Logger
}

func NewTwitterScraper() *TwitterScraper {
	scraper := twitterscraper.New()
	scraper.SetAuthToken(twitterscraper.AuthToken{Token: os.Getenv("TWITTER_AUTHTOKEN"), CSRFToken: os.Getenv("TWITTER_CRSFTOKEN")})

	// After setting Cookies or AuthToken you have to execute IsLoggedIn method.
	// Without it, scraper wouldn't be able to make requests that requires authentication
	if !scraper.IsLoggedIn() {
		panic("Invalid AuthToken")
	}

	client := &http.Client{
		Transport: &http.Transport{
			DialContext: (&net.Dialer{
				Timeout: time.Duration(5) * time.Second,
			}).DialContext,
			TLSHandshakeTimeout:   time.Duration(5) * time.Second,
			ResponseHeaderTimeout: 5 * time.Second,
			DisableKeepAlives:     true,
		},
	}

	return &TwitterScraper{runner: scraper, client: client}
}

func (s *TwitterScraper) ScrapeUser(user string) []string {
	results := []string{}
	for tweet := range s.runner.GetTweets(context.Background(), user, 10) {
		if tweet.Error != nil {
			panic(tweet.Error)
		}
		s.logger.Info(tweet.Text)
		results = append(results, tweet.Text)
	}
	return results
}
