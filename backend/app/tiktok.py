"""TikTok integration. Falls back to a deterministic mock when credentials are missing."""
"""TikTok integration (Login Kit + Content Posting API Direct Post).

Follows https://developers.tiktok.com/docs/en/ . Falls back to a deterministic mock when credentials
or the user's connection are missing.
"""
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx

from .config import settings
from .models import User

API = "https://open.tiktokapis.com/v2"
MAX_CAPTION_UNITS = 2200  # UTF-16 code units, per the Direct Post reference
PRIVACY_LEVELS = ("PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "FOLLOWER_OF_CREATOR", "SELF_ONLY")

ERROR_MESSAGES = {
    "privacy_level_option_mismatch": "The chosen privacy level isn't available for this TikTok account.",
    "unaudited_client_can_only_post_to_private_accounts":
        "This TikTok app hasn't passed TikTok's audit yet, so posts can only be private (Only me) "
        "and the TikTok account must be private.",
    "spam_risk_too_many_posts": "TikTok's daily post limit for this account was reached. Try again later.",
    "spam_risk_user_banned_from_posting": "TikTok has blocked this account from posting.",
    "reached_active_user_cap": "This app reached TikTok's daily active creator cap. Try again later.",
    "access_token_invalid": "The TikTok connection expired. Reconnect TikTok in Settings.",
    "scope_not_authorized": "TikTok permission missing (video.publish). Reconnect TikTok in Settings.",
    "rate_limit_exceeded": "TikTok rate limit hit. Try again in a minute.",
    "url_ownership_unverified": "TikTok can't pull from this URL. Upload the video file instead.",
}


class TikTokError(Exception):
    def __init__(self, code: str, message: str = ""):
        self.code = code
        super().__init__(ERROR_MESSAGES.get(code) or message or code)


def is_live(user: User) -> bool:
    return bool(settings.tiktok_configured and user.tiktok_access_token)


def auth_url(state: str) -> str:
    q = urlencode({
        "client_key": settings.tiktok_client_key,
        "scope": "user.info.basic,video.publish,video.upload,video.list",
        "response_type": "code",
        "redirect_uri": settings.tiktok_redirect_uri,
        "state": state,
    })
    return f"https://www.tiktok.com/v2/auth/authorize/?{q}"


def _token_request(data: dict) -> dict:
    r = httpx.post(f"{API}/oauth/token/", data={
        "client_key": settings.tiktok_client_key,
        "client_secret": settings.tiktok_client_secret,
        **data,
    }, headers={"Cache-Control": "no-cache"}, timeout=30)
    body = r.json()
    if "access_token" not in body:
        raise TikTokError(body.get("error", "oauth_error"), body.get("error_description", "TikTok authorization failed"))
    return body


def store_tokens(user: User, data: dict) -> None:
    """Save every token field; the refresh token is rotated on each refresh so the new one must replace the old."""
    user.tiktok_access_token = data["access_token"]
    user.tiktok_refresh_token = data.get("refresh_token") or user.tiktok_refresh_token
    user.tiktok_open_id = data.get("open_id") or user.tiktok_open_id
    user.tiktok_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(data.get("expires_in", 7200)))


def exchange_code(code: str) -> dict:
    return _token_request({"code": code, "grant_type": "authorization_code",
                           "redirect_uri": settings.tiktok_redirect_uri})


def ensure_fresh_token(user: User) -> bool:
    """Refresh the 2-hour access token shortly before it expires. Returns True if the user row changed."""
    if not is_live(user) or not user.tiktok_refresh_token or not user.tiktok_token_expires_at:
        return False
    expires = user.tiktok_token_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires - datetime.now(timezone.utc) > timedelta(minutes=5):
        return False
    store_tokens(user, _token_request({"grant_type": "refresh_token", "refresh_token": user.tiktok_refresh_token}))
    return True


def _call(user: User, path: str, body: dict | None = None) -> dict:
    r = httpx.post(f"{API}{path}", headers={"Authorization": "Bearer " + user.tiktok_access_token,
                                            "Content-Type": "application/json; charset=UTF-8"},
                   json=body or {}, timeout=60)
    try:
        payload = r.json()
    except ValueError:
        r.raise_for_status()
        raise TikTokError("bad_response", "Unexpected response from TikTok")
    err = payload.get("error") or {}
    if err.get("code", "ok") != "ok":
        raise TikTokError(err["code"], err.get("message", ""))
    return payload.get("data") or {}


def query_creator_info(user: User) -> dict:
    """Latest creator info; must be fetched whenever the 'Post to TikTok' page is rendered."""
    if not is_live(user):
        return {"creator_nickname": "Mock creator", "creator_username": "mock_creator",
                "creator_avatar_url": "", "privacy_level_options": list(PRIVACY_LEVELS),
                "comment_disabled": False, "duet_disabled": False, "stitch_disabled": False,
                "max_video_post_duration_sec": 600, "mock": True}
    return _call(user, "/post/publish/creator_info/query/")


def validate_options(options: dict, creator: dict) -> None:
    """Enforce the guideline rules before anything is sent to TikTok."""
    if not options.get("consent"):
        raise TikTokError("consent_required", "Confirm TikTok's declaration before posting.")
    level = options.get("privacy_level")
    if level not in creator.get("privacy_level_options", []):
        raise TikTokError("privacy_level_option_mismatch")
    if options.get("commercial_content") and not (options.get("brand_organic") or options.get("brand_content")):
        raise TikTokError("disclosure_required",
                          "You need to indicate if your content promotes yourself, a third party, or both.")
    if options.get("brand_content") and options.get("commercial_content") and level == "SELF_ONLY":
        raise TikTokError("branded_private", "Branded content visibility cannot be set to private.")


