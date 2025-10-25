import os
import sys
import pathlib
import pytest

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("TEST_MODE", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")

from app.services.alert_engine import AlertEngine, Alert, AlertType, AlertSeverity  # noqa: E402
from app.config import settings  # noqa: E402


class _DummyResp:
    def __init__(self, code: int):
        self.status_code = code


class _DummyAsyncClient:
    calls = []
    sequence = [500, 200]

    def __init__(self, timeout=5):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None):
        # pick next code from sequence (fail then success)
        code = self.sequence[min(len(self.calls), len(self.sequence)-1)]
        self.calls.append((url, json, code))
        return _DummyResp(code)


@pytest.mark.asyncio
async def test_webhook_retry_and_success(monkeypatch):
    eng = AlertEngine()
    # Configure a fake webhook URL (monkeypatch module.settings, not pydantic instance)
    monkeypatch.setenv("ALERT_WEBHOOK_URLS", "")
    import app.services.alert_engine as ae
    ae.settings = type("_S", (), {"ALERT_WEBHOOK_URLS": ["https://webhook.test/hook"]})

    # Monkeypatch httpx module used in dispatch_alert (import httpx)
    import types
    dummy_httpx = types.SimpleNamespace(AsyncClient=_DummyAsyncClient)
    sys.modules['httpx'] = dummy_httpx

    a = Alert(alert_type=AlertType.DEX_SWAP, severity=AlertSeverity.MEDIUM, title="t", description="d")
    await eng.dispatch_alert(a)

    # Expect at least 2 attempts: first 500, then 200
    assert len(_DummyAsyncClient.calls) >= 2
    # Last call should have 200
    assert _DummyAsyncClient.calls[-1][2] == 200
