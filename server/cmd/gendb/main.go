package main

import (
	"errors"
	"fmt"
	"os"
	"teledeck/internal/config"
	database "teledeck/internal/service/store/db"

	"gorm.io/gen"
)

func main() {
	if err := runMain(); err != nil {
		fmt.Println("Error running main:", err)
		os.Exit(1)
	}
}

func runMain() error {
	g := gen.NewGenerator(gen.Config{
		OutPath: "../data/query",
		Mode:    gen.WithoutContext | gen.WithDefaultQuery | gen.WithQueryInterface, // generate mode
	})

	cfg, cfgErr := config.LoadConfig()
	gormdb, dbErr := database.Open(cfg.DatabasePath())
	if err := errors.Join(cfgErr, dbErr); err != nil {
		return fmt.Errorf("failed to load config or open database: %w", err)
	}

	g.UseDB(gormdb)

	g.ApplyBasic(
		g.GenerateAllTable()...,
	)
	g.Execute()
	return nil
}
