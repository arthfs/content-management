# Deployment & TikTok Registration Guide

**Status**: Render/Supabase configuration updated; PostgreSQL integration still needs verification.  
**Last Updated**: 2026-11-13  
**Project**: Content Manager (Next.js + FastAPI)

---

## ✅ Pre-Deployment Checklist

### Project Status
- ⚠️ **Backend tests**: the prior 15-test pass used MySQL; rerun against PostgreSQL before deployment
- ✅ **Frontend type check**: passing (TypeScript 7.0.2)
- ✅ **Frontend production build**: complete and optimized
- ✅ **Database code**: PostgreSQL/Supabase driver configured; production connection still needs setup and verification
- ✅ **Login flow**: available; enable it for hosted testing with the settings below

### Quick Verification Checklist
- [ ] **Backend `.env`** (`backend/.env`):
  - [ ] `SECRET_KEY` is set to a secure random string (NOT "change-me")
  - [ ] `DATABASE_URL` is set to the Supabase PostgreSQL connection URL
  - [ ] `FRONTEND_ORIGIN` matches your Vercel frontend domain (e.g., `https://my-app.vercel.app`)
  - [ ] `TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET` are filled with your TikTok app credentials
  - [ ] `TIKTOK_REDIRECT_URI` is set to `https://<your-vercel-domain>/settings`
  - [ ] `GEMINI_API_KEY` is set (optional, for AI suggestions)

- [ ] **Frontend `.env.local`** (`frontend/.env.local`):
  - [ ] `NEXT_PUBLIC_API_URL` points to your Render service URL
  - [ ] `NEXT_PUBLIC_AUTH_REQUIRED=true`

- [ ] All environment variables are **NOT committed** to git (check `.gitignore`)

---

## 🚀 Part 1: Deploy Frontend to Vercel

### Step 1: Connect Repository to Vercel
1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository (`arthfs/content-management`)
4. Select your repository and click **"Import"**

### Step 2: Configure Environment Variables
In the Vercel dashboard, go to **Settings** → **Environment Variables** and add:

```
NEXT_PUBLIC_API_URL=https://<your-backend-url>
NEXT_PUBLIC_AUTH_REQUIRED=true
```

Replace `<your-backend-url>` with your backend service URL (see Part 2).

### Step 3: Configure Build Settings
- **Framework Preset**: Next.js (auto-detected)
- **Build Command**: `npm run build` (default)
- **Output Directory**: `.next` (default)
- **Root Directory**: `frontend/` (set this if not auto-detected)

### Step 4: Deploy
1. Click **"Deploy"**
2. Vercel will build and deploy your frontend
3. You'll get a URL like `https://content-management-XXX.vercel.app`
4. **Save this URL** — you'll need it for TikTok redirect URI

---

## 🚀 Part 2: Deploy Backend to Render

Vercel supports FastAPI as serverless functions, but this app's in-process scheduler and local video uploads require changes to work reliably there. Deploy the current backend as a Render Web Service:

