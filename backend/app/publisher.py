from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from . import storage, tiktok
from .models import Post, User, Video


def _fail(db: Session, video: Video, reason: str) -> Video:
    video.status = "failed"
    video.publish_status = "FAILED"
    video.fail_reason = reason[:255]
    db.commit()
    return video


def publish_video(db: Session, user: User, video: Video, options: dict | None = None) -> Video:
    options = options or video.publish_options
    if tiktok.is_live(user) and not options:
        return _fail(db, video, "Choose the post settings (privacy, interactions) and confirm before posting.")
    try:
        if tiktok.ensure_fresh_token(user):
            db.commit()
        caption = f"{video.caption} {video.hashtags}".strip() or video.title
        ext = tiktok.publish(user, caption, video.video_url, storage.path_of(video.file_path), options)
    except tiktok.TikTokError as e:
        return _fail(db, video, str(e))
    except httpx.HTTPError:
        return _fail(db, video, "Couldn't reach TikTok. Try again in a moment.")
    post = Post(video_id=video.id, platform="tiktok", external_id=ext, posted_at=datetime.now(timezone.utc))
    post.metrics = tiktok.fetch_metrics(user, ext)
    db.add(post)
    video.status = "posted"
    video.publish_options = options
    video.publish_status = "PROCESSING_UPLOAD" if tiktok.is_live(user) else "PUBLISH_COMPLETE"
    video.fail_reason = None
    db.commit()
    db.refresh(video)
    return video


def refresh_status(db: Session, user: User, video: Video) -> Video:
    """Poll TikTok's publish status for the video's latest post and keep the final post id when public."""
    post = max(video.posts, key=lambda p: p.posted_at, default=None)
    if post is None or video.publish_status in ("PUBLISH_COMPLETE", "FAILED"):
        return video
    try:
        if tiktok.ensure_fresh_token(user):
            db.commit()
        st = tiktok.fetch_publish_status(user, post.external_id)
    except (tiktok.TikTokError, httpx.HTTPError):
        return video
    video.publish_status = st["status"] or video.publish_status
    if st["status"] == "FAILED":
        video.status = "failed"
        video.fail_reason = (st["fail_reason"] or "TikTok couldn't process the video")[:255]
    if st["post_id"]:
        post.external_id = st["post_id"]
    db.commit()
    db.refresh(video)
    return video


def publish_due(db: Session) -> int:
    now = datetime.now(timezone.utc)
    due = db.query(Video).filter(Video.status == "scheduled", Video.scheduled_at <= now).all()
    for v in due:
        publish_video(db, v.user, v)
    return len(due)
