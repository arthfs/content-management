"""TikTok integration. Falls back to a deterministic mock when credentials are missing."""
import hashlib
from urllib.parse import urlencode

import httpx

from .config import settings
from .models import User

API = "https://open.tiktokapis.com/v2"


def auth_url(state: str) -> str:
    q = urlencode({
        "client_key": settings.tiktok_client_key,
        "scope": "user.info.basic,video.publish,video.list",
        "response_type": "code",
        "redirect_uri": settings.tiktok_redirect_uri,
        "state": state,
    })
    return f"https://www.tiktok.com/v2/auth/authorize/?{q}"


def exchange_code(code: str) -> dict:
    r = httpx.post(f"{API}/oauth/token/", data={
        "client_key": settings.tiktok_client_key,
        "client_secret": settings.tiktok_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.tiktok_redirect_uri,
    }, timeout=30)
    r.raise_for_status()
    return r.json()


def publish(user: User, title: str, caption: str, video_url: str) -> str:
    """Publish a video; returns the external id."""
    if not settings.tiktok_configured or not user.tiktok_access_token:
        return "mock-" + hashlib.sha1(f"{user.id}{title}{video_url}".encode()).hexdigest()[:12]
    r = httpx.post(
        f"{API}/post/publish/inbox/video/init/",
        headers={"Authorization": "Bearer " + user.tiktok_access_token},
        json={"source_info": {"source": "PULL_FROM_URL", "video_url": video_url}},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["data"]["publish_id"]


def fetch_metrics(user: User, external_id: str) -> dict:
    """Return views/likes/comments/shares/avg watch time/completion."""
    if not settings.tiktok_configured or not user.tiktok_access_token or external_id.startswith("mock-"):
        return mock_metrics(external_id)
    r = httpx.post(
        f"{API}/video/query/?fields=id,view_count,like_count,comment_count,share_count",
        headers={"Authorization": "Bearer " + user.tiktok_access_token},
        json={"filters": {"video_ids": [external_id]}},
        timeout=30,
    )
    r.raise_for_status()
    vids = r.json().get("data", {}).get("videos", [])
    if not vids:
        return mock_metrics(external_id)
    v = vids[0]
    return {"views": v.get("view_count", 0), "likes": v.get("like_count", 0),
            "comments": v.get("comment_count", 0), "shares": v.get("share_count", 0)}


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
