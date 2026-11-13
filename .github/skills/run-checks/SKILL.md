---
name: run-checks
description: "Use to verify changes in this repo: run backend pytest against PostgreSQL and the frontend TypeScript check/build, and diagnose common failures (missing test database, connection failure, tzdata)."
---

# Run checks

1. Backend (from `backend/`): `python -m pytest`. Single test: `python -m pytest tests/test_api.py::test_auth_flow`.
   - Needs `TEST_DATABASE_URL` in `backend/.env` pointing to a dedicated PostgreSQL database. The test fixture drops and recreates its tables; never point it at production.
   - `No time zone found` means `tzdata` is missing: `pip install -r requirements.txt`.
2. Frontend (from `frontend/`): `npx tsc --noEmit`, then `npm run build`.
3. Record anything that could not be run in `.github/PROGRESS.md` under "Open items".
