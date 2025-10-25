import pytest

from app.streaming import monitor_consumer as mc


@pytest.mark.asyncio
async def test_process_event_creates_alert_with_stub(monkeypatch):
    # Arrange: one enabled rule that matches any event
    rule = {
        "id": "00000000-0000-0000-0000-0000000000ab",
        "name": "MatchAll",
        "severity": "high",
        "expression": {"any": [{"risk_score": {">=": 0}}]},
        "scope": "tx",
        "enabled": True,
    }

    async def fake_list_enabled_rules():
        return [rule]

    async def fake_persist_alert(rule, entity_type, entity_id, chain, ctx):
        return "11111111-1111-1111-1111-111111111111"

    monkeypatch.setattr(mc, "_list_enabled_rules", fake_list_enabled_rules)
    monkeypatch.setattr(mc, "_persist_alert", fake_persist_alert)

    event = {
        "tx_hash": "0xabc",
        "from_address": "0xfrom",
        "to_address": "0xto",
        "chain": "ethereum",
        "risk_score": 0.9,
        "tx": {"value_usd": 20000},
    }

    # Act
    created = await mc.process_event(event)

    # Assert
    assert created == 1