1. Go to [render.com](https://render.com) and sign up
2. Create a **New Web Service** from GitHub
3. Select `arthfs/content-management`
4. Configure:
   - **Root Directory**: `backend/`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add the environment variables listed below.
6. Select the **Free** instance for initial testing. Omit `UPLOAD_DIR` to use the default `uploads` directory. Free services cannot attach persistent disks.
7. Deploy and save the Render service URL.

**Free-tier limitations:** Render spins down an idle service, so scheduled posts may be delayed until it wakes. Uploaded video files are lost on spin-down, restart, or redeploy; Supabase retains the video records but scheduled publishing can fail if its file is gone. Keep original videos and use immediate posting for testing. When upgrading to a paid instance, attach a persistent disk mounted at `/var/data` and set `UPLOAD_DIR=/var/data/uploads` (disk costs extra).

### Supabase PostgreSQL
1. Create a Supabase project and open **Project Settings → Database**.
2. Copy the PostgreSQL connection string. Use the session pooler when the direct database endpoint cannot be reached from Render.
3. In Render, set `DATABASE_URL` to that connection URL. This app accepts `postgresql://` or `postgresql+psycopg://` URLs; credentials containing reserved characters must be URL-encoded.
4. Do not use the test database URL in Render. The app creates its tables at startup and adds the few supported compatibility columns.

Render environment variables:
```env
SECRET_KEY=<strong random secret>
DATABASE_URL=<Supabase PostgreSQL connection URL>
FRONTEND_ORIGIN=https://<your-vercel-domain>.vercel.app
TIKTOK_CLIENT_KEY=<from-tiktok-developer>
TIKTOK_CLIENT_SECRET=<from-tiktok-developer>
TIKTOK_REDIRECT_URI=https://<your-vercel-domain>.vercel.app/settings
AUTH_REQUIRED=true
DEFAULT_USER_EMAIL=me@local
GEMINI_API_KEY=<optional>
```

Keep the Render service at a single instance: scheduled publishing currently runs in-process, so multiple instances could publish the same due video more than once.

Authentication should be enabled for the hosted test app. Keep `AUTH_REQUIRED=true` on Render and `NEXT_PUBLIC_AUTH_REQUIRED=true` on Vercel, then register/sign in through the app.

---

## 🎵 Part 3: Register Your App on TikTok Developer Portal

### Prerequisites
- ✅ TikTok Developer Account (created)
- ✅ App name: "My Content Manager"
- ✅ Vercel frontend URL (from Part 1)
- ✅ Backend service URL (from Part 2)

### Step 1: Create Your TikTok App
1. Go to [TikTok Developer Platform](https://developers.tiktok.com/app)
2. Sign in with your TikTok Developer account
3. Click **"Create an app"**
4. Fill in:
   - **App name**: "My Content Manager"
   - **Category**: Content Creator / Marketing Tools
   - **Description**: Tool to manage and schedule TikTok content uploads
5. Accept terms and click **"Create"**

### Step 2: Configure OAuth & Redirect URI
1. In your app settings, go to **Login Kit** → **Settings**
2. Add **Redirect URIs**:
   ```
   https://<your-vercel-domain>.vercel.app/settings
   ```
   - Example: `https://content-management-abc123.vercel.app/settings`
3. Note your:
   - **Client Key** (Client ID)
   - **Client Secret** (keep this safe!)
4. Set **User permissions** to:
   - `user.info.basic` (get user profile)
   - `video.publish` (publish videos)

### Step 3: Enable Direct Post API
1. Go to **Your apps** → **My Content Manager**
2. Navigate to **Capabilities** → **Publish Video**
3. Request access to **Content Posting API** (Direct Upload)
4. Complete the questionnaire:
   - Use case: Content management tool
   - Upload method: Direct file upload (chunked)
   - Compliance: Adheres to TikTok content guidelines
   - Privacy handling: No data collection beyond session
5. Submit for review

### Step 4: Fill Backend Environment Variables
Once you have your TikTok credentials, update your backend `.env`:

```env
TIKTOK_CLIENT_KEY=<your-client-key>
TIKTOK_CLIENT_SECRET=<your-client-secret>
TIKTOK_REDIRECT_URI=https://<your-vercel-domain>.vercel.app/settings
```

Redeploy your backend with these credentials.

---

## ✨ Part 4: Test the Full Flow

### 1. Frontend Test
1. Visit your Vercel domain: `https://<your-vercel-domain>.vercel.app`
2. Register or sign in (hosted configuration uses authentication)
3. Click **Videos** to see the video gallery (empty initially)

### 2. Settings & TikTok Connection
1. Click **Settings** in the top navigation
2. Click **"Connect TikTok Account"**
3. You'll be redirected to TikTok's login
4. Authorize the app (grant permissions)
5. TikTok will redirect back to your settings page
6. You should see your creator info displayed

### 3. First Video Upload (Mock Test)
1. Go to **Videos** → **"New Video"**
2. Upload a test MP4 file (short clip, < 60 seconds)
3. Add title and caption
4. Click **"Upload & Post Now"** (or set a scheduled time)
5. Monitor the **Post Status** panel for upload progress
6. Once posted, refresh your profile in Settings to see the post on your TikTok account

### 4. Real Integration Test
With credentials set, the app will:
- Fetch your real TikTok creator info
- Upload directly via TikTok's API
- Track posting status
- (Optional) Fetch audience insights for best-time recommendations

---

## 🔐 Security Checklist

- [ ] `SECRET_KEY` in backend `.env` is a strong random string (not "change-me")
- [ ] `TIKTOK_CLIENT_SECRET` is **never** committed to git
- [ ] `.env` files are in `.gitignore`
- [ ] Backend `CORS` origin matches your Vercel domain exactly
- [ ] TikTok redirect URI is **HTTPS** (not http://)
- [ ] Database credentials for production are stored **only** in hosting provider's secrets
- [ ] No sensitive data is logged or printed to stdout

---

## 🔄 Ongoing Maintenance

### Monitoring
- **Vercel**: Check deployments in dashboard; enable error notifications
- **Render**: Monitor logs for API errors and database issues
- **TikTok**: Check API quotas and rate limits in developer portal

### Updates
- Keep dependencies updated: `pip install --upgrade -r requirements.txt` (backend)
- Run `npm update` regularly (frontend)
- Monitor TikTok API docs for breaking changes

### Backups
- Backend stores uploaded videos in `backend/uploads/` (local disk on your service)
- Decide: auto-purge after posting or keep as backup archive
- Configure Supabase backups for your database

---

## 📋 Troubleshooting

### "Connection refused" when frontend tries to reach backend
- Check `NEXT_PUBLIC_API_URL` in Vercel environment variables
- Verify backend service is running and healthy
- Check CORS settings in backend `main.py` (should allow your Vercel domain)

### TikTok login redirects loop
- Ensure `TIKTOK_REDIRECT_URI` in backend `.env` matches the URI registered in TikTok portal
- URI must be HTTPS and exactly match (no trailing slashes)

### "Media upload failed" when posting
- Check file size (TikTok limit: typically 287 MB for videos)
- Verify file format is MP4 with h264 video codec
- Check backend logs for TikTok API error responses

### Login is not enabled as expected
- Verify `AUTH_REQUIRED=true` in Render and `NEXT_PUBLIC_AUTH_REQUIRED=true` in Vercel
- Redeploy the frontend after changing its environment variable
- Confirm the Supabase database connection works so user registration can persist

---

## 📞 Support

- **TikTok API Issues**: [TikTok Developer Docs](https://developers.tiktok.com/docs/en/)
- **Vercel Deployment**: [Vercel Docs](https://vercel.com/docs)
- **FastAPI Deployment**: [FastAPI Docs](https://fastapi.tiangolo.com/deployment/)
- **Render/Supabase Support**: See each service's documentation

---

## ✅ Final Sign-Off Checklist

Before launching:
- [ ] Backend tests pass locally
- [ ] Frontend builds without errors
- [ ] Vercel deployment is live
- [ ] Backend service is deployed and healthy
- [ ] Environment variables are configured on all services
- [ ] TikTok app is registered and credentials are filled
- [ ] TikTok redirect URI is registered in portal
- [ ] Frontend can connect to backend (test with API call)
- [ ] TikTok login flow works (Settings → Connect)
- [ ] Test video uploads and posts successfully

**Status**: Deploy after the PostgreSQL test suite and live Supabase connection have been verified.
