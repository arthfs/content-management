from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import besttime
from app.db import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return TestClient(app)


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


def test_best_slots_timezone():
    now = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    slots = besttime.upcoming_slots("America/New_York", "18-24", 2, 2, now=now)
    assert [s.hour for s in slots] == [2, 17]  # 21:00 then 12:00 EST in UTC