MIN_CHUNK = 5 * 1024 * 1024
CHUNK_SIZE = 10 * 1024 * 1024


def publish(user: User, caption: str, video_url: str, file_path: Path | None = None,
            options: dict | None = None) -> str:
    """Direct Post a video; returns TikTok's publish_id (mock id when not connected).

    An uploaded file is preferred over video_url. Raises TikTokError on documented API errors.
    """
    options = options or {}
    if not is_live(user):
        key = file_path.name if file_path else video_url
        return "mock-" + hashlib.sha1(f"{user.id}{caption}{key}".encode()).hexdigest()[:12]

    if len(caption.encode("utf-16-le")) // 2 > MAX_CAPTION_UNITS:
        raise TikTokError("caption_too_long", f"Caption is longer than {MAX_CAPTION_UNITS} characters.")
    creator = query_creator_info(user)
    validate_options(options, creator)
    commercial = bool(options.get("commercial_content"))
    post_info = {
        "title": caption,
        "privacy_level": options["privacy_level"],
        "disable_comment": creator.get("comment_disabled") or not options.get("allow_comment"),
        "disable_duet": creator.get("duet_disabled") or not options.get("allow_duet"),
        "disable_stitch": creator.get("stitch_disabled") or not options.get("allow_stitch"),
        "brand_content_toggle": commercial and bool(options.get("brand_content")),
        "brand_organic_toggle": commercial and bool(options.get("brand_organic")),
    }
    init = "/post/publish/video/init/"
    if file_path is None:
        data = _call(user, init, {"post_info": post_info,
                                  "source_info": {"source": "PULL_FROM_URL", "video_url": video_url}})
        return data["publish_id"]

    size = file_path.stat().st_size
    # <5 MB must be a single chunk; larger files use 10 MB chunks and the last one absorbs the remainder
    chunk = size if size < CHUNK_SIZE else CHUNK_SIZE
    count = max(1, size // chunk)
    data = _call(user, init, {"post_info": post_info,
                              "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                                              "chunk_size": chunk, "total_chunk_count": count}})
    mime = "video/quicktime" if file_path.suffix.lower() == ".mov" else (
        "video/webm" if file_path.suffix.lower() == ".webm" else "video/mp4")
    with file_path.open("rb") as f:
        for i in range(count):
            start = i * chunk
            end = size if i == count - 1 else start + chunk
            up = httpx.put(
                data["upload_url"], content=f.read(end - start), timeout=300,
                headers={"Content-Type": mime, "Content-Length": str(end - start),
                         "Content-Range": f"bytes {start}-{end - 1}/{size}"},
            )
            up.raise_for_status()
    return data["publish_id"]


def fetch_publish_status(user: User, publish_id: str) -> dict:
    """Returns {"status", "fail_reason", "post_id"}; post_id is only set once a public post passes moderation."""
    if not is_live(user) or publish_id.startswith("mock-"):
        return {"status": "PUBLISH_COMPLETE", "fail_reason": None, "post_id": None}
    data = _call(user, "/post/publish/status/fetch/", {"publish_id": publish_id})
    ids = data.get("publicaly_available_post_id") or []  # sic: TikTok's spelling
    return {"status": data.get("status", ""), "fail_reason": data.get("fail_reason"),
            "post_id": str(ids[0]) if ids else None}


def fetch_metrics(user: User, external_id: str) -> dict:
    """Return views/likes/comments/shares/avg watch time/completion."""
    if not is_live(user) or external_id.startswith("mock-"):
        return mock_metrics(external_id)
    empty = {"views": 0, "likes": 0, "comments": 0, "shares": 0}
    if not external_id.isdigit():  # still a publish_id: private or not yet moderated, no video id to query
        return empty
    try:
        data = _call(user, "/video/query/?fields=id,view_count,like_count,comment_count,share_count",
                     {"filters": {"video_ids": [external_id]}})
    except TikTokError:
        return empty
    vids = data.get("videos", [])
    if not vids:
        return empty
    v = vids[0]
    return {"views": v.get("view_count", 0), "likes": v.get("like_count", 0),
            "comments": v.get("comment_count", 0), "shares": v.get("share_count", 0)}


AUDIENCE_GROUPS = ("13-17", "18-24", "25-34", "35+")


def fetch_audience(user: User, external_id: str) -> dict[str, float]:
    """Share of the post's viewers (followers or not) per age group, e.g. {"18-24": 0.5, ...}.

    TikTok's Display/Content Posting APIs expose no audience demographics (only TikTok Business/Studio
    does), so real posts return {} and callers fall back to the profile's age group.
    """
    if not settings.tiktok_configured or not user.tiktok_access_token or external_id.startswith("mock-"):
        return mock_audience(external_id)
    return {}


def mock_audience(external_id: str) -> dict[str, float]:
    h = int(hashlib.sha1(("aud" + external_id).encode()).hexdigest(), 16)
    weights = [1 + (h >> (8 * i)) % 10 for i in range(len(AUDIENCE_GROUPS))]
    total = sum(weights)
    return {g: round(w / total, 2) for g, w in zip(AUDIENCE_GROUPS, weights)}


def mock_metrics(external_id: str) -> dict:
    h = int(hashlib.sha1(external_id.encode()).hexdigest(), 16)
    views = 500 + h % 50000
    return {
        "views": views,
        "likes": int(views * (0.03 + (h >> 8) % 10 / 100)),
        "comments": int(views * (0.002 + (h >> 16) % 5 / 1000)),
        "shares": int(views * (0.004 + (h >> 24) % 5 / 1000)),
        "avg_watch_seconds": round(3 + (h >> 32) % 120 / 10, 1),
        "completion_rate": round(0.15 + (h >> 40) % 60 / 100, 2),
    }
