package dbstore

import (
	"encoding/json"
	"io"
	database "teledeck/internal/service/store/db"
	"testing"

	"log/slog"

	"gorm.io/gorm"
)

// Todo: Create test database
func getDB() (*gorm.DB, error) {

	db := database.MustOpen("~/apps/TG-Collector/teledeck.db")

	return db, nil
}

func getMediaStore(db *gorm.DB) *MediaStore {
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	mediaStore := NewMediaStore(db, logger)
	return mediaStore
}

func TestGetMediaItem(t *testing.T) {
	db, err := getDB()
	if err != nil {
		t.Fatalf("Failed to setup test database: %v", err)
	}

	testID := "test_id_1"

	// Test 1: Raw SQL query
	t.Run("RawSQLQuery", func(t *testing.T) {
		var result map[string]interface{}
		err := db.Raw(`
			SELECT media_items.*, telegram_metadata.*, media_types.type as media_type, channels.title as channel_title
			FROM media_items
			LEFT JOIN media_types ON media_items.media_type_id = media_types.id
			LEFT JOIN telegram_metadata ON media_items.id = telegram_metadata.media_item_id
			LEFT JOIN channels ON telegram_metadata.channel_id = channels.id
		`, testID).First(&result).Error

		if err != nil {
			t.Errorf("Raw SQL query failed: %v", err)
		}

		jsonResult, _ := json.MarshalIndent(result, "", "  ")
		t.Logf("Raw SQL result: %s", jsonResult)
	})

	// Test 2: GORM query
	mediaStore := getMediaStore(db)
	t.Run("GORMQuery", func(t *testing.T) {
		item, err := mediaStore.GetMediaItem("4513841A4D98410C432535401A07B22A")
		if err != nil {
			t.Errorf("GORM query failed: %v", err)
		}

		jsonResult, _ := json.MarshalIndent(item, "", "  ")
		t.Logf("GORM query result: %s", jsonResult)
	})
}

/*
func TestGetPaginatedMediaItems(t *testing.T) {
	db, err := getDB()
	if err != nil {
		t.Fatalf("Failed to setup test database: %v", err)
	}

	mediaStore := getMediaStore(db)

	// Test 1: Raw SQL query
	t.Run("RawSQLQuery", func(t *testing.T) {
		var results []map[string]interface{}
		err := db.Raw(`
			SELECT media_items.*, sources.name as source_name,
			telegram_metadata.channel_id, telegram_metadata.message_id,
			channels.title as channel_title
			FROM media_items
			LEFT JOIN sources ON media_items.source_id = sources.id
			LEFT JOIN telegram_metadata ON media_items.id = telegram_metadata.media_item_id
			LEFT JOIN channels ON telegram_metadata.channel_id = channels.id
			WHERE media_items.user_deleted = false
			LIMIT 10
		`).Scan(&results).Error

		if err != nil {
			t.Errorf("Raw SQL query failed: %v", err)
		}

		jsonResult, _ := json.MarshalIndent(results, "", "  ")
		t.Logf("Raw SQL result: %s", jsonResult)
	})

	// Test 2: GORM query
	t.Run("GORMQuery", func(t *testing.T) {
		items, err := mediaStore.GetPaginatedMediaItems(1, 10, store.SearchPrefs{})
		if err != nil {
			t.Errorf("GORM query failed: %v", err)
		}

		jsonResult, _ := json.MarshalIndent(items, "", "  ")
		t.Logf("GORM query result: %s", jsonResult)
	})
}

func TestApplySearchFilters(t *testing.T) {
	db, err := getDB()
	if err != nil {
		t.Fatalf("Failed to setup test database: %v", err)
	}

	// Test different search preferences
	testCases := []struct {
		name  string
		prefs store.SearchPrefs
	}{
		{"VideosOnly", store.SearchPrefs{VideosOnly: true}},
		{"SearchText", store.SearchPrefs{Search: "test"}},
		{"Favorites", store.SearchPrefs{Favorites: "favorites"}},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			query := db.Model(&store.MediaItem{})
			query = applySearchFilters(tc.prefs, query)

			// Get the generated SQL
			sql := query.ToSQL(func(tx *gorm.DB) *gorm.DB {
				return tx.Model(&store.MediaItem{})
			})

			t.Logf("Generated SQL for %s: %s", tc.name, sql)

			// Execute the query and log results
			var results []map[string]interface{}
			err := query.Find(&results).Error
			if err != nil {
				t.Errorf("Query execution failed: %v", err)
			}

			jsonResult, _ := json.MarshalIndent(results, "", "  ")
			t.Logf("Query results: %s", jsonResult)
		})
	}
}

*/
