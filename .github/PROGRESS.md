# Progress log

Read this before starting work. Update it at the end of every session: move finished items to "Done", add anything left unfinished to "Open items", and add dated notes to "Log". Never put passwords or API keys here.

## Decisions (from the owner)
- Database is PostgreSQL, using Supabase in production. Local/test PostgreSQL databases are separate; `TEST_DATABASE_URL` must never point at production.
- Deployment target is Vercel for the frontend, Render for FastAPI, and Supabase PostgreSQL for persistence.
- Render's free tier is acceptable for now despite its limitations; upgrade to the $7 plan when cost is no longer a concern.
- Local development may use `AUTH_REQUIRED=false` for one default user. For the hosted app, the owner chose to enable login with `AUTH_REQUIRED=true` on Render and `NEXT_PUBLIC_AUTH_REQUIRED=true` on Vercel. The owner's TikTok credentials are configured only in hosting secrets.
- **Posting**: TikTok drafts can't be read via API, so the owner chose **direct post via file upload** (stored in `backend/uploads/`, sent with TikTok's `FILE_UPLOAD` flow). Option 1 = upload a file, then post now or schedule at best time. Option 2 = recurring daily/weekly schedule, to be built later.
- **Best time** targets the overall audience (viewers, mostly non-followers), not the follower base, and reads the age group from the **most recent post's analytics** (`audience_for` in `backend/app/main.py`, `tiktok.fetch_audience`), falling back to the profile's `audience_age` (labelled as a fallback in Settings; DB column name unchanged).
- Repetitive tasks get agent skills under `.github/skills/`.

## Done
- FastAPI backend + Next.js frontend, mock mode when no TikTok/Gemini credentials.
- Switched the backend database driver/configuration to PostgreSQL with psycopg, and added a dedicated PostgreSQL `TEST_DATABASE_URL` requirement. Supabase connection was verified; integration tests against PostgreSQL remain pending.
- Created Supabase PostgreSQL `public.users`, `public.videos`, and `public.posts` from `backend/app/models.py`. Enabled RLS without public policies and revoked `PUBLIC`, `anon`, and `authenticated` table and ID-sequence privileges; backend owner access and table columns verified.
- Single-user mode (login bypass) in `backend/app/security.py`, `frontend/components/Shell.tsx`, `frontend/lib/api.ts`.
- Repo instructions in `.github/copilot-instructions.md`; Playwright MCP in `.vscode/mcp.json`.
- TikTok compliance with https://developers.tiktok.com/docs/en/ : creator info queried before every post (`GET /api/tiktok/creator-info`); user-chosen privacy validated against it (no default); comment/duet/stitch toggles (off by default, greyed when the creator disabled them); commercial-content disclosure + consent declaration in `frontend/components/PostPanel.tsx`; init/chunk/PUT per the media-transfer guide; status polling (`GET /api/videos/{id}/publish-status`, stores the public post id when available); documented error codes mapped to clear messages and shown on the video (`fail_reason`); OAuth `state` is a signed 10-minute token; access tokens refresh automatically and the rotated refresh token is stored; no watermarks/branding are added to videos.

