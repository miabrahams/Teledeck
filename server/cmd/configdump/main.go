package main

import (
	"fmt"
	"os"

	"teledeck/internal/config"

	"gopkg.in/yaml.v3"
)

func main() {
	cfg, err := config.LoadConfig()
	if err != nil {
		fmt.Fprintf(os.Stderr, "load config: %v\n", err)
		os.Exit(1)
	}
	enc := yaml.NewEncoder(os.Stdout)
	enc.SetIndent(2)
	if err := enc.Encode(cfg); err != nil {
		fmt.Fprintf(os.Stderr, "encode yaml: %v\n", err)
		os.Exit(1)
	}
}
