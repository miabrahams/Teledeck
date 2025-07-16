# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Go Server (Primary Backend)
- `make dev` - Run development server with hot reload (uses Air)
- `make build` - Build production binary
- `make server` - Alias for `make dev`
- `cd server && make dev` - Run server directly from server directory
- `cd server && make test` - Run Go tests
- `cd server && make fmt` - Format Go code
- `cd server && make vet` - Run Go vet
- `cd server && make lint` - Run golint
- `cd server && make staticcheck` - Run staticcheck

### Frontend (React/TypeScript)
- `make web` - Build frontend for production and copy to server
- `make vite` - Run frontend in development mode with network sharing
- `cd web && npm run dev` - Run Vite development server
- `cd web && npm run build` - Build frontend for production
- `cd web && npm run lint` - Run ESLint

### Python Components
- `make update` - Update Telegram data using admin scripts
- `make tagger` - Start AI tagging server (requires AI models)
- `make deploy-classifier` - Deploy AI classifier service
- `make stop-classifier` - Stop AI classifier service

### Database & Schema
- `make backup-db` - Backup SQLite database to data/db_backup/
- `make dump-schema` - Export database schema to alembic/schema.sql
- `make xo` - Generate Go database code using XO

### Development Tools
- `cd server && make templ` - Generate Go templates
- `cd server && make templ-watch` - Watch and regenerate templates
- `cd server && make tailwind-build` - Build Tailwind CSS
- `cd server && make tailwind-watch` - Watch and rebuild Tailwind CSS

## Architecture Overview

### Multi-Language Stack
- **Go**: Primary backend server with HTMX frontend and REST API
- **Python**: Telegram data collection, AI services (tagging, aesthetic scoring)
- **React/TypeScript**: Modern frontend (optional, HTMX is primary)

### Key Components

#### Server (Go)
- **Framework**: Chi router with custom middleware
- **Database**: SQLite with GORM ORM
- **Templates**: Templ for Go HTML templates
- **Styling**: Tailwind CSS
- **Hot Reload**: Air for development

#### Data Collection (Python)
- **Telegram**: Telethon for Telegram API integration
- **Admin Scripts**: Located in `admin/` directory
- **Database**: SQLAlchemy with Alembic migrations

#### AI Services (Python)
- **Tagging**: CLIP-based image tagging via gRPC
- **Aesthetic Scoring**: EVA-2 model for image quality assessment
- **Requirements**: Separate requirements.txt in `AI/` directory

#### Frontend Options
- **HTMX**: Primary frontend with server-side rendering
- **React**: Modern SPA in `web/` directory using Vite, TanStack Router/Query

### Directory Structure
- `server/` - Go backend server
- `admin/` - Python admin scripts and data collection
- `AI/` - Python AI services (tagging, scoring)
- `web/` - React frontend (optional)
- `data/` - Database, backups, and generated files
- `static/` - Media files and thumbnails
- `alembic/` - Database migration files

### Database
- **Primary**: SQLite (`teledeck.db`)
- **Models**: Generated in `data/model/` and `data/query/`
- **Migrations**: Alembic for Python schema changes
- **Backups**: Automated to `data/db_backup/`

### Key Services
- **Media Management**: File operations, thumbnailing, duplicate detection
- **Telegram Integration**: Message/media fetching and processing
- **AI Processing**: Image tagging and aesthetic scoring via gRPC
- **User Management**: Authentication and session handling

### External Dependencies
- **Go**: Air (hot reload), Templ (templates), Tailwind CSS
- **Python**: Telethon (Telegram), CLIP (AI), FastAPI (AI services)
- **Node**: Vite (frontend), TanStack ecosystem (React)

## Development Workflow

1. **Backend Development**: Use `make dev` for Go server with hot reload
2. **Frontend Development**: Use `make vite` for React or work with HTMX templates
3. **Data Collection**: Use `make update` to fetch Telegram data
4. **AI Services**: Deploy with `make deploy-classifier` for tagging/scoring
5. **Database Changes**: Use Alembic for migrations, `make backup-db` before changes

## Testing

- **Go Tests**: `cd server && make test`
- **Python**: No centralized test runner specified
- **Frontend**: `cd web && npm run lint`
- **Integration**: Playwright tests in `playwright/` directory