import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import besttime, insights, tiktok
from .config import settings
from .db import Base, SessionLocal, engine, get_db
from .models import User, Video
from .publisher import publish_due, publish_video
from .schemas import (ProfileIn, ProfileOut, RegisterIn, ScheduleIn, TokenOut, VideoIn, VideoOut,
                      VideoUpdate)
from .security import create_token, current_user, hash_password, verify_password


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
    task = asyncio.create_task(_scheduler_loop())
    yield
    task.cancel()


app = FastAPI(title="Content Manager API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)


def profile_out(u: User) -> ProfileOut:
    out = ProfileOut.model_validate(u)
    out.tiktok_connected = bool(u.tiktok_access_token)
    return out


def get_video(db: Session, user: User, video_id: int) -> Video:
    v = db.get(Video, video_id)
    if v is None or v.user_id != user.id:
        raise HTTPException(404, "Video not found")
    return v


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
    return {"url": tiktok.auth_url(str(user.id))}


@app.post("/api/tiktok/callback")
def tiktok_callback(code: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not settings.tiktok_configured:
        raise HTTPException(400, "TikTok credentials not configured")
    data = tiktok.exchange_code(code)
    if "access_token" not in data:
        raise HTTPException(400, "TikTok authorization failed")
    user.tiktok_access_token = data["access_token"]
    user.tiktok_open_id = data.get("open_id")
    db.commit()
    return {"connected": True}


# ---- best times ----
@app.get("/api/schedule/best-times")
def best_times(days: int = 3, user: User = Depends(current_user)):
    days = max(1, min(days, 14))
    slots = besttime.upcoming_slots(user.timezone, user.audience_age, user.posts_per_day, days * user.posts_per_day)
    zone = besttime.get_zone(user.timezone)
    return {
        "timezone": user.timezone,
        "local_hours": besttime.best_hours(user.audience_age, user.posts_per_day),
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
    db.delete(get_video(db, user, video_id))
    db.commit()


@app.post("/api/videos/{video_id}/schedule", response_model=VideoOut)
def schedule_video(video_id: int, data: ScheduleIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    v = get_video(db, user, video_id)
    if v.status == "posted":
        raise HTTPException(400, "Video already posted")
    when = data.scheduled_at
    if when is None:
        taken = {x.scheduled_at.replace(tzinfo=timezone.utc) for x in
                 db.query(Video).filter(Video.user_id == user.id, Video.status == "scheduled", Video.id != v.id)
                 if x.scheduled_at}
        slots = besttime.upcoming_slots(user.timezone, user.audience_age, user.posts_per_day,
                                        (len(taken) + 1) * 1 + 1)
        when = next((s for s in slots if s not in taken), None)
        n = len(slots)
        while when is None:  # all candidate slots taken; look further ahead
            n *= 2
            slots = besttime.upcoming_slots(user.timezone, user.audience_age, user.posts_per_day, n)
            when = next((s for s in slots if s not in taken), None)
    elif when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    v.scheduled_at = when
    v.status = "scheduled"
    db.commit()
    return v


@app.post("/api/videos/{video_id}/publish", response_model=VideoOut)
def publish_now(video_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    v = get_video(db, user, video_id)
    if v.status == "posted":
        raise HTTPException(400, "Video already posted")
    return publish_video(db, user, v)


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
