

.PHONY: tailwind-dl
tailwind-dl:
	curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
	mv tailwindcss-linux-x64 tailwindcss
	chmod +x tailwindcss

.PHONY: tailwind-watch
tailwind-watch:
	./tailwindcss -i ./static/css/input.css -o ./static/css/style.css --watch

.PHONY: tailwind-build
tailwind-build:
	./tailwindcss -i ./assets/css/input.css -o ./assets/css/style.css
	./tailwindcss -i ./assets/css/input.css -o ./assets/css/style.min.css --minify

.PHONY: templ
templ:
	go tool templ generate

.PHONY: templ-watch
templ-watch:
	go tool templ generate --watch

APP_NAME = teledeck
.PHONY: dev
dev:
	go tool air --build.cmd "go build -o ./tmp/$(APP_NAME) cmd/$(APP_NAME)/main.go" --build.bin "./tmp/$(APP_NAME)"

.PHONY:fmt
fmt:
	go fmt ./...

.PHONY: vet
vet: fmt
	go vet ./...

.PHONY:lint
lint: fmt
	golint ./...

.PHONY: staticcheck
staticcheck:
	staticcheck ./...

.PHONY: build
build: vet tailwind-build templ
	go build -ldflags "-X main.Environment=production" -o ./bin/$(APP_NAME) ./cmd/$(APP_NAME)/main.go


.PHONY: test
test:
	  go test -race -v -timeout 30s ./...

.PHONY: gendb
	go run ./cmd/gendb/main.go
