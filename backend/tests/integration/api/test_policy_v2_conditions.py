import asyncio
import pytest

from app.services.alert_engine import AlertEngine, AlertSeverity

@pytest.mark.asyncio
async def test_policy_v2_all_any_not_conditions():
    engine = AlertEngine()
    engine.policy_rules = {
        "metadata": {"version": 2.0},
        "rules": [
            {
                "name": "high_risk_and_label",
                "when": {
                    "all": [
                        {"field": "risk_score", "operator": "gte", "value": 0.9},
                        {"field": "labels", "operator": "in", "value": ["sanctioned", "ofac"]},
                        {"operator": "not", "value": {"field": "test_mode", "operator": "eq", "value": True}},
                    ]
                },
                "severity": "high",
            }
        ],
    }

    # Should match
    event = {"risk_score": 0.95, "labels": ["ofac"], "address": "0xabc"}
    alerts = await engine.process_event(event)
    assert any(a.severity == AlertSeverity.HIGH and "Policy Match" in a.title for a in alerts)

    # Should not match because of NOT(test_mode)
    event2 = {"risk_score": 0.95, "labels": ["ofac"], "test_mode": True, "address": "0xabc"}
    alerts2 = await engine.process_event(event2)
    assert not any("Policy Match" in a.title for a in alerts2)


@pytest.mark.asyncio
async def test_policy_v2_simulation_mode_blocks_emission():
    engine = AlertEngine()
    engine.simulation_mode = True
    engine.policy_rules = {
        "metadata": {"version": 2.0},
        "rules": [
            {
                "name": "any_label",
                "when": {"any": [{"field": "labels", "operator": "in", "value": ["x", "y"]}]},
                "severity": "medium",
            }
        ],
    }

    event = {"labels": ["x"], "address": "0xabc"}
    alerts = await engine.process_event(event)
    # In simulation mode, the policy matches but must not emit an alert
    assert not any("Policy Match" in a.title for a in alerts)
