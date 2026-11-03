from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    # profile used for best-time computation
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    country: Mapped[str] = mapped_column(String(64), default="")
    audience_age: Mapped[str] = mapped_column(String(16), default="18-24")
    posts_per_day: Mapped[int] = mapped_column(Integer, default=2)
    tiktok_access_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tiktok_open_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    videos: Mapped[list["Video"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Video(Base):
    __tablename__ = "videos"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    caption: Mapped[str] = mapped_column(Text, default="")
    hashtags: Mapped[str] = mapped_column(String(500), default="")
    video_url: Mapped[str] = mapped_column(String(1000), default="")
    # draft | scheduled | posted | failed
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user: Mapped[User] = relationship(back_populates="videos")
    posts: Mapped[list["Post"]] = relationship(back_populates="video", cascade="all, delete-orphan")


class Post(Base):
    """A video published to one platform."""

    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), index=True)
    platform: Mapped[str] = mapped_column(String(16), default="tiktok")
    external_id: Mapped[str] = mapped_column(String(128), default="")
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    video: Mapped[Video] = relationship(back_populates="posts")
