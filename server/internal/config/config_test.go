package config

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/require"
	"gopkg.in/yaml.v3"
)

func TestAccessors(t *testing.T) {
	require := require.New(t)

	c := Config{
		App:     AppConfig{HTTPPort: 8081, SessionCookieName: "sess", Env: "dev"},
		Paths:   PathsConfig{DBPath: "db.sqlite", StaticRoot: "/srv/static", MediaRoot: "/srv/media", RecycleRoot: "/srv/recycle", StaticAssets: "/srv/assets"},
		Tagging: TaggingConfig{GRPCHost: "localhost", GRPCPort: 50051, DefaultCutoff: 0.5},
	}

	require.Equal(":8081", c.HTTPAddress())
	require.Equal("localhost:50051", c.GRPCAddress())
	require.Equal("8081", c.PortString())
	require.Equal("db.sqlite", c.DatabasePath())
	require.Equal("/srv/assets", c.HtmxAssetDir())
	require.Equal("/srv/media", c.MediaDir())
	require.Equal("/srv/static/thumbnails", c.ThumbnailDir())
	require.Equal("/srv/static", c.StaticMediaDir())
	require.Equal("/srv/recycle", c.RecycleDir())
}

func TestLoadConfig_DefaultAndLocalMergeAndEnvOverrides(t *testing.T) {
	require := require.New(t)

	// Create a temp dir to act as config dir
	dir := t.TempDir()

	// default.yaml
	defaultCfg := map[string]any{
		"app":     map[string]any{"http_port": 9000, "env": "prod"},
		"paths":   map[string]any{"db_path": "default.db", "static_assets": "/default/assets"},
		"tagging": map[string]any{"grpc_host": "tagger", "grpc_port": 1234, "default_cutoff": 0.7},
	}
	defPath := filepath.Join(dir, "default.yaml")
	f, err := os.Create(defPath)
	require.NoError(err)
	enc := yaml.NewEncoder(f)
	require.NoError(enc.Encode(defaultCfg))
	require.NoError(f.Close())

	// local.yaml overrides
	localCfg := map[string]any{
		"app":   map[string]any{"http_port": 9010},
		"paths": map[string]any{"db_path": "local.db"},
	}
	locPath := filepath.Join(dir, "local.yaml")
	f2, err := os.Create(locPath)
	require.NoError(err)
	enc2 := yaml.NewEncoder(f2)
	require.NoError(enc2.Encode(localCfg))
	require.NoError(f2.Close())

	// Point loader to this dir
	require.NoError(os.Setenv(configDirEnvVar, dir))
	defer os.Unsetenv(configDirEnvVar)

	cfg, err := LoadConfig()
	require.NoError(err)

	// Expect merged values: port from local, db_path from local, tagger from default
	require.Equal(9010, cfg.App.HTTPPort)
	require.Equal("local.db", cfg.Paths.DBPath)
	require.Equal("tagger", cfg.Tagging.GRPCHost)
	require.Equal(1234, cfg.Tagging.GRPCPort)

	// Now test env override for TAGGING__GRPC_PORT and APP__HTTP_PORT
	require.NoError(os.Setenv("TAGGING__GRPC_PORT", "4321"))
	require.NoError(os.Setenv("APP__HTTP_PORT", "3333"))
	defer os.Unsetenv("TAGGING__GRPC_PORT")
	defer os.Unsetenv("APP__HTTP_PORT")

	cfg2, err := LoadConfig()
	require.NoError(err)
	require.Equal(4321, cfg2.Tagging.GRPCPort)
	require.Equal(3333, cfg2.App.HTTPPort)
}
