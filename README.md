# Content Manager

Web app to manage short-form content: keep drafts, post twice a day at the best times, see a dashboard, and view per-video analytics with AI suggestions.

- `backend/` – FastAPI (auth, drafts, scheduling, TikTok publishing, analytics, Gemini suggestions)
- `frontend/` – Next.js + TypeScript (sign in/up, dashboard, videos, video analytics, settings)

MVP supports **TikTok only**. Instagram and YouTube Shorts are shown as "coming soon" on the dashboard.
Without credentials the app runs in **mock mode** (fake publishing/metrics, rule-based suggestions), so it works out of the box.

## Run

```bash
cd backend && pip install -r requirements.txt && cp .env.example .env
uvicorn app.main:app --reload            # http://localhost:8000/docs

cd frontend && npm install && cp .env.example .env.local
npm run dev                              # http://localhost:3000
```

Tests: `cd backend && python -m pytest`

## Use PostgreSQL (Supabase)

The backend uses PostgreSQL, including Supabase Postgres. Create a Supabase project and set its PostgreSQL connection string as `DATABASE_URL` in the Render environment. The app accepts standard `postgresql://` URLs (including Supabase pooler URLs) and `postgresql+psycopg://`; credentials containing reserved URL characters must be percent-encoded. Keep the database password private and do not commit it.

For local development, create separate `content_manager` and `content_manager_test` databases in a local PostgreSQL server. Set `DATABASE_URL` and `TEST_DATABASE_URL` in `backend/.env`; tests drop and recreate tables in the dedicated test database, so never point `TEST_DATABASE_URL` at production. Existing records in a MySQL database are not transferred automatically; export/import them separately if you need to preserve them.

On Render, attach a persistent disk mounted at `/var/data` and set `UPLOAD_DIR=/var/data/uploads`. Uploaded videos are needed for scheduled posts and Render's default filesystem is ephemeral. Keep the service to one instance because the in-process scheduler is not coordinated across multiple instances.

## Login
Login is off by default (`AUTH_REQUIRED=false`): every request acts as one local user (`DEFAULT_USER_EMAIL`), and the TikTok connection is stored on that user. Set `AUTH_REQUIRED=true` in `backend/.env` and `NEXT_PUBLIC_AUTH_REQUIRED=true` in `frontend/.env.local` to bring back sign-in/sign-up.

**Security warning:** Do not expose a deployment with `AUTH_REQUIRED=false` to the public internet. Anyone who can reach the app shares the same user and may access its content or use its connected TikTok account. Enable login on both backend and frontend before making the deployment public.

## Posting
Choose a video file from your computer (Videos page → **Video file**, or **Attach video** on an existing draft), then **Post to TikTok now** or **Schedule at best time**. The file is stored in `backend/uploads/` (git-ignored; mp4/mov/webm, up to `MAX_UPLOAD_MB`, default 500) and sent to TikTok with the Content Posting API's direct `FILE_UPLOAD` flow, so no public URL is needed. TikTok's own in-app drafts can't be read through the API, which is why upload is used instead. Until your TikTok app passes TikTok's audit, TikTok only allows private posts; the **Post to TikTok** panel asks you for the account's privacy level (options come from TikTok's creator info, nothing is pre-selected), interactions, commercial-content disclosure and consent, as TikTok's content sharing guidelines require. After posting, use **Refresh** to see TikTok's processing status. In mock mode no file is required. Recurring (daily/weekly) schedules are planned, not built yet. Project status and open items live in [.github/PROGRESS.md](.github/PROGRESS.md).

## How best times work
Per user (Settings): timezone, country, fallback audience age group and posts/day (default 2). The age group targeted is taken from the audience breakdown of your **most recent post's analytics** (viewers, not only followers); if none is available it falls back to the Settings value. Peak local hours are chosen per age group; "Schedule at best time" picks the next free slot. A background task publishes due videos every minute. Note: TikTok's public APIs don't return audience demographics, so real posts currently fall back to Settings and only mock mode produces a breakdown (see `tiktok.fetch_audience`).

## Credentials needed (set in `backend/.env`)
| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Long random string for signing login tokens (required in production) |
| `GEMINI_API_KEY` | Google AI Studio key for improvement suggestions (optional `GEMINI_MODEL`) |
| `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` | From TikTok for Developers app with Login Kit + Content Posting API (scopes `user.info.basic`, `video.publish`, `video.list`) |
| `TIKTOK_REDIRECT_URI` | Must match the redirect URI registered in the TikTok app (default `http://localhost:3000/settings`) |
| `DATABASE_URL` | PostgreSQL/Supabase connection URL (see "Use PostgreSQL") |
| `AUTH_REQUIRED`, `DEFAULT_USER_EMAIL` | Optional; login is off by default (single local user) |

Notes: TikTok's Content Posting API requires app review/audit for public posting. TikTok's API doesn't expose watch-time/completion metrics; those appear only in mock mode.
