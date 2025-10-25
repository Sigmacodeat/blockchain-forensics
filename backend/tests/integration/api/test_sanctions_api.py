from fastapi.testclient import TestClient
from app.main import app

def test_sanctions_stats_and_screen_and_reload():
    client = TestClient(app)

    # stats
    r = client.get("/api/v1/sanctions/stats")
    assert r.status_code == 200
    data = r.json()
    assert "sources" in data and isinstance(data["sources"], list)
    assert set(["ofac", "un", "eu", "uk"]).issuperset(set(data["sources"]))

    # screen minimal (name)
    r = client.post("/api/v1/sanctions/screen", json={"name": "Satoshi Nakamoto"})
    assert r.status_code == 200
    s = r.json()
    assert s["matched"] in (True, False)
    assert "lists" in s

    # reload
    r = client.post("/api/v1/sanctions/reload")
    assert r.status_code == 200
    re = r.json()
    assert re.get("success") is True
