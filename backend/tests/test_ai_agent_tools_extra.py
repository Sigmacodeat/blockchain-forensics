import os
import pytest

# Ensure required settings are present
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ENABLE_AI_AGENTS", "true")

from app.ai_agents.tools import risk_score_tool, bridge_lookup_tool, trigger_alert_tool

pytestmark = pytest.mark.anyio("asyncio")


async def test_risk_score_tool_basic():
    result = await risk_score_tool.ainvoke({
        "address": "0x0000000000000000000000000000000000000000"
    })
    assert isinstance(result, dict)
    assert "risk_score" in result
    assert "risk_level" in result
    assert result.get("address") == "0x0000000000000000000000000000000000000000"


async def test_bridge_lookup_by_chain_lists_contracts():
    result = await bridge_lookup_tool.ainvoke({
        "chain": "polygon"
    })
    assert isinstance(result, dict)
    # Implementation returns 'contracts' and 'stats'
    assert "contracts" in result or "stats" in result


async def test_bridge_lookup_is_bridge_contract_true():
    # Known from registry defaults: Polygon ERC20 Predicate
    result = await bridge_lookup_tool.ainvoke({
        "chain": "polygon",
        "address": "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf"
    })
    assert isinstance(result, dict)
    assert result.get("is_bridge_contract") is True
    assert "contract" in result


async def test_trigger_alert_tool_creates_alert():
    # Use a supported alert_type (e.g., 'mixer')
    result = await trigger_alert_tool.ainvoke({
        "alert_type": "mixer",
        "address": "0x1111111111111111111111111111111111111111",
        "tx_hash": "0xabc",
        "labels": ["mixer"],
    })
    assert isinstance(result, dict)
    # Expect engine-processed alerts summary
    assert result.get("count", 0) >= 1
    assert "alerts_triggered" in result
