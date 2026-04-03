# CLAUDE.md

## Project Overview

FastAPI Issue Tracker — a REST API for tracking issues, built with FastAPI and Pydantic. Uses JSON file-based storage (no database). All endpoints are under `/api/v1/`.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fastapi dev main.py
```

Server runs at `http://localhost:8000`. Docs at `/docs` (Swagger) and `/redoc`.

## Project Structure

```
main.py                    # FastAPI app entry point, middleware setup, health endpoint
app/
  schemas.py               # Pydantic models (IssueCreate, IssueUpdate, IssueOut, enums)
  storage.py               # JSON file persistence (load_data/save_data -> data/issues.json)
  middleware/
    timing.py              # Adds X-Process-Time header to responses
  routes/
    issues.py              # CRUD endpoints for issues (GET, POST, PUT, DELETE)
docs/                      # Tutorial materials (crash_course.md, diagram)
.github/workflows/
  django.yml               # CI workflow (note: misconfigured — runs `python manage.py test`)
```

## Architecture

- **Entry point**: `main.py` creates the FastAPI app, registers CORS + timing middleware, mounts the issues router
- **Routing**: Single router in `app/routes/issues.py` with prefix `/api/v1/issues`
- **Data models**: Pydantic v2 schemas in `app/schemas.py` with validation constraints
- **Storage**: Flat-file JSON storage in `data/issues.json` (directory auto-created, gitignored)
- **No database, no ORM, no migrations** — all state is in the JSON file

## API Endpoints

| Method | Path                    | Description        |
|--------|-------------------------|--------------------|
| GET    | `/api/v1/health`        | Health check       |
| GET    | `/api/v1/issues`        | List all issues    |
| GET    | `/api/v1/issues/{id}`   | Get issue by ID    |
| POST   | `/api/v1/issues`        | Create issue       |
| PUT    | `/api/v1/issues/{id}`   | Update issue       |
| DELETE | `/api/v1/issues/{id}`   | Delete issue       |

## Key Data Models

- **IssuePriority**: `low`, `medium`, `high`
- **IssueStatus**: `open`, `in_progress`, `closed`
- **IssueCreate**: `title` (3-100 chars), `description` (5-2000 chars), `priority` (default: medium)
- **IssueUpdate**: All fields optional (partial update via PUT)
- Issue IDs are UUID4 strings generated server-side

## Development Conventions

- **Python version**: 3.9+ (uses `list[T]` syntax for type hints)
- **Framework**: FastAPI 0.128.0 with Pydantic v2
- **No tests exist** — the CI workflow references Django's test runner which doesn't apply
- **No `.env` usage currently** but `python-dotenv` is in requirements and `.env` is gitignored
- Routes use `APIRouter` with prefix and tags
- HTTP exceptions use `fastapi.status` constants
- Storage functions are synchronous (no async file I/O)
- Middleware is applied via `app.middleware("http")` decorator pattern

## Things to Watch Out For

- The CI workflow (`.github/workflows/django.yml`) is a Django template — it runs `python manage.py test` which will fail. This needs to be updated if CI matters.
- Storage is not concurrency-safe (no file locking). Fine for development, not for production.
- CORS is fully open (`allow_origins=["*"]`).
- The `data/` directory is gitignored, so test data won't persist across clones.
