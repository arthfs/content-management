import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app import besttime
from app.config import Settings, settings
from app.db import Base, get_db
from app.main import app
import app.main as main


@pytest.mark.parametrize(
    "database_url",
    [
        "postgres://user:password@localhost:5432/content_manager",
        "postgresql://user:password@localhost:5432/content_manager",
        "postgresql+psycopg://user:password@localhost:5432/content_manager",
    ],
)
def test_postgres_urls_use_psycopg(database_url):
    assert (
        Settings(database_url=database_url).sqlalchemy_database_url.drivername
        == "postgresql+psycopg"
    )


def test_mysql_database_url_is_rejected():
    with pytest.raises(ValueError, match="DATABASE_URL must use PostgreSQL"):
        Settings(
            database_url="mysql+pymysql://user:password@localhost/content_manager"
        ).sqlalchemy_database_url


@pytest.fixture(scope="session")
def test_engine():
    """Use a dedicated PostgreSQL database; the fixture drops its tables."""
    test_database_url = os.getenv("TEST_DATABASE_URL") or settings.test_database_url
    if not test_database_url:
        pytest.fail("Set TEST_DATABASE_URL to a dedicated PostgreSQL test database.")

    url = make_url(test_database_url)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")
    if url.get_backend_name() != "postgresql":
        pytest.fail("TEST_DATABASE_URL must point to PostgreSQL.")

    app_url = settings.sqlalchemy_database_url
    if (url.host, url.port, url.database) == (app_url.host, app_url.port, app_url.database):
        pytest.fail("TEST_DATABASE_URL must not point to the application database.")

    engine = create_engine(url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture()
def client(monkeypatch, test_engine, tmp_path):
    monkeypatch.setattr(settings, "auth_required", True)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False)
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(main, "engine", test_engine)
    monkeypatch.setattr(main, "SessionLocal", TestSessionLocal)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def auth(client, email="a@b.com"):
    r = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert r.status_code == 201
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def test_auth_flow(client):
    auth(client)
    assert client.post("/api/auth/register", json={"email": "a@b.com", "password": "password123"}).status_code == 409
    ok = client.post("/api/auth/login", data={"username": "a@b.com", "password": "password123"})
    assert ok.status_code == 200
    assert client.post("/api/auth/login", data={"username": "a@b.com", "password": "wrong"}).status_code == 401
    assert client.get("/api/me").status_code == 401


def test_video_lifecycle_and_analytics(client):
    h = auth(client)
    vid = client.post("/api/videos", json={"title": "Hi", "video_url": "https://x/y.mp4"}, headers=h).json()
    s = client.post(f"/api/videos/{vid['id']}/schedule", json={}, headers=h).json()
    assert s["status"] == "scheduled" and s["scheduled_at"]
    assert client.get(f"/api/videos/{vid['id']}/analytics", headers=h).status_code == 404
    p = client.post(f"/api/videos/{vid['id']}/publish", headers=h).json()
    assert p["status"] == "posted"
    a = client.get(f"/api/videos/{vid['id']}/analytics", headers=h).json()
    assert a["metrics"]["views"] > 0 and a["suggestions"]
    d = client.get("/api/dashboard", headers=h).json()
    assert d["counts"]["posted"] == 1 and d["posted_today"] == 1


def test_isolation_between_users(client):
    h1, h2 = auth(client, "one@x.com"), auth(client, "two@x.com")
    vid = client.post("/api/videos", json={"title": "Mine"}, headers=h1).json()
    assert client.get(f"/api/videos/{vid['id']}", headers=h2).status_code == 404


def test_unique_auto_slots(client):
    h = auth(client)
    times = set()
    for i in range(5):
        v = client.post("/api/videos", json={"title": str(i)}, headers=h).json()
        times.add(client.post(f"/api/videos/{v['id']}/schedule", json={}, headers=h).json()["scheduled_at"])
    assert len(times) == 5


def test_single_user_mode_without_login(client, monkeypatch):
    monkeypatch.setattr(settings, "auth_required", False)
    assert client.get("/api/me").json()["email"] == settings.default_user_email
    vid = client.post("/api/videos", json={"title": "Solo"}).json()
    assert client.get(f"/api/videos/{vid['id']}").status_code == 200


def test_best_times_use_latest_post_audience(client):
    h = auth(client)
    first = client.get("/api/schedule/best-times", headers=h).json()
    assert first["audience_source"] == "profile" and first["audience_age"] == "18-24"
    vid = client.post("/api/videos", json={"title": "Hi"}, headers=h).json()
    client.post(f"/api/videos/{vid['id']}/publish", headers=h)
    after = client.get("/api/schedule/best-times", headers=h).json()
    assert after["audience_source"] == "latest_post"
    audience = client.get(f"/api/videos/{vid['id']}/analytics", headers=h).json()["audience"]
    assert after["audience_age"] == max(audience, key=audience.get)


