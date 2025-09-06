// Package config defines the configuration struct for Teledeck
package config

import (
	"path/filepath"

	"github.com/kelseyhightower/envconfig"
)

// TODO: Try Koanf
// TODO: Refactor to have a base path

type Config struct {
	Environment       string `envconfig:"ENV" default:"development"`
	Port              string `envconfig:"PORT" default:"4000"` // TODO: int
	DatabaseName      string `envconfig:"DATABASE_NAME" default:"../teledeck.db"`
	SessionCookieName string `envconfig:"SESSION_COOKIE_NAME" default:"session"`
	HtmxAssetDir      string `envconfig:"STATIC_DIR" default:"./assets"`                 // rename
	StaticMediaDir    string `envconfig:"MEDIA_DIR" default:"/mnt/vhdx/teledeck/static"` // TODO: sync config with admin scripts
	RecycleDir        string `envconfig:"RECYCLE_DIR" default:"/mnt/vhdx/teledeck/recyclebin"`
	TelegramAPIID     string `envconfig:"TG_API_ID" default:""`
	TelegramAPIHash   string `envconfig:"TG_API_HASH" default:""`
	TaggerURL         string `envconfig:"TAGGER_URL" default:"localhost"`
	TagServicePort    string `envconfig:"TAGGER_PORT" default:"8081"`
}

func (cfg *Config) MediaDir() string {
	return filepath.Join(cfg.StaticMediaDir, "media")
}

func (cfg *Config) ThumbnailDir() string {
	return filepath.Join(cfg.StaticMediaDir, "thumbnails")
}

func LoadConfig() (*Config, error) {
	var cfg Config
	err := envconfig.Process("", &cfg)
	return &cfg, err
}
