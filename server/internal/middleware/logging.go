package middleware

import (
	"context"
	"log/slog"
	"net/http"
)

type contextKey string

const loggerKey contextKey = "logger"

func WithLogger(logger *slog.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx := context.WithValue(r.Context(), loggerKey, logger)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func GetLogger(ctx context.Context) *slog.Logger {
	if logger, ok := ctx.Value(loggerKey).(*slog.Logger); ok {
		return logger
	}
	return slog.Default()
}
