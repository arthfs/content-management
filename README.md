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

## How best times work
Per user (Settings): timezone, country, main follower age group and posts/day (default 2). Peak local hours are chosen per age group; "Schedule at best time" picks the next free slot. A background task publishes due videos every minute.

## Credentials needed (set in `backend/.env`)
| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Long random string for signing login tokens (required in production) |
| `GEMINI_API_KEY` | Google AI Studio key for improvement suggestions (optional `GEMINI_MODEL`) |
| `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` | From TikTok for Developers app with Login Kit + Content Posting API (scopes `user.info.basic`, `video.publish`, `video.list`) |
| `TIKTOK_REDIRECT_URI` | Must match the redirect URI registered in the TikTok app (default `http://localhost:3000/settings`) |
| `DATABASE_URL` | Optional; defaults to local SQLite |

Notes: TikTok's Content Posting API requires app review/audit for public posting, and pulls videos from a verified public URL (`video_url`). TikTok's API doesn't expose watch-time/completion metrics; those appear only in mock mode.
