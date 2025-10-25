import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_patterns_check_offline_mock():
    # Ensure TEST_MODE to get mock data deterministically
    os.environ["TEST_MODE"] = "1"
    resp = client.get(
        "/api/v1/patterns/check",
        params={
            "address": "0x1234567890123456789012345678901234567890",
            "window_minutes": 60,
            "max_hops": 5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["address"] == "0x1234567890123456789012345678901234567890"
    assert "findings" in data
    assert isinstance(data["findings"], list)
    # Mock should include at least one finding
    assert len(data["findings"]) >= 1
    first = data["findings"][0]
    assert "pattern" in first and "score" in first and "evidence" in first


def test_patterns_check_invalid_params():
    # Invalid: missing address
    resp = client.get("/api/v1/patterns/check")
    assert resp.status_code in (400, 422)

    # Invalid: out-of-range window
    resp2 = client.get(
        "/api/v1/patterns/check",
        params={"address": "0xabc", "window_minutes": 1},
    )
    assert resp2.status_code in (400, 422)
