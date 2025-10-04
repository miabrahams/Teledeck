package config

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"gopkg.in/yaml.v3"
)

const (
	defaultConfigFile = "default.yaml"
	localConfigFile   = "local.yaml"
	configDirEnvVar   = "TELEDECK_CONFIG_DIR"
	configFileEnvVar  = "TELEDECK_CONFIG_FILE"
)

type Config struct {
	App      AppConfig      `yaml:"app"`
	Paths    PathsConfig    `yaml:"paths"`
	Storage  StorageConfig  `yaml:"storage"`
	Telegram TelegramConfig `yaml:"telegram"`
	Backoff  BackoffConfig  `yaml:"backoff"`
	Queue    QueueConfig    `yaml:"queue"`
	Fetch    FetchConfig    `yaml:"fetch"`
	Twitter  TwitterConfig  `yaml:"twitter"`
	Tagging  TaggingConfig  `yaml:"tagging"`
}

type AppConfig struct {
	Env               string `yaml:"env"`
	HTTPPort          int    `yaml:"http_port"`
	SessionCookieName string `yaml:"session_cookie_name"`
}

type PathsConfig struct {
	DBPath       string `yaml:"db_path"`
	StaticRoot   string `yaml:"static_root"`
	MediaRoot    string `yaml:"media_root"`
	OrphanRoot   string `yaml:"orphan_root"`
	RecycleRoot  string `yaml:"recycle_root"`
	StaticAssets string `yaml:"static_assets"`
	UpdateState  string `yaml:"update_state"`
	ExportRoot   string `yaml:"export_root"`
}

type StorageConfig struct {
	MaxFileSizeBytes int64 `yaml:"max_file_size_bytes"`
}

type TelegramConfig struct {
	APIID       int    `yaml:"api_id"`
	APIHash     string `yaml:"api_hash"`
	Phone       string `yaml:"phone"`
	DBKey       string `yaml:"db_key"`
	SessionFile string `yaml:"session_file"`
}

type BackoffConfig struct {
	MaxAttempts        int        `yaml:"max_attempts"`
	BaseDelaySeconds   float64    `yaml:"base_delay_seconds"`
	SlowMode           bool       `yaml:"slow_mode"`
	SlowModeDelayRange DelayRange `yaml:"slow_mode_delay_seconds"`
}

type DelayRange struct {
	Min float64 `yaml:"min"`
	Max float64 `yaml:"max"`
}

type QueueConfig struct {
	MaxConcurrentTasks int `yaml:"max_concurrent_tasks"`
}

type FetchConfig struct {
	DefaultLimit      int    `yaml:"default_limit"`
	Strategy          string `yaml:"strategy"`
	WriteMessageLinks bool   `yaml:"write_message_links"`
}

type TwitterConfig struct {
	AuthToken string `yaml:"auth_token"`
	CSRFToken string `yaml:"csrf_token"`
}

type TaggingConfig struct {
	GRPCHost      string  `yaml:"grpc_host"`
	GRPCPort      int     `yaml:"grpc_port"`
	DefaultCutoff float64 `yaml:"default_cutoff"`
}

func (c Config) HTTPAddress() string {
	return fmt.Sprintf(":%d", c.App.HTTPPort)
}

func (c Config) GRPCAddress() string {
	return fmt.Sprintf("%s:%d", c.Tagging.GRPCHost, c.Tagging.GRPCPort)
}

func (c Config) PortString() string {
	return strconv.Itoa(c.App.HTTPPort)
}

func (c Config) DatabasePath() string {
	return c.Paths.DBPath
}

func (c Config) HtmxAssetDir() string {
	return c.Paths.StaticAssets
}

func (c Config) MediaDir() string {
	if c.Paths.MediaRoot != "" {
		return c.Paths.MediaRoot
	}
	if c.Paths.StaticRoot != "" {
		return filepath.Join(c.Paths.StaticRoot, "media")
	}
	return ""
}

