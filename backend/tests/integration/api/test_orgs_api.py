import os
import pytest
from fastapi.testclient import TestClient

# Ensure test mode
os.environ.setdefault("DISABLE_LIFESPAN", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")

from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def override_auth_dependency(monkeypatch):
    # Provide a strict user object compatible with orgs endpoints
    from app.auth import dependencies as deps
    app.dependency_overrides[deps.get_current_user_strict] = lambda: {
        "user_id": "user-1",
        "username": "tester",
        "role": "admin",
        "email": "t@example.com",
    }
    yield
    app.dependency_overrides = {}


class _FakePipeline:
    def __init__(self, store):
        self.store = store
        self.ops = []

    def set(self, key, value):
        self.ops.append(("set", key, value))
        return self

    def sadd(self, key, *values):
        self.ops.append(("sadd", key, *values))
        return self

    async def execute(self):
        results = []
        for op in self.ops:
            if op[0] == "set":
                self.store[op[1]] = op[2]
                results.append(True)
            elif op[0] == "sadd":
                s = self.store.setdefault(op[1], set())
                before = len(s)
                for v in op[2:]:
                    s.add(v)
                results.append(len(s) > before)
        self.ops = []
        return results


class _FakeRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        v = self.store.get(key)
        return v

    async def smembers(self, key):
        v = self.store.get(key)
        if isinstance(v, set):
            return set(v)
        return set()

    def pipeline(self):
        return _FakePipeline(self.store)


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    # Patch redis_client used by org_service
    from app.db import redis_client as redis_mod

    async def _ensure():
        return True

    fake = _FakeRedis()
    # pre-warm: nothing

    monkeypatch.setattr(redis_mod, "_ensure_connected", _ensure, raising=True)
    monkeypatch.setattr(redis_mod, "client", fake, raising=True)

    yield


def _client():
    return TestClient(app)


def test_create_and_list_orgs():
    client = _client()

    # Initially empty
    r = client.get("/api/v1/orgs")
    assert r.status_code == 200
    assert r.json()["organizations"] == []

    # Create org
    r = client.post("/api/v1/orgs", json={"name": "MyOrg"})
    assert r.status_code == 201
    org = r.json()
    assert org["name"] == "MyOrg"
    assert "id" in org

    # List should include
    r = client.get("/api/v1/orgs")
    assert r.status_code == 200
    orgs = r.json()["organizations"]
    assert any(o["id"] == org["id"] for o in orgs)

    # Duplicate should 409
    r = client.post("/api/v1/orgs", json={"name": "MyOrg"})
    assert r.status_code == 409


def test_get_org_and_membership_checks():
    client = _client()

    # Create org
    r = client.post("/api/v1/orgs", json={"name": "Alpha"})
    assert r.status_code == 201
    org = r.json()

    # Get org should be ok for owner
    r = client.get(f"/api/v1/orgs/{org['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == org["id"]

    # Members list initially contains owner user-1
    r = client.get(f"/api/v1/orgs/{org['id']}/members")
    assert r.status_code == 200
    members = r.json()["members"]
    assert "user-1" in members


def test_add_member_and_list_members():
    client = _client()

    # Create org
    r = client.post("/api/v1/orgs", json={"name": "TeamX"})
    assert r.status_code == 201
    org = r.json()

    # Add another user
    r = client.post(f"/api/v1/orgs/{org['id']}/members", json={"user_id": "user-2"})
    assert r.status_code == 204

    # List members should include user-2 now
    r = client.get(f"/api/v1/orgs/{org['id']}/members")
    assert r.status_code == 200
    members = r.json()["members"]
    assert "user-2" in members


def test_validation_errors():
    client = _client()

    # Too short name
    r = client.post("/api/v1/orgs", json={"name": "ab"})
    assert r.status_code == 400

    # Invalid chars
    r = client.post("/api/v1/orgs", json={"name": "Bad*!"})
    assert r.status_code == 400
