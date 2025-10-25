from typing import List, Optional, Dict, Any

from app.config import settings

# Plan-Hierarchie konsistent zu auth.dependencies
PLAN_HIERARCHY = ["community", "starter", "pro", "business", "plus", "enterprise"]

SAFE_TOOLS = {
    # Read-only / marketing-sicher
    "text_extract",
    "code_extract",
    "intelligence_stats",
    "intelligence_list_flags",
    "list_alert_rules",
    # Marketing: Payments & Plan Awareness
    "get_user_plan",
    "get_available_cryptocurrencies",
    "get_payment_estimate",
    "recommend_best_currency",
    "suggest_web3_payment",
    "create_crypto_payment",
    "retry_failed_payment",
    "check_payment_status",
    "get_payment_history",
}

# Explizite Policies für sensible Tools
TOOL_POLICIES: Dict[str, Dict[str, Any]] = {
    "trigger_alert": {
        "min_plan": "business",
        "roles": {"admin"},
        "contexts": {"forensics"},
    },
    "trace_address": {
        "min_plan": "pro",
        "roles": {"admin", "analyst", "auditor"},
        "contexts": {"forensics"},
    },
    "advanced_trace": {
        "min_plan": "plus",
        "roles": {"admin", "analyst"},
        "contexts": {"forensics"},
    },
    "query_graph": {
        "min_plan": "pro",
        "roles": {"admin", "analyst", "auditor"},
        "contexts": {"forensics"},
    },
    "find_path": {
        "min_plan": "pro",
        "roles": {"admin", "analyst", "auditor"},
        "contexts": {"forensics"},
    },
    "risk_score": {
        "min_plan": "starter",
        "roles": {"admin", "analyst", "auditor"},
        "contexts": {"forensics"},
    },
    "bridge_lookup": {
        "min_plan": "community",
        "roles": {"admin", "analyst", "auditor", "viewer"},
        "contexts": {"forensics"},
    },
    "simulate_alerts": {
        "min_plan": "pro",
        "roles": {"admin", "analyst"},
        "contexts": {"forensics"},
    },
    "intelligence_flag": {
        "min_plan": "pro",
        "roles": {"admin", "analyst"},
        "contexts": {"forensics"},
    },
    "intelligence_confirm_flag": {
        "min_plan": "pro",
        "roles": {"admin", "analyst"},
        "contexts": {"forensics"},
    },
}


def _has_plan(user_plan: str, required_plan: str) -> bool:
    try:
        return PLAN_HIERARCHY.index(user_plan or "community") >= PLAN_HIERARCHY.index(required_plan)
    except ValueError:
        return False


def is_tool_allowed(tool_name: str, user: Optional[Dict[str, Any]], context: str) -> bool:
    """
    Entscheidet, ob ein Tool für gegebenen User+Kontext ausführbar ist.
    - Wenn RBAC-Flag deaktiviert: immer True
    - Marketing-Kontext: nur SAFE_TOOLS erlaubt
    - Forensics-Kontext: anhand TOOL_POLICIES; unbekannte Tools standardmäßig erlaubt
    - user=None wird als {role: viewer, plan: community} behandelt
    """
    if not getattr(settings, "ENABLE_AGENT_TOOL_RBAC", False):
        return True

    ctx = (context or "forensics").lower()

    if ctx == "marketing":
        return tool_name in SAFE_TOOLS

    # Forensics-Checks
    policy = TOOL_POLICIES.get(tool_name)
    if not policy:
        # unbekannte Tools standardmäßig zulassen im Forensics-Kontext (Least surprise)
        return True

    role = (user or {}).get("role", "viewer")
    plan = (user or {}).get("plan", "community")

    roles_ok = role in policy["roles"]
    plan_ok = _has_plan(plan, policy["min_plan"]) if policy.get("min_plan") else True
    context_ok = ctx in policy.get("contexts", {"forensics"})
    return roles_ok and plan_ok and context_ok


def filter_tools_for_context(tools: List[Any], user: Optional[Dict[str, Any]], context: str) -> List[Any]:
    """
    Filtert die übergebenen LangChain-Tools anhand RBAC/Context.
    """
    if not getattr(settings, "ENABLE_AGENT_TOOL_RBAC", False):
        return tools
    allowed = []
    for t in tools:
        name = getattr(t, "name", None)
        if not name:
            continue
        if is_tool_allowed(name, user, context):
            allowed.append(t)
    return allowed
