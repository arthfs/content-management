import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, UploadFile
import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import besttime, insights, storage, tiktok
from .config import settings
from .db import Base, SessionLocal, engine, ensure_columns, get_db
from .models import Post, User, Video
from .publisher import publish_due, publish_video, refresh_status
from .schemas import (ProfileIn, ProfileOut, PublishOptions, RegisterIn, ScheduleIn, TokenOut, VideoIn, VideoOut,
                      VideoUpdate)
from .security import (create_oauth_state, create_token, current_user, default_user, hash_password,
                       verify_oauth_state, verify_password)


async def _scheduler_loop():
    while True:
        await asyncio.sleep(60)
        db = SessionLocal()
        try:
            await asyncio.to_thread(publish_due, db)
        finally:
            db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    ensure_columns(engine)
    if not settings.auth_required:
        with SessionLocal() as db:
            default_user(db)
    task = asyncio.create_task(_scheduler_loop())
    yield
    task.cancel()


app = FastAPI(title="Content Manager API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin.rstrip("/"), "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def profile_out(u: User) -> ProfileOut:
    out = ProfileOut.model_validate(u)
    out.tiktok_connected = bool(u.tiktok_access_token)
    return out


def audience_for(db: Session, user: User) -> tuple[str, str]:
    """Age group to target, from the audience of the user's most recent post.

    Returns (age_group, source) where source is "latest_post" or "profile" (fallback).
    """
    post = (db.query(Post).join(Video).filter(Video.user_id == user.id)
            .order_by(Post.posted_at.desc()).first())
    if post:
        try:
            shares = tiktok.fetch_audience(user, post.external_id)
        except Exception:
            shares = {}
        if shares:
            return max(shares, key=shares.get), "latest_post"
    return user.audience_age, "profile"


def get_video(db: Session, user: User, video_id: int) -> Video:
    v = db.get(Video, video_id)
    if v is None or v.user_id != user.id:
        raise HTTPException(404, "Video not found")
    return v


def require_media(user: User, v: Video) -> None:
    """With a real TikTok connection a post needs a video; mock mode doesn't."""
    if settings.tiktok_configured and user.tiktok_access_token and not (storage.path_of(v.file_path) or v.video_url):
        raise HTTPException(400, "Upload a video file before posting or scheduling")


# ---- auth ----
@app.post("/api/auth/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "Email already registered")
    user = User(email=email, name=data.name, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    return TokenOut(access_token=create_token(user.id))


@app.post("/api/auth/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return TokenOut(access_token=create_token(user.id))


@app.get("/api/me", response_model=ProfileOut)
def me(user: User = Depends(current_user)):
    return profile_out(user)


@app.patch("/api/me", response_model=ProfileOut)
def update_me(data: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(user, k, v)
    db.commit()
    return profile_out(user)


# ---- TikTok connection ----
@app.get("/api/tiktok/status")
def tiktok_status(user: User = Depends(current_user)):
    return {"configured": settings.tiktok_configured, "connected": bool(user.tiktok_access_token),
            "mock_mode": not settings.tiktok_configured}


@app.get("/api/tiktok/auth-url")
def tiktok_auth_url(user: User = Depends(current_user)):
    if not settings.tiktok_configured:
        raise HTTPException(400, "TikTok credentials not configured (running in mock mode)")
    return {"url": tiktok.auth_url(create_oauth_state(user.id))}


@app.post("/api/tiktok/callback")
def tiktok_callback(code: str, state: str = "", user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not settings.tiktok_configured:
        raise HTTPException(400, "TikTok credentials not configured")
    if not verify_oauth_state(state, user.id):
        raise HTTPException(400, "Invalid or expired TikTok authorization state. Start the connection again.")
    try:
        data = tiktok.exchange_code(code)
    except (tiktok.TikTokError, httpx.HTTPError) as e:
        raise HTTPException(400, f"TikTok authorization failed: {e}")
    tiktok.store_tokens(user, data)
    db.commit()
    return {"connected": True}


@app.get("/api/tiktok/creator-info")
def tiktok_creator_info(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Fetched fresh each time the 'Post to TikTok' panel opens (required by TikTok's UX guidelines)."""
    try:
        if tiktok.ensure_fresh_token(user):
            db.commit()
        return tiktok.query_creator_info(user)
    except tiktok.TikTokError as e:
        raise HTTPException(400, str(e))
    except httpx.HTTPError:
        raise HTTPException(502, "Couldn't reach TikTok")


def checked_options(user: User, options: PublishOptions | None) -> dict | None:
    """Validate the user's post settings against live creator info; None in mock mode without settings."""
    if options is None:
        if tiktok.is_live(user):
            raise HTTPException(400, "Post settings are required (privacy, interactions, consent)")
        return None
    opts = options.model_dump()
    try:
        tiktok.validate_options(opts, tiktok.query_creator_info(user))
    except tiktok.TikTokError as e:
        raise HTTPException(400, str(e))
    except httpx.HTTPError:
        raise HTTPException(502, "Couldn't reach TikTok")
    return opts


# ---- best times ----
@app.get("/api/schedule/best-times")
def best_times(days: int = 3, user: User = Depends(current_user), db: Session = Depends(get_db)):
    days = max(1, min(days, 14))
    age, source = audience_for(db, user)
    slots = besttime.upcoming_slots(user.timezone, age, user.posts_per_day, days * user.posts_per_day)
    zone = besttime.get_zone(user.timezone)
    return {
        "timezone": user.timezone,
        "audience_age": age,
        "audience_source": source,
        "local_hours": besttime.best_hours(age, user.posts_per_day),
        "slots": [{"utc": s.isoformat(), "local": s.astimezone(zone).isoformat()} for s in slots],
    }


# ---- videos ----
@app.post("/api/videos", response_model=VideoOut, status_code=201)
def create_video(data: VideoIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    v = Video(user_id=user.id, **data.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@app.get("/api/videos", response_model=list[VideoOut])
def list_videos(status: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = db.query(Video).filter(Video.user_id == user.id)
    if status:
        q = q.filter(Video.status == status)
    return q.order_by(Video.created_at.desc()).all()


@app.get("/api/videos/{video_id}", response_model=VideoOut)
def read_video(video_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return get_video(db, user, video_id)


@app.patch("/api/videos/{video_id}", response_model=VideoOut)
def update_video(video_id: int, data: VideoUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    v = get_video(db, user, video_id)
    if v.status == "posted":
        raise HTTPException(400, "Posted videos cannot be edited")
    for k, val in data.model_dump(exclude_none=True).items():
        setattr(v, k, val)
    db.commit()
    return v


@app.delete("/api/videos/{video_id}", status_code=204)
def delete_video(video_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    v = get_video(db, user, video_id)
    storage.delete(v.file_path)
    db.delete(v)
    db.commit()


@app.post("/api/videos/{video_id}/file", response_model=VideoOut)
def upload_video_file(video_id: int, file: UploadFile, user: User = Depends(current_user),
                      db: Session = Depends(get_db)):
    v = get_video(db, user, video_id)
    if v.status == "posted":
        raise HTTPException(400, "Posted videos cannot be edited")
    name = storage.save_upload(file)
    storage.delete(v.file_path)
    v.file_path = name
    db.commit()
    return v


@app.post("/api/videos/{video_id}/schedule", response_model=VideoOut)
def schedule_video(video_id: int, data: ScheduleIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    v = get_video(db, user, video_id)
    if v.status == "posted":
        raise HTTPException(400, "Video already posted")
    require_media(user, v)
    opts = checked_options(user, data.options)
    if opts:
        v.publish_options = opts
    when = data.scheduled_at
    if when is None:
        age, _ = audience_for(db, user)
        taken = {x.scheduled_at.replace(tzinfo=timezone.utc) for x in
                 db.query(Video).filter(Video.user_id == user.id, Video.status == "scheduled", Video.id != v.id)
                 if x.scheduled_at}
        slots = besttime.upcoming_slots(user.timezone, age, user.posts_per_day,
                                        (len(taken) + 1) * 1 + 1)
        when = next((s for s in slots if s not in taken), None)
        n = len(slots)
        while when is None:  # all candidate slots taken; look further ahead
            n *= 2
            slots = besttime.upcoming_slots(user.timezone, age, user.posts_per_day, n)
            when = next((s for s in slots if s not in taken), None)
    elif when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    v.scheduled_at = when
    v.status = "scheduled"
    db.commit()
    return v


@app.post("/api/videos/{video_id}/publish", response_model=VideoOut)
def publish_now(video_id: int, options: PublishOptions | None = None, user: User = Depends(current_user),
                db: Session = Depends(get_db)):
    v = get_video(db, user, video_id)
    if v.status == "posted":
        raise HTTPException(400, "Video already posted")
    require_media(user, v)
    return publish_video(db, user, v, checked_options(user, options))


@app.get("/api/videos/{video_id}/publish-status", response_model=VideoOut)
def publish_status(video_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Poll TikTok for processing/moderation status of the video's latest post."""
    return refresh_status(db, user, get_video(db, user, video_id))


# ---- analytics ----
@app.get("/api/videos/{video_id}/analytics")
def video_analytics(video_id: int, platform: str = "tiktok", user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    v = get_video(db, user, video_id)
    post = next((p for p in v.posts if p.platform == platform), None)
    if post is None:
        raise HTTPException(404, f"Video has not been posted to {platform}")
    post.metrics = tiktok.fetch_metrics(user, post.external_id)
    db.commit()
    m = post.metrics
    tips, source = insights.gemini_suggestions(v.title, v.caption, platform, m)
    return {"video_id": v.id, "title": v.title, "platform": platform, "posted_at": post.posted_at,
            "metrics": m, "engagement_rate": insights.engagement_rate(m),
            "audience": tiktok.fetch_audience(user, post.external_id),
            "suggestions": tips, "suggestions_source": source}


@app.get("/api/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    videos = db.query(Video).filter(Video.user_id == user.id).all()
    counts = {s: 0 for s in ("draft", "scheduled", "posted", "failed")}
    totals = {"views": 0, "likes": 0, "comments": 0, "shares": 0}
    top = []
    for v in videos:
        counts[v.status] = counts.get(v.status, 0) + 1
        for p in v.posts:
            for k in totals:
                totals[k] += p.metrics.get(k, 0)
            top.append({"video_id": v.id, "title": v.title, "platform": p.platform,
                        "views": p.metrics.get("views", 0),
                        "engagement_rate": insights.engagement_rate(p.metrics)})
    top.sort(key=lambda x: x["views"], reverse=True)
    upcoming = sorted((v for v in videos if v.status == "scheduled" and v.scheduled_at),
                      key=lambda v: v.scheduled_at)[:5]
    today = datetime.now(timezone.utc).date()
    posted_today = sum(1 for v in videos for p in v.posts if p.posted_at.date() == today)
    return {
        "counts": counts, "totals": totals, "top_videos": top[:5],
        "upcoming": [{"id": v.id, "title": v.title, "scheduled_at": v.scheduled_at} for v in upcoming],
        "posted_today": posted_today, "daily_goal": user.posts_per_day,
        "platforms": {"tiktok": True, "instagram": False, "youtube_shorts": False},
    }