func (c Config) ThumbnailDir() string {
	if c.Paths.StaticRoot != "" {
		return filepath.Join(c.Paths.StaticRoot, "thumbnails")
	}
	if c.Paths.MediaRoot != "" {
		return filepath.Join(filepath.Dir(c.Paths.MediaRoot), "thumbnails")
	}
	return ""
}

// StaticMediaDir returns the base directory configured for media assets.
func (c Config) StaticMediaDir() string {
	if c.Paths.StaticRoot != "" {
		return c.Paths.StaticRoot
	}
	if c.Paths.MediaRoot != "" {
		return filepath.Dir(c.Paths.MediaRoot)
	}
	return ""
}

func (c Config) RecycleDir() string {
	return c.Paths.RecycleRoot
}

// LoadConfig loads configuration from YAML files and environment variables.
func LoadConfig() (*Config, error) {
	cfg := Config{}

	files, err := resolveConfigFiles()
	if err != nil {
		return nil, err
	}

	for _, path := range files {
		if err := loadYAML(path, &cfg); err != nil {
			return nil, err
		}
	}

	if err := applyEnvOverrides(&cfg); err != nil {
		return nil, err
	}

	return &cfg, nil
}

func resolveConfigFiles() ([]string, error) {
	if custom := os.Getenv(configFileEnvVar); custom != "" {
		if _, err := os.Stat(custom); err != nil {
			return nil, fmt.Errorf("config file %s: %w", custom, err)
		}
		return []string{custom}, nil
	}

	configDir := os.Getenv(configDirEnvVar)
	if configDir == "" {
		dir, err := findConfigDir()
		if err != nil {
			return nil, err
		}
		configDir = dir
	}

	files := []string{filepath.Join(configDir, defaultConfigFile)}
	local := filepath.Join(configDir, localConfigFile)
	if _, err := os.Stat(local); err == nil {
		files = append(files, local)
	}

	return files, nil
}

func findConfigDir() (string, error) {
	cwd, err := os.Getwd()
	if err != nil {
		return "", err
	}

	candidates := []string{
		filepath.Join(cwd, "config"),
		filepath.Join(filepath.Dir(cwd), "config"),
		filepath.Join(filepath.Dir(filepath.Dir(cwd)), "config"),
	}
	for _, dir := range candidates {
		if info, err := os.Stat(dir); err == nil && info.IsDir() {
			return dir, nil
		}
	}
	return "", errors.New("config directory not found; set TELEDECK_CONFIG_DIR")
}

func loadYAML(path string, out any) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("read config %s: %w", path, err)
	}
	decoder := yaml.NewDecoder(bytes.NewReader(data))
	decoder.KnownFields(true)
	if err := decoder.Decode(out); err != nil {
		return fmt.Errorf("parse config %s: %w", path, err)
	}
	return nil
}

