---
name: tiktok-api
description: "Use when changing TikTok posting, OAuth, creator info, publish status or the Post to TikTok panel. Lists the TikTok Content Posting API rules this repo must follow (https://developers.tiktok.com/docs/en/)."
---

# TikTok API rules

Code: `backend/app/tiktok.py` (API calls), `backend/app/publisher.py` (publish + status), `frontend/components/PostPanel.tsx` (UX).

- Direct Post flow: creator info (`/post/publish/creator_info/query/`) -> init (`/post/publish/video/init/`) -> chunked PUT to `upload_url` -> status (`/post/publish/status/fetch/`).
- `privacy_level` must be one of `privacy_level_options` from creator info; the UI shows no default. Unaudited apps can only post `SELF_ONLY`.
- Comment/duet/stitch: off by default; greyed out when creator info says disabled.
- Commercial content toggle (off by default): "Your brand" -> Promotional content; "Branded content" -> Paid partnership and can't be private. At least one option is required when on.
- Consent text before posting: Music Usage Confirmation (plus Branded Content Policy for branded content). Only send the video after consent.
- Never add watermarks, logos or promo text to the user's video or caption.
- Chunks: 5-64 MB (last one may be up to 128 MB), videos <5 MB in one chunk, max 1000 chunks, sequential. Headers: `Content-Type`, `Content-Length`, `Content-Range`.
- Caption max 2200 UTF-16 units. Rate limits: creator info 20/min, init 6/min, status 30/min per token.
- Access token lives 2 h, refresh token 180 days and is rotated on every refresh: always store the newest one.
- Redirect URI must be HTTPS and registered; OAuth `state` must be verified (signed token in `security.py`).
- `publicaly_available_post_id` (sic) only appears for public, moderated posts; private posts never get a post id.
- Map new documented error codes in `ERROR_MESSAGES` in `tiktok.py` and add a mocked-HTTP test in `backend/tests/test_api.py`.
