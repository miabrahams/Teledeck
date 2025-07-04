package db

import (
	// "teledeck/internal/store"
	"log"
	"os"
	"time"

	"gorm.io/driver/sqlite" // Sqlite driver based on CGO
	"gorm.io/gorm/logger"

	"gorm.io/gorm"
)

func Open(dbName string) (*gorm.DB, error) {

	// make the temp directory if it doesn't exist
	// TODO: What is this for
	err := os.MkdirAll("/tmp", 0755)
	if err != nil {
		return nil, err
	}

	/* TODO - move logger config up */
	newLogger := logger.New(
		log.New(os.Stdout, "\r\n", log.LstdFlags), // io writer
		logger.Config{
			SlowThreshold:             time.Second, // Slow SQL threshold
			LogLevel:                  logger.Warn, // Log level
			IgnoreRecordNotFoundError: true,        // Ignore ErrRecordNotFound error for logger
			ParameterizedQueries:      true,        // Don't include params in the SQL log
			Colorful:                  false,       // Disable color
		},
	)

	return gorm.Open(sqlite.Open(dbName), &gorm.Config{
		Logger: newLogger,
	})
}
