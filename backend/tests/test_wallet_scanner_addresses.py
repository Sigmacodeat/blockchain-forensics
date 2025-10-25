import os
import pytest
from fastapi.testclient import TestClient

# Ensure TEST_MODE for predictable behavior
os.environ.setdefault("TEST_MODE", "1")

from app.main import app  # noqa: E402

# Dependency override for auth
from app.auth.dependencies import get_current_user_strict  # noqa: E402

app.dependency_overrides[get_current_user_strict] = lambda: {
    "user_id": "test-user",
    "username": "tester",
    "plan": "pro",
}

client = TestClient(app)

@pytest.fixture(autouse=True)
def _disable_require_plan(monkeypatch):
    # Bypass plan gate inside endpoint for this focused test
    async def _noop_require_plan(user, plan):
        return None
    monkeypatch.setattr("app.api.v1.wallet_scanner.require_plan", _noop_require_plan)
    yield


def test_scan_addresses_zero_trust_minimal():
    payload = {
        "addresses": [
            {"chain": "ethereum", "address": "0x28c6c06298d514db089934071355e5743bf21d60"},  # Binance hot wallet
        ],
        "check_history": False,
        "check_illicit": True,
    }
    resp = client.post("/api/v1/wallet-scanner/scan/addresses", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["wallet_type"] == "addresses"
    assert isinstance(data.get("addresses"), list) and len(data["addresses"]) >= 1
    addr_res = data["addresses"][0]
    assert addr_res["address"].lower() == payload["addresses"][0]["address"].lower()
    # risk_level should be present
    assert addr_res.get("risk_level") in {"low", "medium", "high", "critical"}
