from datetime import datetime, timezone

from sqlalchemy.orm import Session

from . import tiktok
from .models import Post, User, Video


def publish_video(db: Session, user: User, video: Video) -> Video:
    try:
        ext = tiktok.publish(user, video.title, f"{video.caption} {video.hashtags}".strip(), video.video_url)
    except Exception:
        video.status = "failed"
        db.commit()
        return video
    post = Post(video_id=video.id, platform="tiktok", external_id=ext, posted_at=datetime.now(timezone.utc))
    post.metrics = tiktok.fetch_metrics(user, ext)
    db.add(post)
    video.status = "posted"
    db.commit()
    db.refresh(video)
    return video


def publish_due(db: Session) -> int:
    now = datetime.now(timezone.utc)
    due = db.query(Video).filter(Video.status == "scheduled", Video.scheduled_at <= now).all()
    for v in due:
        publish_video(db, v.user, v)
    return len(due)
