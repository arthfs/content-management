from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(default="", max_length=100)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileIn(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    timezone: str | None = None
    country: str | None = Field(default=None, max_length=64)
    audience_age: str | None = Field(default=None, pattern=r"^(13-17|18-24|25-34|35\+)$")
    posts_per_day: int | None = Field(default=None, ge=1, le=6)


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    timezone: str
    country: str
    audience_age: str
    posts_per_day: int
    tiktok_connected: bool = False


class VideoIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    caption: str = Field(default="", max_length=2200)
    hashtags: str = Field(default="", max_length=500)
    video_url: str = Field(default="", max_length=1000)


class VideoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    caption: str | None = Field(default=None, max_length=2200)
    hashtags: str | None = Field(default=None, max_length=500)
    video_url: str | None = Field(default=None, max_length=1000)


class PublishOptions(BaseModel):
    """What the user chose in the 'Post to TikTok' panel (TikTok content sharing guidelines)."""
    privacy_level: str = ""  # must be one of creator_info.privacy_level_options; no default
    allow_comment: bool = False
    allow_duet: bool = False
    allow_stitch: bool = False
    commercial_content: bool = False
    brand_organic: bool = False  # "Your brand" -> labeled Promotional content
    brand_content: bool = False  # "Branded content" -> labeled Paid partnership
    consent: bool = False  # user agreed to TikTok's Music Usage Confirmation (and Branded Content Policy)


class ScheduleIn(BaseModel):
    scheduled_at: datetime | None = None  # None -> next best slot
    options: PublishOptions | None = None


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    platform: str
    external_id: str
    posted_at: datetime
    metrics: dict


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    caption: str
    hashtags: str
    video_url: str
    has_file: bool = False
    status: str
    publish_status: str | None = None
    fail_reason: str | None = None
    scheduled_at: datetime | None
    created_at: datetime
    posts: list[PostOut] = []
