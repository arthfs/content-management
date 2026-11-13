# 📌 Quick Reference Card

## What's Ready

```
⏳ Backend:   PostgreSQL integration tests pending
✅ Frontend:  Production build ready
⏳ Database:  PostgreSQL driver configured; Supabase connection pending
✅ Docs:      9 guides created
✅ Security:  All best practices included
```

## Where to Start

```
⏱️  SHORT ON TIME? (5-10 min)
    → .github/START_HERE.md

⏱️  MEDIUM TIME (30 min)
    → .github/QUICK_START.md

⏱️  FULL GUIDE (70 min with tracking)
    → .github/DEPLOYMENT_CHECKLIST.md

⏱️  COMPLETE DETAILS (2+ hours)
    → .github/DEPLOYMENT_GUIDE.md
```

## The 5 Deployment Phases

```
1. Frontend → Vercel           (10 min)
2. TikTok App Setup             (10 min)
3. Supabase PostgreSQL           (10 min)
4. Backend → Render              (20 min)
5. Connect Services              (5 min)
6. Test Everything               (15 min)
   ────────────────────────────
   TOTAL: ~55 minutes
```

## Key Files in .github/

| File | Use When |
|------|----------|
| **START_HERE.md** | You don't know where to begin |
| **GUIDE_SELECTOR.md** | You want help choosing |
| **QUICK_START.md** | You want a fast overview |
| **DEPLOYMENT_CHECKLIST.md** | You want step-by-step tracking |
| **DEPLOYMENT_GUIDE.md** | You need all details |
| **TIKTOK_REGISTRATION.md** | You're setting up TikTok |
| **ENV_TEMPLATES.md** | You need env variable values |

## Critical Things to Remember

```
🔴 MUST DO:
   • Register Redirect URI in TikTok portal (HTTPS only)
   • Set TikTok credentials in backend .env
   • Never commit .env files

🔴 DON'T FORGET:
   • Create Supabase PostgreSQL project
   • Use strong SECRET_KEY (32+ chars)
   • Save your Vercel URL for later

🔴 SECURITY:
   • Keep TIKTOK_CLIENT_SECRET private
   • Store all secrets in hosting dashboards
   • Use HTTPS for all URLs
```

## Testing Checklist

After deployment, verify:

```
□ Frontend loads at https://your-app.vercel.app
□ Backend responds at https://your-service.onrender.com/docs
□ TikTok login works (Settings page)
□ Can upload a test video
□ Video posts to TikTok
□ Video appears on your profile
```

## Environment Variables at a Glance

### Backend (Set on Render)
```
SECRET_KEY = [32+ random chars]
DATABASE_URL = <Supabase PostgreSQL connection URL>
UPLOAD_DIR = /var/data/uploads
FRONTEND_ORIGIN = https://your-vercel-app.com
TIKTOK_CLIENT_KEY = [from TikTok]
TIKTOK_CLIENT_SECRET = [from TikTok]
TIKTOK_REDIRECT_URI = https://your-app.com/settings
AUTH_REQUIRED = true
```

### Frontend (Set on Vercel)
```
NEXT_PUBLIC_API_URL = https://your-service.onrender.com
NEXT_PUBLIC_AUTH_REQUIRED = true
```

## Platform Quick Links

```
Vercel:        https://vercel.com
Render:        https://render.com
Supabase:      https://supabase.com
TikTok Dev:    https://developers.tiktok.com
TikTok API:    https://developers.tiktok.com/docs/en/
```

## Common Issues & Quick Fixes

| Issue | Fix |
|-------|-----|
| "Connection refused" | Check NEXT_PUBLIC_API_URL in Vercel env |
| TikTok login fails | Verify redirect URI is HTTPS + exact match |
| Video upload fails | Check file is MP4 with h264 codec |
| Env vars not working | Restart backend after setting them |

## Success = This

```
You can:
✓ Visit your app
✓ Click Settings
✓ Connect with TikTok
✓ Upload a video
✓ See it on TikTok
✓ Set best-time recommendations

TIME TO SUCCESS: after database verification and deployment (TikTok review timing varies)
```

## Key Contacts

- **TikTok Developer Support**: https://community.tiktok.com/developers/
- **Vercel Support**: help.vercel.com
- **Render Docs**: https://render.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **This Project**: See guides in .github/

---

**Print This** and keep it open while deploying! 🚀
