package config

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"

	"github.com/knadh/koanf/parsers/yaml"
	"github.com/knadh/koanf/providers/file"
	"github.com/knadh/koanf/v2"
)

const (
	defaultConfigFile = "default.yaml"
	localConfigFile   = "local.yaml"
	configDirEnvVar   = "TELEDECK_CONFIG_DIR"
	configFileEnvVar  = "TELEDECK_CONFIG_FILE"
)

type Config struct {
	App      AppConfig      `koanf:"app"`
	Paths    PathsConfig    `koanf:"paths"`
	Storage  StorageConfig  `koanf:"storage"`
	Telegram TelegramConfig `koanf:"telegram"`
	Backoff  BackoffConfig  `koanf:"backoff"`
	Queue    QueueConfig    `koanf:"queue"`
	Fetch    FetchConfig    `koanf:"fetch"`
	Twitter  TwitterConfig  `koanf:"twitter"`
	Tagging  TaggingConfig  `koanf:"tagging"`
}

type AppConfig struct {
	Env               string `koanf:"env"`
	HTTPPort          int    `koanf:"http_port"`
	SessionCookieName string `koanf:"session_cookie_name"`
}

type PathsConfig struct {
	DBPath       string `koanf:"db_path"`
	StaticRoot   string `koanf:"static_root"`
	MediaRoot    string `koanf:"media_root"`
	OrphanRoot   string `koanf:"orphan_root"`
	RecycleRoot  string `koanf:"recycle_root"`
	StaticAssets string `koanf:"static_assets"`
	UpdateState  string `koanf:"update_state"`
	ExportRoot   string `koanf:"export_root"`
}

type StorageConfig struct {
	MaxFileSizeBytes int64 `koanf:"max_file_size_bytes"`
}

type TelegramConfig struct {
	APIID       int    `koanf:"api_id"`
	APIHash     string `koanf:"api_hash"`
	Phone       string `koanf:"phone"`
	DBKey       string `koanf:"db_key"`
	SessionFile string `koanf:"session_file"`
}

type BackoffConfig struct {
	MaxAttempts        int        `koanf:"max_attempts"`
	BaseDelaySeconds   float64    `koanf:"base_delay_seconds"`
	SlowMode           bool       `koanf:"slow_mode"`
	SlowModeDelayRange DelayRange `koanf:"slow_mode_delay_seconds"`
}

type DelayRange struct {
	Min float64 `koanf:"min"`
	Max float64 `koanf:"max"`
}

type QueueConfig struct {
	MaxConcurrentTasks int `koanf:"max_concurrent_tasks"`
}

type FetchConfig struct {
	DefaultLimit      int    `koanf:"default_limit"`
	Strategy          string `koanf:"strategy"`
	WriteMessageLinks bool   `koanf:"write_message_links"`
}

type TwitterConfig struct {
	AuthToken string `koanf:"auth_token"`
	CSRFToken string `koanf:"csrf_token"`
}

type TaggingConfig struct {
	GRPCHost      string  `koanf:"grpc_host"`
	GRPCPort      int     `koanf:"grpc_port"`
	DefaultCutoff float64 `koanf:"default_cutoff"`
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

// LoadConfig loads configuration from YAML files using koanf.
func LoadConfig() (*Config, error) {
	k := koanf.New(".")

	files, err := resolveConfigFiles()
	if err != nil {
		return nil, err
	}

	for _, path := range files {
		if err := k.Load(file.Provider(path), yaml.Parser()); err != nil {
			return nil, fmt.Errorf("load config %s: %w", path, err)
		}
	}

	var cfg Config
	if err := k.Unmarshal("", &cfg); err != nil {
		return nil, fmt.Errorf("unmarshal config: %w", err)
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
		os.Getenv("TELEDECK_CONFIG_DIR"),
		filepath.Join(cwd, "config"),
		filepath.Join(filepath.Dir(cwd), "config"),
		filepath.Join(filepath.Dir(filepath.Dir(cwd)), "config"),
		os.Getenv("HOME") + "/.config/teledeck",
	}
	for _, dir := range candidates {
		if len(dir) == 0 {
			continue
		}
		if info, err := os.Stat(dir); err == nil && info.IsDir() {
			return dir, nil
		}
	}
	return "", errors.New("config directory not found; set TELEDECK_CONFIG_DIR")
}
