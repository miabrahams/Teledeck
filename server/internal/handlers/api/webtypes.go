package webapi

import (
	"encoding/json"
	"net/http"
)

type APIError struct {
	Message string `json:"message"`
}

func writeJSON[T any](w http.ResponseWriter, status int, v T) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, APIError{Message: message})
}
