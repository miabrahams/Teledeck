package db

import (
	// "goth/internal/store"
	"log"
	"os"
	"time"

	"gorm.io/driver/sqlite" // Sqlite driver based on CGO
	"gorm.io/gorm/logger"

	// "github.com/glebarez/sqlite" // Pure go SQLite driver, checkout https://github.com/glebarez/sqlite for details

	"gorm.io/gorm"
)

func open(dbName string) (*gorm.DB, error) {

	// make the temp directory if it doesn't exist
	err := os.MkdirAll("/tmp", 0755)
	if err != nil {
		return nil, err
	}

	/* TODO - logging config */
	newLogger := logger.New(
		log.New(os.Stdout, "\r\n", log.LstdFlags), // io writer
		logger.Config{
			SlowThreshold:             time.Second, // Slow SQL threshold
			LogLevel:                  logger.Info, // Log level
			IgnoreRecordNotFoundError: true,        // Ignore ErrRecordNotFound error for logger
			ParameterizedQueries:      true,        // Don't include params in the SQL log
			Colorful:                  false,       // Disable color
		},
	)

	return gorm.Open(sqlite.Open(dbName), &gorm.Config{
		Logger: newLogger,
	})
}

func MustOpen(dbName string) *gorm.DB {

	if dbName == "" {
		dbName = "../teledeck.db"
	}

	db, err := open(dbName)
	if err != nil {
		panic(err)
	}

	// err = db.AutoMigrate(&store.User{}, &store.Session{}, &store.MediaItem{})

	if err != nil {
		panic(err)
	}

	return db
}