func applyEnvOverrides(cfg *Config) error {
	if value, ok := os.LookupEnv("APP__HTTP_PORT"); ok {
		port, err := strconv.Atoi(value)
		if err != nil {
			return fmt.Errorf("APP__HTTP_PORT: %w", err)
		}
		cfg.App.HTTPPort = port
	}
	if value, ok := os.LookupEnv("APP__SESSION_COOKIE_NAME"); ok {
		cfg.App.SessionCookieName = value
	}
	if value, ok := os.LookupEnv("APP__ENV"); ok {
		cfg.App.Env = value
	}
	if value, ok := os.LookupEnv("PATHS__DB_PATH"); ok {
		cfg.Paths.DBPath = value
	}
	if value, ok := os.LookupEnv("PATHS__STATIC_ROOT"); ok {
		cfg.Paths.StaticRoot = value
	}
	if value, ok := os.LookupEnv("PATHS__MEDIA_ROOT"); ok {
		cfg.Paths.MediaRoot = value
	}
	if value, ok := os.LookupEnv("PATHS__RECYCLE_ROOT"); ok {
		cfg.Paths.RecycleRoot = value
	}
	if value, ok := os.LookupEnv("PATHS__STATIC_ASSETS"); ok {
		cfg.Paths.StaticAssets = value
	}
	if value, ok := os.LookupEnv("TAGGING__GRPC_HOST"); ok {
		cfg.Tagging.GRPCHost = value
	}
	if value, ok := os.LookupEnv("TAGGING__GRPC_PORT"); ok {
		port, err := strconv.Atoi(value)
		if err != nil {
			return fmt.Errorf("TAGGING__GRPC_PORT: %w", err)
		}
		cfg.Tagging.GRPCPort = port
	}
	if value, ok := os.LookupEnv("TAGGING__DEFAULT_CUTOFF"); ok {
		cutoff, err := strconv.ParseFloat(value, 64)
		if err != nil {
			return fmt.Errorf("TAGGING__DEFAULT_CUTOFF: %w", err)
		}
		cfg.Tagging.DefaultCutoff = cutoff
	}
	if value, ok := os.LookupEnv("TELEGRAM__API_ID"); ok {
		id, err := strconv.Atoi(value)
		if err != nil {
			return fmt.Errorf("TELEGRAM__API_ID: %w", err)
		}
		cfg.Telegram.APIID = id
	}
	if value, ok := os.LookupEnv("TELEGRAM__API_HASH"); ok {
		cfg.Telegram.APIHash = value
	}
	if value, ok := os.LookupEnv("TELEGRAM__PHONE"); ok {
		cfg.Telegram.Phone = value
	}
	if value, ok := os.LookupEnv("TELEGRAM__DB_KEY"); ok {
		cfg.Telegram.DBKey = value
	}
	if value, ok := os.LookupEnv("TELEGRAM__SESSION_FILE"); ok {
		cfg.Telegram.SessionFile = value
	}
	if value, ok := os.LookupEnv("TWITTER__AUTH_TOKEN"); ok {
		cfg.Twitter.AuthToken = value
	}
	if value, ok := os.LookupEnv("TWITTER__CSRF_TOKEN"); ok {
		cfg.Twitter.CSRFToken = value
	}
	if value, ok := os.LookupEnv("QUEUE__MAX_CONCURRENT_TASKS"); ok {
		max, err := strconv.Atoi(value)
		if err != nil {
			return fmt.Errorf("QUEUE__MAX_CONCURRENT_TASKS: %w", err)
		}
		cfg.Queue.MaxConcurrentTasks = max
	}
	if value, ok := os.LookupEnv("FETCH__DEFAULT_LIMIT"); ok {
		limit, err := strconv.Atoi(value)
		if err != nil {
			return fmt.Errorf("FETCH__DEFAULT_LIMIT: %w", err)
		}
		cfg.Fetch.DefaultLimit = limit
	}
	if value, ok := os.LookupEnv("FETCH__STRATEGY"); ok {
		cfg.Fetch.Strategy = value
	}
	if value, ok := os.LookupEnv("FETCH__WRITE_MESSAGE_LINKS"); ok {
		cfg.Fetch.WriteMessageLinks = parseBool(value, cfg.Fetch.WriteMessageLinks)
	}
	if value, ok := os.LookupEnv("STORAGE__MAX_FILE_SIZE_BYTES"); ok {
		size, err := strconv.ParseInt(value, 10, 64)
		if err != nil {
			return fmt.Errorf("STORAGE__MAX_FILE_SIZE_BYTES: %w", err)
		}
		cfg.Storage.MaxFileSizeBytes = size
	}
	if value, ok := os.LookupEnv("BACKOFF__MAX_ATTEMPTS"); ok {
		attempts, err := strconv.Atoi(value)
		if err != nil {
			return fmt.Errorf("BACKOFF__MAX_ATTEMPTS: %w", err)
		}
		cfg.Backoff.MaxAttempts = attempts
	}
	if value, ok := os.LookupEnv("BACKOFF__BASE_DELAY_SECONDS"); ok {
		seconds, err := strconv.ParseFloat(value, 64)
		if err != nil {
			return fmt.Errorf("BACKOFF__BASE_DELAY_SECONDS: %w", err)
		}
		cfg.Backoff.BaseDelaySeconds = seconds
	}
	if value, ok := os.LookupEnv("BACKOFF__SLOW_MODE"); ok {
		cfg.Backoff.SlowMode = parseBool(value, cfg.Backoff.SlowMode)
	}
	if value, ok := os.LookupEnv("BACKOFF__SLOW_MODE_DELAY_SECONDS__MIN"); ok {
		seconds, err := strconv.ParseFloat(value, 64)
		if err != nil {
			return fmt.Errorf("BACKOFF__SLOW_MODE_DELAY_SECONDS__MIN: %w", err)
		}
		cfg.Backoff.SlowModeDelayRange.Min = seconds
	}
	if value, ok := os.LookupEnv("BACKOFF__SLOW_MODE_DELAY_SECONDS__MAX"); ok {
		seconds, err := strconv.ParseFloat(value, 64)
		if err != nil {
			return fmt.Errorf("BACKOFF__SLOW_MODE_DELAY_SECONDS__MAX: %w", err)
		}
		cfg.Backoff.SlowModeDelayRange.Max = seconds
	}

	return nil
}

