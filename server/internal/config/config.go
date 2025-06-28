// Package config defines the configuration struct for Teledeck
package config

import (
	"path/filepath"

	"github.com/kelseyhightower/envconfig"
)

// TODO: Try Koanf

type Config struct {
	Environment       string `envconfig:"ENV" default:"development"`
	Port              string `envconfig:"PORT" default:":4000"`
	DatabaseName      string `envconfig:"DATABASE_NAME" default:"../teledeck.db"`
	SessionCookieName string `envconfig:"SESSION_COOKIE_NAME" default:"session"`
	HtmxAssetDir      string `envconfig:"STATIC_DIR" default:"./assets"`
	StaticMediaDir    string `envconfig:"MEDIA_DIR" default:"../static"`
	RecycleDir        string `envconfig:"RECYCLE_DIR" default:"../recyclebin"`
	TelegramAPIID     string `envconfig:"TG_API_ID" default:""`
	TelegramAPIHash   string `envconfig:"TG_API_HASH" default:""`
	TaggerURL         string `envconfig:"TAGGER_URL" default:""`
	TagServicePort    string `envconfig:"TAGGER_PORT" default:"8081"`
}

func (cfg *Config) MediaDir(workDir string) string {
	return filepath.Join(workDir, cfg.StaticMediaDir, "media")
}

func (cfg *Config) ThumbnailDir(workDir string) string {
	return filepath.Join(workDir, cfg.StaticMediaDir, "thumbnails")
}

func loadConfig() (*Config, error) {
	var cfg Config
	err := envconfig.Process("", &cfg)
	if err != nil {
		return nil, err
	}
	return &cfg, nil
}

func MustLoadConfig() *Config {
	cfg, err := loadConfig()
	if err != nil {
		panic(err)
	}
	return cfg
}
