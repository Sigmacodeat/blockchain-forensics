import os
import sys
import pathlib
import pytest
from fastapi.testclient import TestClient

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("TEST_MODE", "1")

from app.main import app  # noqa: E402
from app.config import settings  # noqa: E402
from app.compliance.screening_engine import ScreeningEngine, screening_engine  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def test_name_screen_defaults(monkeypatch, client):
    calls = {}

    async def fake_screen_name(name, threshold=None, max_results=None):
        calls["name"] = name
        calls["threshold"] = threshold
        calls["max_results"] = max_results
        return [{"entity": {"entity_number": 1}, "confidence": 0.9}]

    monkeypatch.setattr(screening_engine, "screen_name", fake_screen_name, raising=True)

    resp = client.get("/api/v1/compliance/name-screen", params={"name": "Test Entity"})
    assert resp.status_code == 200
    data = resp.json()

    # Defaults come from settings
    assert abs(data["threshold"] - float(getattr(settings, "FUZZY_NAME_THRESHOLD", 0.85))) < 1e-9
    assert data["match_count"] == 1

    # Verify passed through to engine
    assert abs(calls["threshold"] - float(getattr(settings, "FUZZY_NAME_THRESHOLD", 0.85))) < 1e-9
    assert int(calls["max_results"]) == int(getattr(settings, "FUZZY_MAX_MATCHES", 10))


def test_name_screen_with_params(monkeypatch, client):
    seen = {}

    async def fake_screen_name(name, threshold=None, max_results=None):
        seen["threshold"] = threshold
        seen["max_results"] = max_results
        return []

    monkeypatch.setattr(screening_engine, "screen_name", fake_screen_name, raising=True)

    resp = client.get(
        "/api/v1/compliance/name-screen",
        params={"name": "Acme Inc", "threshold": 0.9, "limit": 3},
    )
    assert resp.status_code == 200
    assert abs(seen["threshold"] - 0.9) < 1e-9
    assert seen["max_results"] == 3


def test_engine_normalization_and_similarity():
    eng = ScreeningEngine()
    # Diacritics removed and whitespace collapsed
    assert eng._normalize_name("José  García") == "Jose Garcia"
    # Similarity should be high for diacritic-insensitive comparison
    sim = eng._calculate_similarity("Jose Garcia", "José García")
    assert 0.85 <= sim <= 1.0
