import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("configured_origin", ["http://frontend.example", "http://frontend.example/"])
def test_registration_preflight_allows_configured_and_local_origins(configured_origin):
    env = os.environ.copy()
    env["FRONTEND_ORIGIN"] = configured_origin
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
headers = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}
response = client.options("/api/auth/register", headers={**headers, "Origin": "http://frontend.example"})
assert response.status_code == 200
assert response.headers["access-control-allow-origin"] == "http://frontend.example"
response = client.options("/api/auth/register", headers={**headers, "Origin": "http://localhost:3000"})
assert response.status_code == 200
assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
response = client.options("/api/auth/register", headers={**headers, "Origin": "http://other.example"})
assert response.status_code == 400
response = client.options("/api/auth/register", headers={**headers, "Origin": "http://localhost:3001"})
assert response.status_code == 400
""",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
