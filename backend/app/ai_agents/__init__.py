"""AI Agents module exports.

The original implementation skipped importing heavy LangChain dependencies when
agents were disabled.  Our test-suite, however, relies on these modules being
importable so that targets like ``app.ai_agents.agent.agent_executor`` can be
patched.  To balance both needs we attempt to import the modules eagerly, but
gracefully fall back to lightweight defaults when optional dependencies are not
available or agents are disabled.
"""

from typing import Any

from app.config import settings

FORENSIC_TOOLS: Any = None
forensic_agent: Any = None
ForensicAgent: Any = None
agent_executor: Any = None


def _load_tools() -> Any:
    try:
        from .tools import FORENSIC_TOOLS as _TOOLS  # type: ignore

        return _TOOLS
    except Exception:
        # Tests patch concrete tool callables.  Expose an empty list instead of
        # failing the import so attribute access keeps working.
        return []


def _load_agent_exports() -> tuple[Any, Any, Any]:
    try:
        from .agent import (  # type: ignore
            forensic_agent as _agent,
            ForensicAgent as _AgentCls,
            agent_executor as _executor,
        )

        return _agent, _AgentCls, _executor
    except Exception:
        return None, None, None


# Tools are safe to expose even when AI agents are disabled – the functions
# perform their own availability checks.  Keeping the attribute ensures patches
# in tests succeed.
FORENSIC_TOOLS = _load_tools()

_agent, _AgentCls, _executor = _load_agent_exports()
forensic_agent = _agent
ForensicAgent = _AgentCls
agent_executor = _executor

# When agents are explicitly disabled ensure we expose harmless defaults so API
# handlers can still operate in mock/test mode.
if not getattr(settings, "ENABLE_AI_AGENTS", False):
    forensic_agent = None
    # Prefer leaving FORENSIC_TOOLS as list (possibly empty) so iteration works.

__all__ = ["FORENSIC_TOOLS", "forensic_agent", "ForensicAgent", "agent_executor"]
