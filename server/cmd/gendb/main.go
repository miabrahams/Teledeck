package main

import (
	"teledeck/internal/config"
	database "teledeck/internal/service/store/db"

	"gorm.io/gen"
)

func main() {
	g := gen.NewGenerator(gen.Config{
		OutPath: "../data/query",
		Mode:    gen.WithoutContext | gen.WithDefaultQuery | gen.WithQueryInterface, // generate mode
	})

	cfg := config.MustLoadConfig()
	gormdb := database.MustOpen(cfg.DatabaseName)

	g.UseDB(gormdb)

	g.ApplyBasic(
		g.GenerateAllTable()...,
	)
	g.Execute()
}
