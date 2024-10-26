package htmxhandlers

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"teledeck/internal/middleware"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestGlobalHandler(t *testing.T) {

	/* Tests GetAbout */
	testCases := []struct {
		name               string
		expectedStatusCode int
		expectedBody       []byte
	}{
		{
			name:               "render successfully",
			expectedStatusCode: http.StatusOK,
			expectedBody:       []byte("My website"),
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {

			assert := assert.New(t)

			handler := NewGlobalHandler()

			req, err := http.NewRequest("GET", "/about", nil)
			assert.NoError(err)

			value := middleware.Nonces{
				Htmx:            "nonce-1234",
				ResponseTargets: "nonce-5678",
				Tw:              "nonce-9101",
				HtmxCSSHash:     "sha256-pgn1TCGZX6O77zDvy0oTODMOxemn0oj0LeCnQTRj7Kg=",
			}
			ctx := context.WithValue(req.Context(), middleware.NonceKey, value)
			req = req.WithContext(ctx)

			rr := httptest.NewRecorder()

			handler.GetAbout(rr, req)

			assert.Equal(tc.expectedStatusCode, rr.Code, "handler returned wrong status code: got %v want %v", rr.Code, tc.expectedStatusCode)

			assert.True(bytes.Contains(rr.Body.Bytes(), tc.expectedBody), "handler returned unexpected body: got %v want %v", rr.Body.String(), tc.expectedBody)

		})

	}

}