def test_file_upload_and_direct_post(client, tmp_path):
    h = auth(client)
    vid = client.post("/api/videos", json={"title": "Upload me"}, headers=h).json()
    assert vid["has_file"] is False
    bad = client.post(f"/api/videos/{vid['id']}/file", files={"file": ("x.exe", b"abc")}, headers=h)
    assert bad.status_code == 400
    ok = client.post(f"/api/videos/{vid['id']}/file", files={"file": ("clip.mp4", b"\x00" * 2048, "video/mp4")},
                     headers=h)
    assert ok.status_code == 200 and ok.json()["has_file"] is True
    stored = list((tmp_path / "uploads").iterdir())
    assert len(stored) == 1
    assert client.post(f"/api/videos/{vid['id']}/publish", headers=h).json()["status"] == "posted"
    other = client.post("/api/videos", json={"title": "Other"}, headers=h).json()
    client.post(f"/api/videos/{other['id']}/file", files={"file": ("b.mp4", b"1234")}, headers=h)
    assert len(list((tmp_path / "uploads").iterdir())) == 2
    assert client.delete(f"/api/videos/{other['id']}", headers=h).status_code == 204
    assert len(list((tmp_path / "uploads").iterdir())) == 1


def test_upload_isolated_and_size_limited(client, monkeypatch):
    h1, h2 = auth(client, "one@x.com"), auth(client, "two@x.com")
    vid = client.post("/api/videos", json={"title": "Mine"}, headers=h1).json()
    assert client.post(f"/api/videos/{vid['id']}/file", files={"file": ("a.mp4", b"1234")}, headers=h2).status_code == 404
    monkeypatch.setattr(settings, "max_upload_mb", 0)
    big = client.post(f"/api/videos/{vid['id']}/file", files={"file": ("a.mp4", b"1234")}, headers=h1)
    assert big.status_code == 413


CREATOR = {"creator_nickname": "Nick", "privacy_level_options": ["SELF_ONLY"], "comment_disabled": False,
           "duet_disabled": True, "stitch_disabled": False, "max_video_post_duration_sec": 600}
OPTIONS = {"privacy_level": "SELF_ONLY", "allow_comment": True, "allow_duet": True, "allow_stitch": False,
           "consent": True}


@pytest.fixture()
def fake_tiktok(monkeypatch):
    """Live-mode TikTok with the HTTP layer mocked; records every request."""
    from app import tiktok

    monkeypatch.setattr(settings, "tiktok_client_key", "k")
    monkeypatch.setattr(settings, "tiktok_client_secret", "s")
    rec = {"init": None, "puts": [], "urls": []}

    class Resp:
        def __init__(self, data=None):
            self._d = data or {}

        def raise_for_status(self):
            pass

        def json(self):
            return {"data": self._d, "error": {"code": "ok", "message": ""}}

    def fake_post(url, **kw):
        rec["urls"].append(url)
        if url.endswith("/creator_info/query/"):
            return Resp(CREATOR)
        if url.endswith("/video/init/"):
            rec["init"] = kw["json"]
            return Resp({"publish_id": "pub1", "upload_url": "https://upload.example/x"})
        if url.endswith("/status/fetch/"):
            return Resp({"status": "PUBLISH_COMPLETE", "publicaly_available_post_id": [1234]})
        raise AssertionError(url)

    def fake_put(url, content, headers, **kw):
        rec["puts"].append((len(content), headers["Content-Range"]))
        return Resp()

    monkeypatch.setattr(tiktok.httpx, "post", fake_post)
    monkeypatch.setattr(tiktok.httpx, "put", fake_put)
    return rec


def test_tiktok_direct_post_chunking_and_options(fake_tiktok, tmp_path):
    from app import tiktok
    from app.models import User

    size = 25 * 1024 * 1024 + 123
    f = tmp_path / "big.mp4"
    f.write_bytes(b"\x01" * size)
    user = User(id=1, email="a@b.c", password_hash="x", tiktok_access_token="tok")
    assert tiktok.publish(user, "cap", "", f, OPTIONS) == "pub1"
    assert fake_tiktok["urls"][0].endswith("/creator_info/query/")  # creator info is fetched before init
    init = fake_tiktok["init"]
    src = init["source_info"]
    assert src["source"] == "FILE_UPLOAD" and src["video_size"] == size and src["total_chunk_count"] == 2
    assert [p[0] for p in fake_tiktok["puts"]] == [10 * 1024 * 1024, size - 10 * 1024 * 1024]
    assert fake_tiktok["puts"][-1][1] == f"bytes {10 * 1024 * 1024}-{size - 1}/{size}"
    info = init["post_info"]
    assert info["privacy_level"] == "SELF_ONLY" and info["title"] == "cap"
    assert info["disable_comment"] is False
    assert info["disable_duet"] is True  # creator disabled duets, even though the user ticked it
    assert info["disable_stitch"] is True  # unticked -> off


