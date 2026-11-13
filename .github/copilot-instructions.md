# Copilot Instructions

## Build and test

Run commands from the relevant project directory:

- Backend setup: `pip install -r requirements.txt`
- Backend tests: `python -m pytest`
- One backend test: `python -m pytest tests/test_api.py::test_auth_flow` (replace the test name to target another test in `tests/test_api.py`)
- Backend development server: `uvicorn app.main:app --reload`
- Frontend setup: `npm install`
- Frontend development server: `npm run dev`
- Frontend production build: `npm run build`
- Frontend type check: `npx tsc --noEmit`
- Serve a production build: `npm start`

The backend tests use `TestClient` and a dedicated PostgreSQL database configured by `TEST_DATABASE_URL`; tests drop and recreate its tables, so never point it at production. The frontend scripts are defined in `frontend/package.json`.

## Architecture

- `backend/app/main.py` is the FastAPI composition layer: it defines `/api` endpoints, wires authentication and persistence, creates tables at startup, and starts a lifespan task that checks for scheduled posts once per minute.
- `backend/app/models.py` defines the SQLAlchemy `User` → `Video` → `Post` ownership and persistence model. `schemas.py` defines Pydantic request/response validation; `db.py` provides the shared engine, session factory, and request-scoped sessions.
- `publisher.py` publishes scheduled or immediate videos through `tiktok.py`. TikTok calls and metrics fall back to deterministic mock behavior when credentials or a user connection are absent. `insights.py` uses Gemini when configured and otherwise returns rule-based suggestions.
- `besttime.py` computes posting slots in each user's timezone; scheduled timestamps are stored/handled as UTC. User profile preferences drive the suggested local hours.
- `frontend/` is a Next.js App Router application. Pages call the FastAPI service through `frontend/lib/api.ts`, whose base URL is `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`). The shared client stores the bearer token in `localStorage`, adds it to API requests, and redirects to sign-in on expired authorization.
- See [README.md](../README.md) for product behavior, environment variables, and external TikTok setup details.

## Key conventions

- Authenticated API handlers obtain the current user through `current_user`. Video lookup must remain user-scoped: use `get_video` in `main.py`, which returns 404 for missing or another user's video.
- Keep HTTP request/response shapes in `schemas.py`; use `model_dump(exclude_none=True)` for partial profile/video updates so omitted fields are not overwritten.
- Video lifecycle statuses are `draft`, `scheduled`, `posted`, and `failed`. Publishing and analytics should go through `publisher.py` and `tiktok.py` so mock and configured integrations behave consistently.
- Best-time calculations use timezone-aware datetimes, returning UTC slots for persistence/API use and converting to the profile's timezone for display.
- Frontend API calls and shared client types belong in `frontend/lib/api.ts`; pages use the shared `Shell` for authenticated navigation.
- The database is PostgreSQL (Supabase in production). Tests require a separate PostgreSQL database via `TEST_DATABASE_URL`; never use production data.
- Login is off by default: with `AUTH_REQUIRED=false`, `current_user` returns one local default user. Keep the login/register code working behind `AUTH_REQUIRED=true` / `NEXT_PUBLIC_AUTH_REQUIRED=true`.
- Best-time logic targets the overall audience (mostly non-followers) using the latest post's audience analytics via `audience_for`, falling back to the profile age group.

## Project memory

Read [.github/PROGRESS.md](PROGRESS.md) at the start of a session (owner decisions, open items) and update it at the end. Repeatable workflows live in `.github/skills/` (`add-api-endpoint`, `run-checks`, `update-progress-log`); add a new skill when a task repeats.
