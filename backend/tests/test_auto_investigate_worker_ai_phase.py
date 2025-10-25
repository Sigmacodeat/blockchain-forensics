import asyncio
import types
import pytest

from typing import Any, Dict, List

# Target under test
from app.workers.auto_investigate_worker import _ai_assess_and_alert


@pytest.mark.asyncio
async def test_ai_assess_and_alert_creates_evidence(monkeypatch):
    calls: Dict[str, List[Dict[str, Any]]] = {
        "save_attachment": [],
        "link_attachment_as_evidence": [],
        "alerts": [],
    }

    # Mock case_service.save_attachment/link_attachment_as_evidence
    from app.cases import service as case_service_module

    def fake_save_attachment(case_id: str, filename: str, content: bytes, content_type: str):
        calls["save_attachment"].append({
            "case_id": case_id,
            "filename": filename,
            "content_type": content_type,
            "size": len(content),
        })
        # minimal meta expected by link_attachment_as_evidence
        return {"filename": filename, "content_type": content_type, "size": len(content)}

    def fake_link_attachment_as_evidence(case_id: str, meta: Dict[str, Any], notes: str = ""):
        calls["link_attachment_as_evidence"].append({
            "case_id": case_id,
            "meta": meta,
            "notes": notes,
        })

    monkeypatch.setattr(case_service_module.case_service, "save_attachment", fake_save_attachment)
    monkeypatch.setattr(case_service_module.case_service, "link_attachment_as_evidence", fake_link_attachment_as_evidence)

    # Mock risk_scorer
    from app.ml import risk_scorer as risk_module

    async def fake_calc(addr: str):
        return {"risk_score": 0.91, "risk_level": "high", "factors": ["sanctioned", "mixer"]}

    monkeypatch.setattr(risk_module.risk_scorer, "calculate_risk_score", fake_calc)

    # Mock bridge_registry
    from app.bridge import registry as bridge_module

    class _DummyContract:
        address = "0xdead"
        chain = "ethereum"
        name = "TestBridge"
        bridge_type = "canonical"
        counterpart_chains = ["polygon"]
        method_selectors = ["0xa9059cbb"]
        import datetime
        added_at = datetime.datetime(2024, 1, 1)

    monkeypatch.setattr(bridge_module.bridge_registry, "is_bridge_contract", lambda addr, chain: True)
    monkeypatch.setattr(bridge_module.bridge_registry, "get_contract", lambda addr, chain: _DummyContract)
    monkeypatch.setattr(bridge_module.bridge_registry, "is_bridge_method", lambda selector: True)

    # Mock alert_service
    from app.services import alert_service as alert_module

    class _DummyAlert:
        def __init__(self, title: str = "High Risk"):
            self._title = title
        def to_dict(self):
            return {"title": self._title, "severity": "high"}

    async def fake_process_event(event: Dict[str, Any]):
        calls["alerts"].append(event)
        return [_DummyAlert()]  # one alert

    monkeypatch.setattr(alert_module.alert_service, "process_event", fake_process_event)

    # Execute
    case_id = "TEST-CASE-AI"
    job = {
        "address": "0xabc123456789",
        "chain": "ethereum",
        "tx_hash": "0xbeef",
        "method_selector": "0xa9059cbb",
        "value_usd": 250000,
    }

    await _ai_assess_and_alert(job, case_id)

    # Asserts: three attachments saved and linked (risk, bridge, alerts)
    assert len(calls["save_attachment"]) == 3
    assert len(calls["link_attachment_as_evidence"]) == 3

    filenames = [c["filename"] for c in calls["save_attachment"]]
    assert any(fn.startswith("risk_") and fn.endswith(".json") for fn in filenames)
    assert any(fn.startswith("bridge_") and fn.endswith(".json") for fn in filenames)
    assert any(fn.startswith("alerts_") and fn.endswith(".json") for fn in filenames)

    # Alert event carried context
    assert calls["alerts"], "alert_service.process_event must be called"
    evt = calls["alerts"][0]
    assert evt["address"].lower() == job["address"].lower()
    assert evt["risk_score"] >= 0.9
    assert evt["tx_hash"] == job["tx_hash"]
    assert evt["value_usd"] == job["value_usd"]
    assert evt["chain"] == job["chain"]
