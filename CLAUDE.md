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

## Full-Stack Development Patterns

### Database Schema Changes
When modifying the database schema, changes must be made in multiple places:

1. **Go Models**: Update structs in `server/internal/models/dbmodels.go` with GORM tags
2. **Python Models**: Update SQLModel classes in `admin/models/telegram.py` 
3. **Database Migration**: Create Alembic migration in `alembic/versions/` using `alembic revision -m "description"`
4. **Migration Content**: Include both `upgrade()` and `downgrade()` functions with proper SQL operations

### API Development Pattern
Full-stack API changes follow this flow:

1. **Database Layer**: Add methods to store interfaces (`server/internal/service/store/store.go`) and implementations (`server/internal/service/store/dbstore/`)
2. **Controller Layer**: Add business logic methods in `server/internal/controllers/`
3. **Handler Layer**: Add HTTP endpoints in `server/internal/handlers/api/` 
4. **Router Registration**: Add routes in `server/cmd/teledeck/main.go` under the `/api` group
5. **Frontend API**: Add request functions in `web/src/shared/api/requests.ts`
6. **React Integration**: Add mutation/query hooks in feature-specific API files (e.g., `web/src/features/media/api.ts`)

### File Operations
The file operations system uses an interface pattern:
- **Interface**: `server/internal/service/files/fileoperator.go` defines operations
- **Implementation**: `server/internal/service/files/localfile/` contains actual file system operations
- **Usage**: Controllers use the interface, allowing for easy testing and alternative implementations

### State Management (Frontend)
- **TanStack Query**: Used for server state management and caching
- **Jotai**: Used for client-side state (preferences, UI state)
- **Optimistic Updates**: Mutations often include optimistic updates for better UX

### Error Handling Patterns
- **Go**: Custom error types (e.g., `ErrFavorite{}`) for business logic errors
- **API**: Consistent JSON error responses via `writeError()` helper
- **Frontend**: Error boundaries and mutation error handling via TanStack Query

### Database Conventions
- **Soft Deletes**: Use `user_deleted` boolean + `deleted_at` timestamp for audit trails
- **Indexing**: Add indexes for frequently queried fields (especially filtering/sorting columns)
- **Foreign Keys**: Properly defined relationships between tables with cascade options where appropriate