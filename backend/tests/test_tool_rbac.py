
from app.ai_agents.tool_rbac import filter_tools_for_context
from app.config import settings


class DummyTool:
    def __init__(self, name: str):
        self.name = name


def test_marketing_only_safe_tools():
    prev = settings.ENABLE_AGENT_TOOL_RBAC
    settings.ENABLE_AGENT_TOOL_RBAC = True
    try:
        tools = [
            DummyTool("text_extract"),
            DummyTool("code_extract"),
            DummyTool("list_alert_rules"),
            DummyTool("trace_address"),
            DummyTool("risk_score"),
        ]
        allowed = filter_tools_for_context(tools, user=None, context="marketing")
        names = {t.name for t in allowed}
        assert "text_extract" in names
        assert "code_extract" in names
        assert "list_alert_rules" in names
        assert "trace_address" not in names
        assert "risk_score" not in names
    finally:
        settings.ENABLE_AGENT_TOOL_RBAC = prev


def test_marketing_allows_payment_tools():
    prev = settings.ENABLE_AGENT_TOOL_RBAC
    settings.ENABLE_AGENT_TOOL_RBAC = True
    try:
        tools = [
            DummyTool("create_crypto_payment"),
            DummyTool("recommend_best_currency"),
            DummyTool("get_payment_estimate"),
            DummyTool("get_available_cryptocurrencies"),
            DummyTool("retry_failed_payment"),
            DummyTool("check_payment_status"),
            DummyTool("get_payment_history"),
            DummyTool("suggest_web3_payment"),
        ]
        allowed = filter_tools_for_context(tools, user=None, context="marketing")
        names = {t.name for t in allowed}
        for n in [
            "create_crypto_payment",
            "recommend_best_currency",
            "get_payment_estimate",
            "get_available_cryptocurrencies",
            "retry_failed_payment",
            "check_payment_status",
            "get_payment_history",
            "suggest_web3_payment",
        ]:
            assert n in names
    finally:
        settings.ENABLE_AGENT_TOOL_RBAC = prev


def test_forensics_policy_roles_and_plans():
    prev = settings.ENABLE_AGENT_TOOL_RBAC
    settings.ENABLE_AGENT_TOOL_RBAC = True
    try:
        user = {"role": "analyst", "plan": "pro"}
        tools = [
            DummyTool("trace_address"),
            DummyTool("risk_score"),
            DummyTool("bridge_lookup"),
            DummyTool("trigger_alert"),
        ]
        allowed = filter_tools_for_context(tools, user=user, context="forensics")
        names = {t.name for t in allowed}
        assert "trace_address" in names  # pro + analyst OK
        assert "risk_score" in names     # starter+ + analyst OK
        assert "bridge_lookup" in names  # community+ + viewer+ OK
        assert "trigger_alert" not in names  # requires admin + business
    finally:
        settings.ENABLE_AGENT_TOOL_RBAC = prev


def test_forensics_viewer_community_limits():
    prev = settings.ENABLE_AGENT_TOOL_RBAC
    settings.ENABLE_AGENT_TOOL_RBAC = True
    try:
        user = {"role": "viewer", "plan": "community"}
        tools = [
            DummyTool("trace_address"),
            DummyTool("risk_score"),
            DummyTool("bridge_lookup"),
        ]
        allowed = filter_tools_for_context(tools, user=user, context="forensics")
        names = {t.name for t in allowed}
        assert "bridge_lookup" in names
        assert "risk_score" not in names
        assert "trace_address" not in names
    finally:
        settings.ENABLE_AGENT_TOOL_RBAC = prev


def test_unknown_tool_default_allow_forensics():
    prev = settings.ENABLE_AGENT_TOOL_RBAC
    settings.ENABLE_AGENT_TOOL_RBAC = True
    try:
        user = {"role": "analyst", "plan": "pro"}
        tools = [DummyTool("my_custom_view")]
        allowed = filter_tools_for_context(tools, user=user, context="forensics")
        names = {t.name for t in allowed}
        assert "my_custom_view" in names
    finally:
        settings.ENABLE_AGENT_TOOL_RBAC = prev
