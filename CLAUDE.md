# CLAUDE.md

## Project Overview

FastAPI Issue Tracker — a REST API for tracking issues, built with FastAPI and Pydantic. Uses JSON file-based storage (no database). All endpoints are under `/api/v1/`. Originally from a [FastAPI Crash Course](https://youtu.be/8TMQcRcBnW8) by Brad Traversy.

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
requirements.txt           # Pinned dependencies (pip freeze output)
app/
  __init__.py              # Empty package init
  schemas.py               # Pydantic models (IssueCreate, IssueUpdate, IssueOut, enums)
  storage.py               # JSON file persistence (load_data/save_data -> data/issues.json)
  middleware/
    timing.py              # Adds X-Process-Time header to responses
  routes/
    __init__.py            # Empty package init
    issues.py              # CRUD endpoints for issues (GET, POST, PUT, DELETE)
data/                      # Auto-created, gitignored — runtime JSON storage
docs/
  crash_course.md          # Written FastAPI tutorial
  crash_course_excalidraw.png  # Architecture diagram from video
.github/workflows/
  django.yml               # CI workflow (BROKEN — see "Things to Watch Out For")
```

## Architecture

- **Entry point**: `main.py` creates the FastAPI app, registers timing middleware via `app.middleware("http")`, then CORS middleware via `app.add_middleware()`, and mounts the issues router
- **Routing**: Single router in `app/routes/issues.py` with prefix `/api/v1/issues` and tag `Issues`. Health check is defined directly in `main.py` at `/api/v1/health`
- **Data models**: Pydantic v2 schemas in `app/schemas.py` with validation constraints
- **Storage**: Flat-file JSON in `data/issues.json` — `load_data()` returns `list[dict]`, `save_data()` writes with `indent=2`. Directory auto-created on first write
- **No database, no ORM, no migrations** — all state is in the JSON file
- **No async I/O** — route handlers and storage are all synchronous (FastAPI runs them in a threadpool)

## API Endpoints

| Method | Path                    | Description        | Status Code |
|--------|-------------------------|--------------------|-------------|
| GET    | `/api/v1/health`        | Health check       | 200         |
| GET    | `/api/v1/issues`        | List all issues    | 200         |
| GET    | `/api/v1/issues/{id}`   | Get issue by ID    | 200 / 404   |
| POST   | `/api/v1/issues`        | Create issue       | 201         |
| PUT    | `/api/v1/issues/{id}`   | Update issue       | 200 / 404   |
| DELETE | `/api/v1/issues/{id}`   | Delete issue       | 204 / 404   |

## Key Data Models

- **IssuePriority** (str enum): `low`, `medium`, `high`
- **IssueStatus** (str enum): `open`, `in_progress`, `closed`
- **IssueCreate**: `title` (min 3, max 100 chars), `description` (min 5, max 2000 chars), `priority` (default: `medium`)
- **IssueUpdate**: All fields optional for partial update — `title` (max 100, no min_length), `description` (min 5, max 2000), `priority`, `status`
- **IssueOut**: `id`, `title`, `description`, `priority`, `status` — used as `response_model` on all read/write endpoints
- Issue IDs are UUID4 strings generated server-side via `uuid.uuid4()`
- New issues always start with `status: "open"`

## Dependencies

Key packages from `requirements.txt` (pinned versions):

- **fastapi** 0.128.0 (with **starlette** 0.49.3)
- **pydantic** 2.12.5 (pydantic_core 2.41.5)
- **uvicorn** 0.39.0 (with uvloop, httptools, watchfiles for dev reload)
- **python-dotenv** 1.2.1 (installed but not currently used)
- **sentry-sdk** 2.48.0 (installed but not configured in the app)
- **httpx** 0.28.1 (available for testing if needed)

## Development Conventions

- **Python version**: 3.9+ required (uses `list[T]` type hint syntax from PEP 585)
- **No tests exist** — the CI workflow references Django's test runner which doesn't apply
- **No linter/formatter configured** — no pyproject.toml, setup.cfg, or ruff/black/flake8 config
- Routes use `APIRouter` with `prefix` and `tags` parameters
- HTTP exceptions use `fastapi.status` constants (e.g., `status.HTTP_404_NOT_FOUND`)
- Storage functions are synchronous — `load_data()` / `save_data()` do plain `open()` / `json.load()` / `json.dump()`
- Middleware is applied via `app.middleware("http")` decorator pattern for timing, `app.add_middleware()` for CORS
- Route handlers use sync `def` (not `async def`), so FastAPI runs them in a threadpool automatically
- The `data/` directory is in `.gitignore` along with `.venv`, `__pycache__`, `*.pyc`, and `.env`

## Things to Watch Out For

- **CI is broken**: `.github/workflows/django.yml` is a Django template that runs `python manage.py test` — this will always fail. It also tests against Python 3.7/3.8/3.9, but the codebase requires 3.9+ (due to `list[T]` syntax). Needs a full rewrite if CI matters.
- **No concurrency safety**: Storage has no file locking. Concurrent writes will cause data loss. Fine for single-user development.
- **CORS is fully open**: `allow_origins=["*"]` with `allow_credentials=True` — this combination is insecure for production.
- **No input sanitization beyond Pydantic**: Title and description are stored as-is after Pydantic validates length.
- **IssueUpdate.title has no min_length**: Unlike `IssueCreate.title` (min 3 chars), `IssueUpdate.title` only has `max_length=100`, allowing single-character titles via update.
- **Sentry SDK is installed but unconfigured**: `sentry-sdk` is in requirements but never imported or initialized.
- **python-dotenv is installed but unused**: No `.env` loading is set up in the application.

## Common Tasks

**Run the dev server:**
```bash
fastapi dev main.py
```

**Test an endpoint manually:**
```bash
# Create an issue
curl -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{"title": "Test issue", "description": "Testing the API endpoint", "priority": "high"}'

# List all issues
curl http://localhost:8000/api/v1/issues
```

**Reset all data:**
```bash
rm -f data/issues.json
```
