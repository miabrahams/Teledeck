# Repository Guidelines

## Project Structure & Module Organization
- `server/` hosts the Go backend (`cmd/teledeck`, domain logic in `internal/`, Tailwind assets in `assets/`).
- `web/` contains the Vite + React client; edit `web/src/`, bundle output lands in `web/dist/` for embedding in the Go service.
- `AI/` holds Python tooling for tagging and scoring; place downloaded weights under `AI/models/`.
- `admin/` exposes Telegram database and media collection commands.
- persistent SQLite data lives in `data/` with exports in `export/`.
- Shared settings live under `config/default.yaml`; override secrets in `config/local.yaml` (ignored by git) so both Go and Python read the same YAML tree. Database change files are tracked in `alembic/`.

## Build, Test, and Development Commands
- `make server` starts the Go dev server with Air live reload.
- `make web` installs dependencies and builds the frontend bundle.
- `make build` runs Tailwind + templ generation and produces a production binary.
- `python tagger/server.py` launches the tagging microservice once models exist.
- `python admin/admin.py --client-update` refreshes cached Telegram data prior to ingest jobs.

## Coding Style & Naming Conventions
- Run `cd server && make fmt` before committing; follow with `make vet`, `make lint`, or `make staticcheck` as needed. Go code stays gofmt-formatted with PascalCase types and camelCase identifiers.
- Frontend TypeScript follows `web/eslint.config.js`; keep React components in PascalCase files, prefer function components, and use camelCase for hooks and stores.
- Regenerate templ files via `make templ` or `make templ-watch`; avoid editing generated assets in `server/internal/service/web/`.

## Testing Guidelines
- Execute backend tests with `cd server && make test` (race-enabled) and add `_test.go` files alongside target packages.
- Run `npx playwright test` from `playwright/` for end-to-end coverage; group specs by feature directory.
- No frontend unit harness exists yet; cover complex UI logic with Playwright expectations or add targeted Vitest suites before merging.

## Commit & Pull Request Guidelines
- Match the existing history (`Fix config`, `More type tweaks`): short, imperative commit subjects under ~50 characters.
- Pull requests should state scope, manual verification, linked issues, and include UI screenshots when visuals change. Flag any config or migration updates for reviewers.

## Configuration & Environment
- Keep `config/default.yaml` committed as the base template and copy `config/local.example.yaml` to `config/local.yaml` for per-machine overrides; environment variables like `APP__HTTP_PORT` or the legacy `PORT` still work for quick tweaks.
- Apply migrations with `make alembic-upgrade`; refresh `alembic/schema.sql` via `make dump-schema` after schema edits.
- Back up the SQLite store with `make backup-db`; snapshots are written to `data/db_backup/` before risky operations.
