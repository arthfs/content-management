# 🚀 Deployment Checklist (Copy & Bookmark)

## Pre-Flight (5 min)
- [ ] Backend tests passing: `python -m pytest` ✅
- [ ] Frontend build passing: `npm run build` ✅
- [ ] TypeScript check: `npx tsc --noEmit` ✅
- [ ] Git status clean (or ready to commit)

---

## Phase 1: Vercel Frontend Deployment (10 min)

### Setup
- [ ] Log in to vercel.com (existing account)
- [ ] Click "Add New" → "Project"
- [ ] Import `arthfs/content-management`
- [ ] Set Root Directory: `frontend/`

### Environment Variables
- [ ] `NEXT_PUBLIC_API_URL` = `https://YOUR_BACKEND_URL` (placeholder: update after deploying backend)
- [ ] `NEXT_PUBLIC_AUTH_REQUIRED` = `true`

### Deploy
- [ ] Click "Deploy"
- [ ] Wait for build to complete (~2 min)
- [ ] Copy Vercel URL: `https://content-management-XXX.vercel.app`

**Vercel URL saved**: ___________________________

---

## Phase 2: Create TikTok App (10 min)

### Register App
- [ ] Go to developers.tiktok.com
- [ ] Log in with Developer Account ✅
- [ ] Click "My Apps" → "Create an app"
- [ ] App Name: "My Content Manager"
- [ ] Category: Marketing Tools / Content Creator Tools
- [ ] Submit

### Get Credentials
- [ ] Go to **Settings** → **Credentials**
- [ ] Copy **Client Key**: ___________________________
- [ ] Copy **Client Secret**: ___________________________
- [ ] ⚠️ Keep Secret private (never commit)

### Configure OAuth
- [ ] Go to **Settings** → **OAuth Scopes**
- [ ] Enable `user.info.basic`
- [ ] Enable `video.publish`
- [ ] Go to **Redirect URIs**
- [ ] Add: `https://content-management-XXX.vercel.app/settings` (use your Vercel URL from Phase 1)
- [ ] Save changes

**TikTok Client Key saved**: ___________________________
**TikTok Client Secret saved** (secure location): ___________________________
**Redirect URI confirmed**: ___________________________

---

## Phase 3: Create Supabase Database (10 min)

- [ ] Create a Supabase project
- [ ] Open **Project Settings → Database**
- [ ] Copy a PostgreSQL connection string (use session pooler if Render cannot reach the direct endpoint)
- [ ] Keep the database password private; URL-encode reserved characters if needed

**Supabase project / connection confirmed**: ___________________________

---

## Phase 4: Deploy Backend to Render (20 min)

### Configure Service
- [ ] Create a Web Service from `arthfs/content-management`
- [ ] Set **Root Directory**: `backend/`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Choose the Free instance and omit `UPLOAD_DIR` to use the default local `uploads` directory
- [ ] Keep one backend instance for the in-process scheduler

### Add Environment Variables
In the Render dashboard, add:

```
SECRET_KEY = <generate-32-char-random-string>
DATABASE_URL = <Supabase PostgreSQL connection URL>
FRONTEND_ORIGIN = https://content-management-XXX.vercel.app
TIKTOK_CLIENT_KEY = <from-phase-2>
TIKTOK_CLIENT_SECRET = <from-phase-2>
TIKTOK_REDIRECT_URI = https://content-management-XXX.vercel.app/settings
AUTH_REQUIRED = true
DEFAULT_USER_EMAIL = me@local
```

Set `NEXT_PUBLIC_AUTH_REQUIRED=true` in Vercel as well. Register an account through the app before testing the authenticated flows.

Free services sleep and lose uploaded videos on spin-down, restart, or redeploy; scheduled posts may be delayed or fail. Keep originals and test immediate posting. After upgrading to a paid instance, attach a persistent disk at `/var/data` and set `UPLOAD_DIR=/var/data/uploads`; disk costs extra.

- [ ] All variables filled
- [ ] Click "Deploy"
- [ ] Wait for deployment (~3 min)
- [ ] Copy Render URL: `https://<your-service>.onrender.com`

**Render Backend URL saved**: ___________________________

---

## Phase 5: Connect Frontend to Backend (5 min)

