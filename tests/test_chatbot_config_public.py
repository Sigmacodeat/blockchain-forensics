import json
import os
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app

DATA_FILE = Path("data/chatbot_config.json")

client = TestClient(app)

def test_public_config_returns_defaults_and_cache_headers():
    # Ensure seed file exists
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps({"enabled": True}, indent=2))

    r1 = client.get("/api/v1/admin/chatbot-config/public")
    assert r1.status_code == 200
    assert r1.headers.get("ETag") is not None
    assert "Cache-Control" in r1.headers
    body1 = r1.json()
    # expected keys (subset)
    assert "enabled" in body1
    assert "primaryColor" in body1

    # Second request with If-None-Match should 304
    etag = r1.headers["ETag"]
    r2 = client.get("/api/v1/admin/chatbot-config/public", headers={"If-None-Match": etag})
    assert r2.status_code == 304


def test_public_config_etag_changes_on_update(tmp_path):
    # read current etag
    r1 = client.get("/api/v1/admin/chatbot-config/public")
    assert r1.status_code == 200
    etag1 = r1.headers["ETag"]

    # update file (toggle a flag)
    data = json.loads(r1.text)
    data["showVoiceInput"] = not data.get("showVoiceInput", True)
    DATA_FILE.write_text(json.dumps(data, indent=2))

    r2 = client.get("/api/v1/admin/chatbot-config/public")
    assert r2.status_code == 200
    etag2 = r2.headers["ETag"]
    assert etag2 != etag1
