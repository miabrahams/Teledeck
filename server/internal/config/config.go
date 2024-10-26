package config

import (
	"path/filepath"

	"github.com/kelseyhightower/envconfig"
)

type Config struct {
	Port              string `envconfig:"PORT" default:":4000"`
	DatabaseName      string `envconfig:"DATABASE_NAME" default:"../teledeck.db"`
	SessionCookieName string `envconfig:"SESSION_COOKIE_NAME" default:"session"`
	StaticDir         string `envconfig:"STATIC_DIR" default:"./static"`
	StaticMediaDir    string `envconfig:"MEDIA_DIR" default:"../static"`
	RecycleDir        string `envconfig:"RECYCLE_DIR" default:"../recyclebin"`
	Telegram_API_ID   string `envconfig:"TG_API_ID" default:""`
	Telegram_API_Hash string `envconfig:"TG_API_HASH" default:""`
	TaggerURL         string `envconfig:"TAGGER_URL" default:""`
	TagServicePort    string `envconfig:"TAGGER_PORT" default:"8081"`
}

func (cfg *Config) MediaDir(workDir string) string {
	return filepath.Join(workDir, cfg.StaticMediaDir, "media") // Adjust this path as needed
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
