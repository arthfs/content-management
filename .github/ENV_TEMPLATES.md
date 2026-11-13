# Environment Variable Templates

Set production values in Render and Vercel dashboards. Never commit credentials or production `.env` files.

## Render backend

Configure the Render Web Service with `backend/` as its root directory:

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Choose the Free instance for initial testing. The default local `uploads` directory is ephemeral; omit `UPLOAD_DIR`.

Set these Render environment variables:

```env
SECRET_KEY=<strong-random-secret>
DATABASE_URL=<Supabase-PostgreSQL-connection-URL>
FRONTEND_ORIGIN=https://<your-vercel-domain>.vercel.app
AUTH_REQUIRED=true
DEFAULT_USER_EMAIL=me@local
TIKTOK_CLIENT_KEY=<from-tiktok-developer-portal>
TIKTOK_CLIENT_SECRET=<from-tiktok-developer-portal>
TIKTOK_REDIRECT_URI=https://<your-vercel-domain>.vercel.app/settings
GEMINI_API_KEY=<optional>
GEMINI_MODEL=gemini-1.5-flash
```

Copy the database URL from **Supabase → Project Settings → Database**. Use the session pooler if Render cannot connect to the direct endpoint. The app accepts either a `postgresql://` URL or `postgresql+psycopg://`. URL-encode reserved characters in the database username/password. Do not configure `TEST_DATABASE_URL` on the production Render service.

Free Render services sleep and lose uploaded files on spin-down, restart, and deploy. Scheduling may be delayed or fail when files disappear. When upgrading to a paid instance, add a persistent disk mounted at `/var/data` and set `UPLOAD_DIR=/var/data/uploads`; disk costs extra.

Authentication is enabled for the hosted test app. Keep `AUTH_REQUIRED=true` on Render and `NEXT_PUBLIC_AUTH_REQUIRED=true` on Vercel; create an account through the app to test it.

## Vercel frontend

In Vercel **Settings → Environment Variables**, set:

```env
NEXT_PUBLIC_API_URL=https://<your-render-service>.onrender.com
NEXT_PUBLIC_AUTH_REQUIRED=true
```

Redeploy the frontend after changing environment variables.

## Local development

`backend/.env`:

```env
SECRET_KEY=dev-secret-key-not-production
DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5432/content_manager
TEST_DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5432/content_manager_test
FRONTEND_ORIGIN=http://localhost:3000
AUTH_REQUIRED=false
DEFAULT_USER_EMAIL=me@local
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
TIKTOK_REDIRECT_URI=http://localhost:3000/settings
GEMINI_API_KEY=
```

Create the two local PostgreSQL databases before running tests. Tests drop and recreate tables in `TEST_DATABASE_URL`; never point it at the production Supabase database.

`frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AUTH_REQUIRED=false
```

## Generate a secret

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Security checklist

- Use a unique random `SECRET_KEY` in Render.
- Keep the Supabase database password and TikTok client secret only in hosting-provider secrets.
- Never commit `.env` files.
- Use HTTPS for deployed frontend, backend, and TikTok redirect URI.
- Never log a full database connection string or print all application settings.
