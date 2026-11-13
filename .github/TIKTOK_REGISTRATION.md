# TikTok Registration & Integration Checklist

**Purpose**: Verify your app meets TikTok requirements before first real post  
**Status**: Ready to register ✅

---

## 📋 Pre-Registration: Developer Account & App Creation

### TikTok Developer Account
- [ ] Account created at [developers.tiktok.com](https://developers.tiktok.com)
- [ ] Verified email address
- [ ] Personal TikTok account linked (recommended)
- [ ] API tier appropriate for your use (free tier for testing)

### Create Your App
1. Go to **TikTok Developer Platform** → **My Apps** → **Create an app**
2. Fill form:
   - **App Name**: "My Content Manager"
   - **Application Category**: Choose "Other" → "Content Creator Tools" or "Marketing Tools"
   - **Display Language**: English
3. Review and accept Developer Agreement
4. **Submit**
5. Your app is created in **Development** status

---

## 🔑 Credentials & Security

### Get Your Credentials
In your app dashboard:
1. Go to **Edit app** → **Credentials**
2. Copy **Client Key** (also called Client ID)
3. Copy **Client Secret** (keep SECRET — never commit to git)
4. Save both to your `backend/.env`:
   ```env
   TIKTOK_CLIENT_KEY=your_client_key_here
   TIKTOK_CLIENT_SECRET=your_client_secret_here
   ```

### ⚠️ Security Rules (Critical)
- [ ] **Never** share Client Secret with anyone
- [ ] **Never** commit `.env` or secrets to git
- [ ] Regenerate secret if ever exposed
- [ ] Use different secrets for dev/staging/production
- [ ] Backend environment variables in production are set in the Render dashboard

---

## 🔗 OAuth & Redirect URI Configuration

### What is the Redirect URI?
After user logs in with TikTok, TikTok redirects back to your app with an authorization code. You must tell TikTok where this callback URL is.

### Set Your Redirect URI
1. In your TikTok app dashboard, go **Settings** → **OAuth Scopes** or **Login Kit** (exact location varies)
2. Add **Redirect URIs**:
   ```
   https://<your-vercel-domain>.vercel.app/settings
   ```
   - Example: `https://content-manager-xyz.vercel.app/settings`
   - **Must be HTTPS** (TikTok does not allow HTTP)
   - **Must be exact match** (no trailing slashes, exact domain)

3. Update your backend `.env`:
   ```env
   TIKTOK_REDIRECT_URI=https://<your-vercel-domain>.vercel.app/settings
   ```

### Test Redirect
1. Deploy backend with new `TIKTOK_REDIRECT_URI`
2. In Settings page, click "Connect TikTok Account"
3. After login, you should land back on `/settings` page (not an error)

---

## 🎬 Capabilities: Enable Video Publishing

### Request Content Posting API Access

**Current Status**: App is in **Development** — can only post `SELF_ONLY` (private) videos

### What You Need for Public Posts
To post public videos, you need TikTok to review and approve your app. Here's the process:

#### Step 1: Request Capabilities
1. In your app dashboard, go **Capabilities** → **Publish Video**
2. Status should show: "Approved" or "Review Pending" or "Request Access"
3. If "Request Access", click **"Request Access"** or **"Apply"**

#### Step 2: Complete the Application Form
TikTok will ask you to fill an application with:
- **Use Case**: "A content management tool that allows users to upload and schedule TikTok videos"
- **Video Source**: "User-uploaded files via web interface"
- **Upload Method**: "Chunked file upload" or "Direct file upload"
- **Privacy Policy**: Link to your privacy policy
- **Data Handling**: "No data storage beyond session; files deleted after posting"
- **Compliance**: "App complies with TikTok Community Guidelines and Commercial Music Library"

#### Step 3: Upload Sample Video & Screenshot
- Submit a **short test video** (10–60 seconds, MP4 format)
- Screenshot of your app interface showing the upload flow
- Example description: "Content Manager allows creators to upload, caption, and schedule TikTok videos directly from a web dashboard"

#### Step 4: Wait for Review
- TikTok reviews in **2–7 days**
- You'll receive email notification
- Status updates in your app dashboard

### In the Meantime (Development Mode)
Your app **can** post in development mode, but:
- [ ] Videos post as **`SELF_ONLY`** (private, only you can see)
- [ ] You cannot set any other privacy level (`FRIENDS_ONLY`, `PUBLIC`)
- [ ] UI disables privacy dropdown (frontend checks `disable_comment`, `disable_duet`, `disable_stitch` from creator info)

### After Approval (Production Mode)
- [ ] Videos can post as **`PUBLIC`** (visible to all)
- [ ] Privacy dropdown enabled in UI
- [ ] All posting options available

---

## ✅ Required Permissions & Scopes

Ensure your TikTok app has these permissions enabled:

- [ ] **user.info.basic** — Read creator name, profile picture, follower count
- [ ] **video.publish** — Upload and publish videos
- [ ] **video.publish.publish** or similar — Post videos (exact name varies by region)

### Configure in Dashboard
1. Go **Settings** → **OAuth Scopes**
2. Ensure the above are **checked** and **enabled**
3. Save changes
4. Redeploy backend (scopes checked at OAuth login)

---

## 🎯 Testing Checklist

### Test 1: OAuth Login Flow
1. Navigate to `https://<your-vercel-domain>/settings`
2. Click "Connect TikTok Account"
3. Login with your TikTok personal account
4. Grant permissions
5. Redirected back to settings
6. **Expected**: Creator info displayed (name, profile pic, follower count, etc.)

### Test 2: Creator Info Validation
1. After connecting, the app fetches creator info via `GET /api/tiktok/creator-info`
2. **Expected Response** (in mock mode or real):
   ```json
   {
     "username": "your_username",
     "display_name": "Your Name",
     "follower_count": 1234,
     "video_count": 56,
     "bio": "Your bio...",
     "avatar_large_url": "https://...",
     "is_verified": false,
     "disable_comment": false,
     "disable_duet": false,
     "disable_stitch": false
   }
   ```

### Test 3: First Video Upload
1. Go to **Videos** → **New Video**
2. Upload a test MP4 (< 60 seconds, < 287 MB)
3. Add title and caption
4. **Private Mode** (Development): Privacy defaults to `SELF_ONLY` (auto-selected)
5. Check **Commercial Content** checkbox if applicable
6. Click **Upload & Post**
7. Monitor **Post Status** panel:
   - "Initializing upload..." → "Uploading..." → "Posted ✓"
8. **Expected**: After ~30 seconds, video appears on your TikTok account (private only in dev mode)

### Test 4: Best Time Recommendation (Optional)
1. After posting, go to **New Video** again
2. Panel shows "Suggested times based on your audience"
3. Click on a suggested time slot
4. **Expected**: Scheduled time is set; video will post automatically at that time

### Test 5: Status Polling (Optional)
1. Post a video
2. Refresh the page (or wait)
3. Video status updates from "Uploading" → "Posted"
4. **Expected**: No manual refresh needed (polling every 5 seconds for 2 minutes)

---

## 🔴 Common Issues & Fixes

### "invalid_redirect_uri" Error During Login
**Cause**: Redirect URI in TikTok portal doesn't match `TIKTOK_REDIRECT_URI` in backend `.env`
**Fix**:
- Check exact URL match (case-sensitive, no trailing slash)
- Verify it's HTTPS, not HTTP
- Update both TikTok portal and backend `.env`
- Restart backend

### "Media upload failed" or "Invalid file format"
**Cause**: File not MP4 or video codec not h264
**Fix**:
- Convert video: `ffmpeg -i input.mov -vcodec h264 -acodec aac output.mp4`
- Check file size < 287 MB
- Test file locally first: `python -c "from app import tiktok; tiktok.validate_media('file.mp4')"`

### "You don't have permission to publish videos"
**Cause**: 
- Scopes not granted during OAuth
- App still in development (expected for public posts)
- Refresh token expired
**Fix**:
- Disconnect and reconnect TikTok account in Settings
- Re-grant all permissions
- Wait for app approval if requesting public posts

### OAuth Token Expired
**Cause**: Access token older than ~24 hours without refresh
**Fix**: 
- App auto-refreshes on use (checks expiry before each API call)
- Manual reconnect in Settings if issues persist

---

## 📊 Monitoring & Analytics

### Check Your Posts
1. Go to **Videos** in the app, or check your TikTok profile directly
2. Private posts appear only to your account
3. Once approved, public posts visible to all

### Best Time Analytics
- After each post, app fetches audience demographics
- Next "New Video" shows recommended posting times
- Improves over time as more posts accumulate

### API Rate Limits
TikTok limits requests per user:
- Upload: ~1 video per 5 seconds
- Creator info: ~100 requests per hour
- Status polling: ~1000 requests per hour

App respects these limits (no rapid-fire uploads)

---

## 🚀 Going to Production

### Before Public Launch
1. [ ] TikTok app approved for public posting
2. [ ] Backend deployed on Render with Supabase PostgreSQL
3. [ ] Vercel frontend live and connected to backend
4. [ ] All environment variables set securely
5. [ ] Test video posted successfully
6. [ ] Privacy settings working as expected
7. [ ] Error handling tested (network errors, invalid files, etc.)

### Scaling Considerations
- TikTok API may limit daily uploads as app grows
- Consider queueing system for bulk uploads
- Monitor quota usage in developer portal
- Request quota increase if needed

### Maintenance
- Check TikTok API docs monthly for changes
- Update dependencies: `pip install --upgrade -r requirements.txt`
- Monitor error logs for API failures
- Refresh credentials if regenerated

---

## 📞 Support Resources

- **TikTok Developer Docs**: https://developers.tiktok.com/docs/en/
- **Content Posting API**: https://developers.tiktok.com/docs/en/content-posting-api/
- **OAuth Guide**: https://developers.tiktok.com/docs/en/auth-and-permissions/
- **Developer Support**: https://community.tiktok.com/developers/

---

## ✅ Sign-Off Checklist

Before posting your first real video:
- [ ] Client Key and Secret stored securely in backend `.env`
- [ ] Redirect URI registered in TikTok portal and matches backend
- [ ] Video.publish scope enabled
- [ ] OAuth test successful (can login and see creator info)
- [ ] First video uploaded and posted (in `SELF_ONLY` mode during development)
- [ ] Video appears on your TikTok profile
- [ ] TikTok app submitted for review (if targeting public posts)

**Ready to launch!** 🎉
