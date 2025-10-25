from fastapi.testclient import TestClient
from app.main import app
from app.compliance import monitor_service as monitor_service_module

client = TestClient(app)


def test_list_alert_events_monkeypatch(monkeypatch):
    async def fake_list_alert_events(alert_id: str, limit: int = 100):
        return [
            {
                "id": 1,
                "alert_id": alert_id,
                "created_at": "2025-01-01T00:00:00",
                "actor": None,
                "type": "note_added",
                "payload": {"note": "Test"},
            }
        ]

    monkeypatch.setattr(
        monitor_service_module.monitor_service, "list_alert_events", fake_list_alert_events
    )

    res = client.get(
        "/api/v1/monitor/alerts/00000000-0000-0000-0000-000000000001/events?limit=10"
    )
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert data[0]["type"] == "note_added"
    assert data[0]["payload"]["note"] == "Test"