/*
func applyLegacyEnv(cfg *Config) error {
	legacy := map[string]func(string) error{
		"ENV": func(v string) error { cfg.App.Env = v; return nil },
		"PORT": func(v string) error {
			port, err := strconv.Atoi(v)
			if err != nil {
				return err
			}
			cfg.App.HTTPPort = port
			return nil
		},
		"SESSION_COOKIE_NAME": func(v string) error { cfg.App.SessionCookieName = v; return nil },
		"DATABASE_NAME":       func(v string) error { cfg.Paths.DBPath = v; return nil },
		"DB_PATH":             func(v string) error { cfg.Paths.DBPath = v; return nil },
		"STATIC_DIR":          func(v string) error { cfg.Paths.StaticAssets = v; return nil },
		"MEDIA_DIR":           func(v string) error { cfg.Paths.StaticRoot = v; return nil },
		"MEDIA_PATH":          func(v string) error { cfg.Paths.MediaRoot = v; return nil },
		"RECYCLE_DIR":         func(v string) error { cfg.Paths.RecycleRoot = v; return nil },
		"ORPHAN_PATH":         func(v string) error { cfg.Paths.OrphanRoot = v; return nil },
		"TAGGER_URL":          func(v string) error { cfg.Tagging.GRPCHost = v; return nil },
		"TAGGER_PORT": func(v string) error {
			port, err := strconv.Atoi(v)
			if err != nil {
				return err
			}
			cfg.Tagging.GRPCPort = port
			return nil
		},
		"TELEGRAM_API_ID": func(v string) error {
			id, err := strconv.Atoi(v)
			if err != nil {
				return err
			}
			cfg.Telegram.APIID = id
			return nil
		},
		"TELEGRAM_API_HASH": func(v string) error { cfg.Telegram.APIHash = v; return nil },
		"TELEGRAM_PHONE":    func(v string) error { cfg.Telegram.Phone = v; return nil },
		"TELEGRAM_DB_KEY":   func(v string) error { cfg.Telegram.DBKey = v; return nil },
		"SESSION_FILE":      func(v string) error { cfg.Telegram.SessionFile = v; return nil },
		"TWITTER_AUTHTOKEN": func(v string) error { cfg.Twitter.AuthToken = v; return nil },
		"TWITTER_CSRFTOKEN": func(v string) error { cfg.Twitter.CSRFToken = v; return nil },
	}

	for key, setter := range legacy {
		if value, ok := os.LookupEnv(key); ok {
			if err := setter(value); err != nil {
				return fmt.Errorf("legacy env %s: %w", key, err)
			}
		}
	}

	return nil
}
*/

func parseBool(value string, fallback bool) bool {
	switch strings.ToLower(strings.TrimSpace(value)) {
	case "true", "1", "yes", "on":
		return true
	case "false", "0", "no", "off":
		return false
	default:
		return fallback
	}
}
