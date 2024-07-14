package store
import "time"

type MediaItem struct {
    ID       int       `json:"id"`
    Date     time.Time `json:"date"`
    Channel  string    `json:"channel"`
    Text     string    `json:"text"`
    Type     string    `json:"type"`
    Path     string    `json:"path"`
    FileID   string    `json:"file_id"`
    FileName string    `json:"file_name"`
    FileSize int64     `json:"file_size"`
    URL      string    `json:"url,omitempty"`
}