import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DISABLE_LIFESPAN", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")
os.environ.setdefault("TEST_MODE", "1")

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def with_auth_override():
    from app.auth import dependencies as deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"user": "test"}
    app.dependency_overrides[deps.get_current_user_strict] = lambda: {"user": "test"}
    yield
    app.dependency_overrides = {}


def test_patterns_requires_auth(client: TestClient):
    r = client.get("/api/v1/patterns/detect", params={"address": "0xabc"})
    assert r.status_code in (401, 403)


def test_patterns_basic_with_auth(client: TestClient, with_auth_override):
    r = client.get("/api/v1/patterns/detect", params={"address": "0xabc", "limit": 20})
    assert r.status_code == 200
    body = r.json()
    assert body.get("address") == "0xabc"
    assert "findings" in body


def test_patterns_filtering_with_auth(client: TestClient, with_auth_override):
    # Request with filters: only peel_chain and min_score high to likely filter
    r = client.get(
        "/api/v1/patterns/detect",
        params={"address": "0xabc", "limit": 20, "patterns": "peel_chain", "min_score": 0.9},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("address") == "0xabc"
    assert "findings" in body
    # In TEST_MODE the unified detector may return empty; assert structure not failing
    assert isinstance(body["findings"], list)


def test_patterns_check_mock_in_test_mode(client: TestClient):
    # /patterns/check bypasses strict auth in TEST/OFFLINE via _optional_user
    r = client.get("/api/v1/patterns/check", params={"address": "0xdeadbeef"})
    assert r.status_code == 200
    body = r.json()
    assert body.get("address") == "0xdeadbeef"
    assert "findings" in body
    assert isinstance(body["findings"], list)


def test_patterns_check_filters(client: TestClient):
    r = client.get(
        "/api/v1/patterns/check",
        params={"address": "0xdeadbeef", "patterns": "peel_chain", "min_score": 0.7},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("address") == "0xdeadbeef"
    assert isinstance(body.get("findings", []), list)


def test_patterns_check_alias_with_auth(client: TestClient, with_auth_override):
    r = client.get("/api/v1/patterns/check", params={"address": "0xabc", "patterns": "peel_chain,rapid_movement", "min_score": 0.0, "limit": 20})
    assert r.status_code == 200
    body = r.json()
    assert body.get("address") == "0xabc"
    assert "findings" in body


def test_patterns_detect_alias_with_auth(client: TestClient, with_auth_override):
    r = client.get("/api/v1/patterns/detect", params={"address": "0xabc", "limit": 20})
    assert r.status_code == 200
    body = r.json()
    assert body.get("address") == "0xabc"
    assert "findings" in body