### Update Vercel Environment
- [ ] Go back to Vercel dashboard
- [ ] Settings → Environment Variables
- [ ] Find `NEXT_PUBLIC_API_URL`
- [ ] Update to your Render URL (from Phase 4)
- [ ] Vercel auto-redeploys

- [ ] Wait for redeploy to complete
- [ ] Check domains are connected

---

## Phase 6: End-to-End Test (15 min)

### Test 1: Frontend Access
- [ ] Visit `https://content-management-XXX.vercel.app`
- [ ] Register/sign in and confirm the dashboard loads
- [ ] UI loads without errors
- [ ] Network tab shows requests to correct backend

### Test 2: TikTok OAuth
- [ ] Click "Settings" in navigation
- [ ] Click "Connect TikTok Account"
- [ ] Redirected to TikTok login
- [ ] Log in with your TikTok account
- [ ] Grant permissions
- [ ] Redirected back to Settings page
- [ ] See your creator info (name, avatar, followers)

### Test 3: Upload & Post
- [ ] Go to "Videos"
- [ ] Click "New Video"
- [ ] Upload a test MP4 (< 60 sec, < 287 MB)
- [ ] Add title & caption
- [ ] Click "Upload & Post"
- [ ] Monitor status panel:
  - "Initializing..." ✓
  - "Uploading..." ✓
  - "Posted ✓" ✓
- [ ] Go to your TikTok profile
- [ ] New video appears (private/SELF_ONLY in dev mode)

**Test Status**: ____________________________

---

## Phase 7: TikTok App Review (1–7 days)

### Request Public Posting
- [ ] Go to TikTok Developer dashboard
- [ ] Navigate to **Capabilities** → **Publish Video**
- [ ] Click "Request Access" (or "Apply")
- [ ] Fill application form:
  - Use case: Content management tool
  - Upload method: Chunked file upload
  - Include sample video + screenshot
- [ ] Submit

### Monitor Review
- [ ] Check email for TikTok review status
- [ ] Once approved, your app can post public videos
- [ ] Status shows in developer dashboard

**TikTok App Status**: ____________________________

---

## Final Checklist Before Going Live

### Security
- [ ] `SECRET_KEY` is 32+ random characters
- [ ] `.env` files are in `.gitignore`
- [ ] Secrets stored only in hosting provider dashboards
- [ ] HTTPS redirect URI registered in TikTok portal
- [ ] No secrets in git history

### Testing
- [ ] Frontend loads and connects to backend
- [ ] TikTok login works
- [ ] Can upload and post videos
- [ ] Videos appear on TikTok profile

### Deployment
- [ ] Vercel deployment live
- [ ] Render deployment live and healthy
- [ ] Supabase PostgreSQL connection verified
- [ ] Environment variables configured on all services
- [ ] Backend database is production-ready

### Documentation
- [ ] TikTok app registered and awaiting review
- [ ] Redirect URI registered in TikTok portal
- [ ] Credentials stored securely
- [ ] Deployment documented

---

## 🎯 Status Summary

| Phase | Task | Status | Time |
|-------|------|--------|------|
| 1 | Frontend → Vercel | ⏳ | 10 min |
| 2 | TikTok App Setup | ⏳ | 10 min |
| 3 | Supabase PostgreSQL | ⏳ | 10 min |
| 4 | Backend → Render | ⏳ | 20 min |
| 5 | Connect Frontend ↔ Backend | ⏳ | 5 min |
| 6 | End-to-End Testing | ⏳ | 15 min |
| 7 | TikTok Review | ⏳ | 1–7 days |

**Total Hands-On Time**: ~60 minutes  
**Total Calendar Time**: 1–7 days (TikTok review)

---

## 📚 Reference Guides

If you get stuck:
- **QUICK_START.md** — 30-min overview with copy-paste commands
- **DEPLOYMENT_GUIDE.md** — Detailed steps for all platforms
- **TIKTOK_REGISTRATION.md** — TikTok setup, testing, troubleshooting

---

## 🎉 Success!

Once all phases complete and TikTok approves your app:
1. Your Content Manager is live on Vercel
2. Backend is running on Render
3. You can upload and publish TikTok videos directly from the web app
4. Best-time recommendations are ready to use

**Happy posting!** 🚀

---

**Started**: ________________________  
**Completed**: ________________________  
**Notes**: ________________________