def test_tiktok_option_validation():
    from app import tiktok

    with pytest.raises(tiktok.TikTokError, match="privacy"):
        tiktok.validate_options({**OPTIONS, "privacy_level": "PUBLIC_TO_EVERYONE"}, CREATOR)
    with pytest.raises(tiktok.TikTokError):
        tiktok.validate_options({**OPTIONS, "consent": False}, CREATOR)
    with pytest.raises(tiktok.TikTokError, match="promotes"):
        tiktok.validate_options({**OPTIONS, "commercial_content": True}, CREATOR)
    with pytest.raises(tiktok.TikTokError, match="private"):
        tiktok.validate_options({**OPTIONS, "commercial_content": True, "brand_content": True}, CREATOR)


def test_tiktok_publish_flow_via_api(client, fake_tiktok, tmp_path):
    from app.models import User

    h = auth(client)
    with next(client.app.dependency_overrides[get_db]()) as db:
        db.query(User).update({"tiktok_access_token": "tok"})
        db.commit()
    assert client.get("/api/tiktok/creator-info", headers=h).json()["creator_nickname"] == "Nick"
    vid = client.post("/api/videos", json={"title": "V"}, headers=h).json()
    client.post(f"/api/videos/{vid['id']}/file", files={"file": ("a.mp4", b"1234")}, headers=h)
    assert client.post(f"/api/videos/{vid['id']}/publish", headers=h).status_code == 400  # settings required
    bad = client.post(f"/api/videos/{vid['id']}/publish", json={**OPTIONS, "privacy_level": "PUBLIC_TO_EVERYONE"},
                      headers=h)
    assert bad.status_code == 400
    ok = client.post(f"/api/videos/{vid['id']}/publish", json=OPTIONS, headers=h).json()
    assert ok["status"] == "posted" and ok["publish_status"] == "PROCESSING_UPLOAD"
    done = client.get(f"/api/videos/{vid['id']}/publish-status", headers=h).json()
    assert done["publish_status"] == "PUBLISH_COMPLETE"
    assert done["posts"][0]["external_id"] == "1234"  # public post id replaces the publish_id


def test_oauth_state_is_verified(client, fake_tiktok):
    from app.security import create_oauth_state

    h = auth(client)
    assert client.post("/api/tiktok/callback?code=x&state=forged", headers=h).status_code == 400
    assert create_oauth_state(1) != create_oauth_state(1)


def test_token_refresh_rotates_refresh_token(monkeypatch):
    from datetime import timedelta
    from app import tiktok
    from app.models import User

    monkeypatch.setattr(settings, "tiktok_client_key", "k")
    monkeypatch.setattr(settings, "tiktok_client_secret", "s")
    seen = {}

    class Resp:
        def json(self):
            return {"access_token": "new", "refresh_token": "rft2", "expires_in": 7200}

    def fake_post(url, data, **kw):
        seen.update(data)
        return Resp()

    monkeypatch.setattr(tiktok.httpx, "post", fake_post)
    user = User(id=1, email="a@b.c", password_hash="x", tiktok_access_token="old", tiktok_refresh_token="rft1",
                tiktok_token_expires_at=datetime.now(timezone.utc) + timedelta(minutes=1))
    assert tiktok.ensure_fresh_token(user)
    assert seen["grant_type"] == "refresh_token" and seen["refresh_token"] == "rft1"
    assert user.tiktok_access_token == "new" and user.tiktok_refresh_token == "rft2"

def test_real_tiktok_requires_media(client, monkeypatch):
    from app.models import User

    h = auth(client)
    monkeypatch.setattr(settings, "tiktok_client_key", "k")
    monkeypatch.setattr(settings, "tiktok_client_secret", "s")
    with next(client.app.dependency_overrides[get_db]()) as db:
        db.query(User).update({"tiktok_access_token": "tok"})
        db.commit()
    vid = client.post("/api/videos", json={"title": "No file"}, headers=h).json()
    assert client.post(f"/api/videos/{vid['id']}/publish", json=OPTIONS, headers=h).status_code == 400
    assert client.post(f"/api/videos/{vid['id']}/schedule", json={}, headers=h).status_code == 400


def test_best_slots_timezone():
    now = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    slots = besttime.upcoming_slots("America/New_York", "18-24", 2, 2, now=now)
    assert [s.hour for s in slots] == [2, 17]  # 21:00 then 12:00 EST in UTC
