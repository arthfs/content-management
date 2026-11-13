---
name: add-api-endpoint
description: "Use when adding or changing a backend API endpoint, Pydantic schema, or model field, and the matching frontend client call, in this FastAPI + Next.js repo."
---

# Add an API endpoint

1. **Schema**: add request/response models to `backend/app/schemas.py`. Partial updates use optional fields and `model_dump(exclude_none=True)`.
2. **Model** (only if data changes): edit `backend/app/models.py`. `create_all` does not alter existing PostgreSQL tables, so tell the user a migration or manual `ALTER TABLE` is needed and log it in `.github/PROGRESS.md`.
3. **Handler**: add it to `backend/app/main.py` under `/api`, with `user: User = Depends(current_user)` and `db: Session = Depends(get_db)`. Look videos up only with `get_video` (user-scoped 404). Publishing/analytics go through `publisher.py` / `tiktok.py`.
4. **Test**: add a case to `backend/tests/test_api.py` using the `client` fixture (dedicated PostgreSQL database from `TEST_DATABASE_URL`, `AUTH_REQUIRED` forced on, so use `auth(client)` headers). Run `cd backend && python -m pytest tests/test_api.py::<test_name>`, then the full suite.
5. **Frontend**: put types and helpers in `frontend/lib/api.ts`; pages call `api<T>()`. Check with `cd frontend && npx tsc --noEmit`.
6. Update `.github/PROGRESS.md` if anything is left unfinished.
