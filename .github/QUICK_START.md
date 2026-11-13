# 🚀 Quick Start: Deployment & TikTok Setup

**Timeline**: ~2–3 hours for deployment, ~1–7 days for TikTok app review  
**Status**: Render/Supabase instructions are prepared; configure the live database before deployment.

---

## 📝 30-Minute Quick Setup

### What You Need Right Now
1. **Vercel Account**: ✅ (you have this)
2. **TikTok Developer Account**: ✅ (you have this)
3. **TikTok App Credentials** (TBD): Client Key + Secret
4. **Backend Service** (TBD): Render account
5. **Database** (TBD): Supabase PostgreSQL project

### Part 1: Deploy Frontend to Vercel (15 min)

**Command Line** (optional, or use Vercel dashboard):
```bash
npm install -g vercel
cd frontend
vercel --prod
```

**OR Via Dashboard**:
1. Go to [vercel.com](https://vercel.com)
2. Click "Add New" → "Project"
3. Import `arthfs/content-management`
4. Set **Root Directory** to `frontend/`
5. Add environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://YOUR_BACKEND_URL (placeholder for now)
   NEXT_PUBLIC_AUTH_REQUIRED=true
   ```
6. Click **Deploy**

**Save this URL**: `https://content-management-XXX.vercel.app` (you'll use it next)

---

### Part 2: Create TikTok App (10 min)

1. Go to [developers.tiktok.com](https://developers.tiktok.com)
2. Click **My Apps** → **Create an app**
3. App Name: "My Content Manager"
4. Category: Marketing Tools
5. Submit
6. Copy **Client Key** and **Client Secret**
7. Go to **Settings** → **OAuth Scopes** → Enable:
   - `user.info.basic`
   - `video.publish`
8. Go to **Redirect URIs** → Add: `https://content-management-XXX.vercel.app/settings` (use your Vercel URL from Part 1)

**Save these**:
- Client Key: `_____________________`
- Client Secret: `_____________________`
- Redirect URI: `https://content-management-XXX.vercel.app/settings`

---

### Part 3: Set Up Supabase PostgreSQL (10 min)

1. Create a project at [supabase.com](https://supabase.com).
2. In **Project Settings → Database**, copy a PostgreSQL connection string. Use the session pooler if the direct endpoint is unreachable from Render.
3. Keep the database password private and URL-encode special characters in it. Set this as `DATABASE_URL` in Render in Part 4.

---

### Part 4: Deploy the Backend to Render (20 min)

1. Go to [render.com](https://render.com) and create a **Web Service** from `arthfs/content-management`.
2. Set **Root Directory** to `backend`.
3. Set **Build Command** to `pip install -r requirements.txt`.
4. Set **Start Command** to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
5. Add these environment variables in Render:
   ```
   SECRET_KEY=<a strong random secret>
   DATABASE_URL=<Supabase PostgreSQL connection URL>
   FRONTEND_ORIGIN=https://content-management-XXX.vercel.app
   TIKTOK_CLIENT_KEY=<from-step-2>
   TIKTOK_CLIENT_SECRET=<from-step-2>
   TIKTOK_REDIRECT_URI=https://content-management-XXX.vercel.app/settings
   AUTH_REQUIRED=true
   DEFAULT_USER_EMAIL=me@local
   ```
6. Choose the **Free** instance for initial testing. Omit `UPLOAD_DIR` to use the default local `uploads` directory; persistent disks are not available on the free tier.
7. Deploy, then save the Render service URL (for example, `https://content-manager-api.onrender.com`).

Authentication is enabled for the hosted test app. Create an account on the login screen, and keep `AUTH_REQUIRED=true` on Render and `NEXT_PUBLIC_AUTH_REQUIRED=true` on Vercel.

Free Render sleeps after inactivity and loses uploaded files on spin-down, restart, or deploy. Scheduled posts can be delayed or fail if their video is gone; keep originals and test immediate posting. When you upgrade to a paid instance, add a disk at `/var/data` and set `UPLOAD_DIR=/var/data/uploads`; storage is charged separately.

---

### Part 5: Connect Frontend to Backend (5 min)

**Back to Vercel Dashboard**:
1. Go to your frontend project
2. Settings → Environment Variables
3. Update `NEXT_PUBLIC_API_URL`:
   ```
   NEXT_PUBLIC_API_URL=https://<your-render-service>.onrender.com
   ```
4. Vercel auto-redeploys

---

## ✅ Testing (10 min)

1. **Visit frontend**: `https://content-management-XXX.vercel.app`
   - Sign in or register, then confirm the dashboard loads

2. **Go to Settings** → **Connect TikTok Account**
   - Should redirect to TikTok login
   - After approving, see your profile info

3. **Create a test video**:
   - Upload a short MP4
   - Post immediately
   - Status should go: "Uploading..." → "Posted ✓"

4. **Check TikTok**: Your video appears on your profile (private in dev mode)

**Success?** ✅ Everything works!

---

## 📋 Detailed Guides

For more information, see:
- **[DEPLOYMENT_GUIDE.md](.github/DEPLOYMENT_GUIDE.md)** — Full deployment steps, all platforms
- **[TIKTOK_REGISTRATION.md](.github/TIKTOK_REGISTRATION.md)** — TikTok setup, testing, and approval process

---

## 🎯 Next Steps

### Immediate (Next 1–2 hours)
- [ ] Deploy frontend to Vercel
- [ ] Create TikTok app and get credentials
- [ ] Create Supabase PostgreSQL project
- [ ] Deploy backend to Render
- [ ] Connect frontend to backend
- [ ] Test full flow (Settings → TikTok login → Upload video)

### Within 1 Week
- [ ] Submit TikTok app for review (for public posting)
- [ ] Monitor TikTok approval email
- [ ] Configure Render persistent disk for uploaded media

### Ongoing
- [ ] Monitor deployments
- [ ] Keep dependencies updated
- [ ] Check TikTok API limits

---

## ⚠️ Security Reminders

- [ ] Never commit `.env` files
- [ ] Never share `TIKTOK_CLIENT_SECRET`
- [ ] Use strong `SECRET_KEY` (32+ random chars)
- [ ] Set environment variables in hosting provider, not in code
- [ ] Use HTTPS redirect URIs (TikTok requires it)

---

## 📞 Troubleshooting

**Frontend can't reach backend?**
- Check `NEXT_PUBLIC_API_URL` is correct
- Verify backend is running: `curl https://<backend-url>/docs`
- Check CORS in backend (should allow your Vercel domain)

**TikTok login redirects in loop?**
- Verify redirect URI is HTTPS and matches exactly
- Check TikTok dashboard for the right URI
- No trailing slashes

**Video upload fails?**
- File must be MP4 with h264 codec
- Size < 287 MB
- Check backend logs in the Render dashboard

**Need help?**
- See detailed guides above
- TikTok Docs: https://developers.tiktok.com/docs/en/
- Vercel Docs: https://vercel.com/docs
- Render Docs: https://render.com/docs
- Supabase Docs: https://supabase.com/docs

---

**You're ready!** 🚀 Start with Part 1 above.