## Open items (left behind)
- [x] ~~Frontend verification~~ — `npx tsc --noEmit` and `npm run build` previously passed; frontend source was not changed in this database/deployment update.
- [ ] **User action required**: Set the Supabase PostgreSQL URL as `DATABASE_URL` in Render; create a separate local PostgreSQL DB and set `TEST_DATABASE_URL` before running backend tests.
- [ ] **Verification pending**: Run all backend tests against PostgreSQL/Supabase. Previous 15-test pass was against MySQL and does not verify this database switch.
- [ ] **Security follow-up**: Startup's `Base.metadata.create_all` does not apply the Supabase RLS and privilege restrictions created in this session. Add a repeatable migration/provisioning mechanism before creating these tables in another project or recreating them; do not run destructive tests against production.
- [ ] **User action required**: Fill `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` in Render after creating the TikTok app; set `TIKTOK_REDIRECT_URI` and `FRONTEND_ORIGIN` to the Vercel domain.
- [ ] **User action required**: Deploy frontend to Vercel and backend to Render using the updated guides.
- [ ] **Future upgrade**: When moving to a paid Render instance, attach a persistent disk at `/var/data` and set `UPLOAD_DIR=/var/data/uploads`; keep one backend instance for the in-process scheduler.
- [ ] **Free-tier limitation**: Scheduled posts may be delayed while Render sleeps; uploaded videos are lost on spin-down, restart, or redeploy, so scheduled posts can fail even though their Supabase records remain.
- [ ] **User action required**: Set `AUTH_REQUIRED=true` in Render and `NEXT_PUBLIC_AUTH_REQUIRED=true` in Vercel, then register/sign in before hosted testing.
- [ ] **Decision pending**: Existing MySQL records are not automatically copied to Supabase; confirm whether any existing local videos/users need export/import.
- [ ] **User action required**: Create TikTok app and register redirect URI in developer portal (see `TIKTOK_REGISTRATION.md`).
- [ ] **Untested against real TikTok**: the Direct Post flow (creator info → init → chunked upload → status) in `backend/app/tiktok.py` is only unit-tested with a mocked HTTP layer. Try one real post with a short clip once credentials are set and deployed. Until the TikTok app passes TikTok's audit, TikTok only allows private posts (`SELF_ONLY`, account must be private).
- [ ] **TikTok app review pending**: Submit app for review to allow public posting (currently limited to private/SELF_ONLY in dev mode).
- [ ] Not enforced yet: `max_video_post_duration_sec` (needs reading the video duration, e.g. ffprobe) and a preview of the video file in the Post panel (currently shows title/caption only). Both are in TikTok's content sharing guidelines.
- [ ] Optional: handle TikTok webhooks (`post.publish.complete` etc.) instead of manual "Refresh" polling; apply for TikTok's audit to lift private-only posting.
- [ ] Uploaded files are kept after posting (deleted only when the video is deleted); decide whether to purge after posting. Render disk must be persistent and backed up if uploads matter.
- [ ] `video_url` still exists on videos (API/DB) as a fallback; the UI no longer exposes it. Remove it if you never want URL posting.
- [ ] Real audience data: `tiktok.fetch_audience` returns `{}` for real posts (TikTok Display/Content Posting APIs have no demographics), so only mock mode uses the latest-post audience. To enable it for real, apply for TikTok Business/Accounts API access and implement the real call there.
- [ ] Build recurring daily/weekly scheduling (option 2 for posting).
- [ ] No migration tool: `ensure_columns` in `backend/app/db.py` only adds a fixed list of columns (videos: file_path, publish_options, publish_status, fail_reason; users: TikTok refresh token/expiry). Add Alembic before making other model changes (`create_all` never alters existing PostgreSQL tables).
- [ ] Instagram / YouTube Shorts are "coming soon" only.
- [x] ~~Deployment guides~~ — updated the main Vercel + Render + Supabase instructions in `.github/QUICK_START.md`, `.github/DEPLOYMENT_GUIDE.md`, `.github/DEPLOYMENT_CHECKLIST.md`, and `.github/ENV_TEMPLATES.md`.

## Log
- 2026-11-03: MySQL switch, SQLite removal, single-user mode, audience wording, skills and this log added.
- 2026-11-03: TikTok docs audit; Direct Post brought in line with the docs (see Done). 15 backend tests pass; frontend type check and build pass.
- 2026-11-13: Pre-deployment readiness check complete. Created `QUICK_START.md`, `DEPLOYMENT_GUIDE.md`, and `TIKTOK_REGISTRATION.md`. All tests passing (15 backend, frontend build successful). Ready for Vercel + TikTok registration.
- 2026-11-13: Owner decision: “I'll use render to host the fast api backend. I'm switching from mysql to supabase”. Updated backend configuration/dependencies and primary deployment docs for PostgreSQL, Render, and Supabase; PostgreSQL test execution and deployment remain pending.
- 2026-11-13: Added psycopg URL normalization/rejection tests (4 passed), compiled backend sources and PostgreSQL model DDL, and updated deployment/security notes. Full backend integration tests remain blocked until `backend/.env` and a dedicated `TEST_DATABASE_URL` point to PostgreSQL.
- 2026-11-13: Owner chose “Enable login on Render and Vercel (recommended for a public URL)”. Hosted deployment guides now enable auth; the application already contains the login/register flow.
- 2026-11-13: Supabase connection established over TLS; created app tables transactionally, enabled RLS and revoked public roles' table/sequence privileges. Verified model columns, backend reads, role privileges, and absence of public policies; no destructive test suite run. Supabase skills were installed under `.agents/skills/`, a valid project skill location.
- 2026-11-13: Compared hosting options: Render's paid web service and persistent disk fit the current in-process scheduler and file uploads; Vercel FastAPI support would require scheduler and storage changes. Free Render sleeps and lacks persistent disks.
- 2026-11-13: Owner accepts the free Render tier's limitations for now and plans to upgrade to the $7 plan later. Updated deployment guidance for the free tier and future persistent disk.
