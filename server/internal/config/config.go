package config

import "github.com/kelseyhightower/envconfig"

type Config struct {
	Port              string `envconfig:"PORT" default:":4000"`
	DatabaseName      string `envconfig:"DATABASE_NAME" default:"../teledeck.db"`
	SessionCookieName string `envconfig:"SESSION_COOKIE_NAME" default:"session"`
	StaticDir         string `envconfig:"MEDIA_DIR" default:"./static"`
	StaticMediaDir    string `envconfig:"MEDIA_DIR" default:"../static"`
	RecycleDir        string `envconfig:"RECYCLE_DIR" default:"../recyclebin"`
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
