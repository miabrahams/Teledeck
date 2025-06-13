package webapi

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"teledeck/internal/middleware"
	"teledeck/internal/models"
	"teledeck/internal/service/hash"
	"teledeck/internal/service/store"
)

type UserHandler struct {
	userStore         store.UserStore
	sessionStore      store.SessionStore
	passwordHash      hash.PasswordHash
	sessionCookieName string
}

func NewUserHandler(userStore store.UserStore, sessionStore store.SessionStore, passwordHash hash.PasswordHash, sessionCookieName string) *UserHandler {
	return &UserHandler{
		userStore:         userStore,
		sessionStore:      sessionStore,
		passwordHash:      passwordHash,
		sessionCookieName: sessionCookieName,
	}
}

func (h *UserHandler) GetCurrentUser(w http.ResponseWriter, r *http.Request) {
	user := middleware.GetUser(r.Context())
	if user == nil {
		writeError(w, http.StatusUnauthorized, "Not authenticated")
		return
	}

	// Only send necessary user data
	userData := struct {
		Email string `json:"email"`
	}{
		Email: user.Email,
	}

	writeJSON(w, http.StatusOK, userData)
}

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

func (h *UserHandler) Login(w http.ResponseWriter, r *http.Request) {
	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	user, err := h.userStore.GetUser(req.Email)
	if err != nil {
		writeError(w, http.StatusUnauthorized, "Invalid email or password")
		return
	}

	valid, err := h.passwordHash.ComparePasswordAndHash(req.Password, user.Password)
	if err != nil || !valid {
		writeError(w, http.StatusUnauthorized, "Invalid email or password")
		return
	}

	session, err := h.sessionStore.CreateSession(&models.Session{
		UserID: user.ID,
	})
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Error creating session")
		return
	}

	// Create session cookie
	cookieValue := base64.StdEncoding.EncodeToString([]byte(fmt.Sprintf("%s:%d", session.SessionID, user.ID)))
	http.SetCookie(w, &http.Cookie{
		Name:     h.sessionCookieName,
		Value:    cookieValue,
		Path:     "/",
		HttpOnly: true,
		Secure:   true,
		SameSite: http.SameSiteStrictMode,
	})

	// Return user data
	userData := struct {
		Email string `json:"email"`
	}{
		Email: user.Email,
	}

	writeJSON(w, http.StatusOK, userData)
}

type RegisterRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type RegisterHandler struct {
	userStore store.UserStore
}

func NewRegisterHandler(userStore store.UserStore) *RegisterHandler {
	return &RegisterHandler{userStore: userStore}
}

func (h *RegisterHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	var req RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	err := h.userStore.CreateUser(req.Email, req.Password)
	if err != nil {
		writeError(w, http.StatusBadRequest, "Error creating user")
		return
	}

	writeJSON(w, http.StatusCreated, struct{}{})
}

type LogoutHandler struct {
	sessionCookieName string
}

func NewLogoutHandler(sessionCookieName string) *LogoutHandler {
	return &LogoutHandler{sessionCookieName: sessionCookieName}
}

func (h *LogoutHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	http.SetCookie(w, &http.Cookie{
		Name:     h.sessionCookieName,
		Value:    "",
		Path:     "/",
		MaxAge:   -1,
		HttpOnly: true,
		Secure:   true,
		SameSite: http.SameSiteStrictMode,
	})

	w.WriteHeader(http.StatusNoContent)
}
