import pytest

from backend.app.ai_agents.tools import (
    intelligence_stats_tool,
    intelligence_flag_tool,
    intelligence_confirm_flag_tool,
    intelligence_list_flags_tool,
    intelligence_check_tool,
)


@pytest.mark.asyncio
async def test_intelligence_workflow_end_to_end():
    # 1) Stats should be callable (empty network ok)
    stats = await intelligence_stats_tool()
    assert isinstance(stats, dict)
    assert "total_flags" in stats

    # 2) Create a flag
    flag = await intelligence_flag_tool(
        address="0x1234567890abcdef1234567890abcdef12345678",
        chain="ethereum",
        reason="ransomware",
        description="Test flag for ransomware",
        amount_usd=1000.0,
        evidence=[{"type": "report", "value": "https://example.com/report"}],
        related_addresses=["0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"],
        auto_trace=True,
    )
    assert isinstance(flag, dict)
    assert flag.get("flag_id")
    assert flag.get("status") in {"active", "confirmed"}

    flag_id = flag["flag_id"]

    # 3) Confirm the flag (idempotent safety in service)
    confirmed = await intelligence_confirm_flag_tool(
        flag_id=flag_id,
        additional_evidence=[{"type": "article", "value": "https://example.com/article"}],
    )
    assert confirmed.get("flag_id") == flag_id
    assert confirmed.get("confirmations") >= 1

    # 4) List flags with filters
    listed = await intelligence_list_flags_tool(status=confirmed["status"], reason=confirmed["reason"], chain=confirmed["chain"], limit=10, offset=0)
    assert isinstance(listed, dict)
    assert isinstance(listed.get("flags"), list)
    assert listed.get("total") >= 1

    # 5) Check address against network
    check = await intelligence_check_tool(
        address=flag["address"],
        chain=flag["chain"],
        check_related=True,
    )
    assert isinstance(check, dict)
    assert "risk_score" in check
    assert check["address"] == flag["address"]
