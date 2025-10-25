"""
Modular Tool Structure for AI Agent.
All tools organized by category for better maintainability.

Total Tools: 50+ production-ready tools across 9 categories.
"""

import logging
from typing import Optional, List, Dict, Any

from pydantic.v1 import BaseModel, Field  # type: ignore

logger = logging.getLogger(__name__)

# Initialize forensic tools list (will be populated after imports)
FORENSIC_TOOLS = []

# Import all tool categories
try:
    from .case_management import CASE_TOOLS
except ImportError:
    logger.warning("case_management tools not found")
    CASE_TOOLS = []

try:
    from .reporting import REPORTING_TOOLS
except ImportError:
    logger.warning("reporting tools not found")
    REPORTING_TOOLS = []

try:
    from .analytics import ANALYTICS_TOOLS
except ImportError:
    logger.warning("analytics tools not found")
    ANALYTICS_TOOLS = []

try:
    from .defi import DEFI_TOOLS
except ImportError:
    logger.warning("defi tools not found")
    DEFI_TOOLS = []

try:
    from .nft import NFT_TOOLS
except ImportError:
    logger.warning("nft tools not found")
    NFT_TOOLS = []

try:
    from .dark_web import DARKWEB_TOOLS
except ImportError:
    logger.warning("dark_web tools not found")
    DARKWEB_TOOLS = []

try:
    from .automation import AUTOMATION_TOOLS
except ImportError:
    logger.warning("automation tools not found")
    AUTOMATION_TOOLS = []

try:
    from .collaboration import COLLAB_TOOLS
except ImportError:
    logger.warning("collaboration tools not found")
    COLLAB_TOOLS = []

try:
    from .discovery import DISCOVERY_TOOLS
except ImportError:
    logger.warning("discovery tools not found")
    DISCOVERY_TOOLS = []

# Combine all tools
ALL_TOOLS = (
    FORENSIC_TOOLS + 
    CASE_TOOLS + 
    REPORTING_TOOLS + 
    ANALYTICS_TOOLS + 
    DEFI_TOOLS + 
    NFT_TOOLS + 
    DARKWEB_TOOLS + 
    AUTOMATION_TOOLS + 
    COLLAB_TOOLS +
    DISCOVERY_TOOLS
)

# Log detailed summary
logger.info("=" * 60)
logger.info("✅ AI AGENT TOOLS LOADED")
logger.info("=" * 60)
logger.info(f"Total Tools: {len(ALL_TOOLS)}")
logger.info(f"  📊 Forensic Tools: {len(FORENSIC_TOOLS)}")
logger.info(f"  📁 Case Management: {len(CASE_TOOLS)}")
logger.info(f"  📄 Reporting: {len(REPORTING_TOOLS)}")
logger.info(f"  📈 Analytics: {len(ANALYTICS_TOOLS)}")
logger.info(f"  🏦 DeFi: {len(DEFI_TOOLS)}")
logger.info(f"  🖼️  NFT: {len(NFT_TOOLS)}")
logger.info(f"  🕵️  Dark Web: {len(DARKWEB_TOOLS)}")
logger.info(f"  ⚙️  Automation: {len(AUTOMATION_TOOLS)}")
logger.info(f"  👥 Collaboration: {len(COLLAB_TOOLS)}")
logger.info(f"  🔍 Discovery: {len(DISCOVERY_TOOLS)}")
logger.info("=" * 60)

# Import individual forensic tools
try:
    from .forensic_tools import (
        risk_score_tool,
        bridge_lookup_tool,
        trigger_alert_tool,
        list_alert_rules_tool,
        simulate_alerts_tool,
        trace_address_tool,
        code_extract_tool,
        text_extract_tool,
    )
    logger.info("✅ Forensic tools imported successfully")
    
    # Add to FORENSIC_TOOLS list
    if risk_score_tool:
        FORENSIC_TOOLS.extend([
            risk_score_tool,
            bridge_lookup_tool,
            trigger_alert_tool,
            list_alert_rules_tool,
            simulate_alerts_tool,
            trace_address_tool,
            code_extract_tool,
            text_extract_tool,
        ])
except ImportError as e:
    logger.error(f"Could not import forensic tools: {e}")
    # Create dummy tools to prevent import errors
    risk_score_tool = None
    bridge_lookup_tool = None
    trigger_alert_tool = None
    list_alert_rules_tool = None
    simulate_alerts_tool = None
    trace_address_tool = None
    code_extract_tool = None
    text_extract_tool = None

# ------------------------------------------------------------------
# Legacy alias names expected by tests (package-level attributes)
# ------------------------------------------------------------------
try:
    # Primary forensic aliases
    trace_address = trace_address_tool  # type: ignore[name-defined]
except Exception:
    trace_address = None  # type: ignore[assignment]

try:
    risk_score = risk_score_tool  # type: ignore[name-defined]
except Exception:
    risk_score = None  # type: ignore[assignment]

try:
    # Case management alias may live in case_management_tools
    from .case_management_tools import create_case_tool as _create_case_tool  # type: ignore
    create_case = _create_case_tool
except Exception:
    try:
        from .case_management import create_case_tool as _create_case_tool2  # type: ignore
        create_case = _create_case_tool2
    except Exception:
        create_case = None  # type: ignore[assignment]

try:
    # Crypto payments aliases
    from .crypto_payment_tools import (
        get_available_cryptocurrencies_tool as _get_available_cryptocurrencies_tool,  # type: ignore
        create_crypto_payment_tool as _create_crypto_payment_tool,  # type: ignore
    )
    get_available_cryptocurrencies = _get_available_cryptocurrencies_tool
    create_crypto_payment = _create_crypto_payment_tool
except Exception:
    # Fallback to None so unittest.mock.patch can target attributes
    get_available_cryptocurrencies = None  # type: ignore[assignment]
    create_crypto_payment = None  # type: ignore[assignment]

# ================================
# Intelligence Network Direct Tools (package-level)
# ================================
try:
    from app.services.intelligence_sharing_service import (
        intelligence_sharing_service,
        FlagReason,
        InvestigatorTier,
        FlagStatus,
    )
except Exception:  # pragma: no cover
    intelligence_sharing_service = None
    FlagReason = InvestigatorTier = FlagStatus = None  # type: ignore


async def intelligence_check_tool(address: str, chain: str, check_related: bool = True) -> Dict[str, Any]:
    """Check an address against the Intelligence Network and return risk, flags and recommendation."""
    try:
        return await intelligence_sharing_service.check_address_against_network(address=address, chain=chain, check_related=check_related)  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.error(f"intelligence_check_tool error: {e}")
        return {"error": str(e)}


async def intelligence_flag_tool(address: str, chain: str, reason: str, description: str, amount_usd: Optional[float] = None, evidence: Optional[List[Dict[str, Any]]] = None, related_addresses: Optional[List[str]] = None, auto_trace: bool = True) -> Dict[str, Any]:
    """Create an Intelligence Network flag for an address with optional evidence and auto-trace."""
    try:
        # ensure default investigator exists
        inv_id = "inv-agent"
        if inv_id not in intelligence_sharing_service.investigators:  # type: ignore
            await intelligence_sharing_service.register_investigator(  # type: ignore
                investigator_id=inv_id,
                org_name="AI Agent",
                tier=InvestigatorTier.COMMUNITY_TRUSTED,
                verification_docs=None,
                contact_info={},
            )
        rmap = {
            "hack": FlagReason.HACK,
            "fraud": FlagReason.FRAUD,
            "sanctions": FlagReason.SANCTIONS,
            "terrorism_financing": FlagReason.TERRORISM_FINANCING,
            "money_laundering": FlagReason.MONEY_LAUNDERING,
            "ransomware": FlagReason.RANSOMWARE,
            "scam": FlagReason.SCAM,
            "mixer_abuse": FlagReason.MIXER_ABUSE,
            "child_exploitation": FlagReason.CHILD_EXPLOITATION,
            "other_illicit": FlagReason.OTHER_ILLICIT,
        }
        r = rmap.get(reason.lower())
        if not r:
            return {"error": f"Unsupported reason: {reason}"}
        return await intelligence_sharing_service.flag_address(  # type: ignore
            address=address,
            chain=chain,
            reason=r,
            investigator_id=inv_id,
            incident_id=None,
            amount_usd=amount_usd,
            description=description,
            evidence=evidence or [],
            related_addresses=related_addresses or [],
            auto_trace=auto_trace,
        )
    except Exception as e:  # pragma: no cover
        logger.error(f"intelligence_flag_tool error: {e}")
        return {"error": str(e)}


async def intelligence_confirm_flag_tool(flag_id: str, additional_evidence: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Confirm an existing Intelligence Network flag, optionally adding additional evidence."""
    try:
        inv_id = "inv-agent"
        if inv_id not in intelligence_sharing_service.investigators:  # type: ignore
            await intelligence_sharing_service.register_investigator(  # type: ignore
                investigator_id=inv_id,
                org_name="AI Agent",
                tier=InvestigatorTier.COMMUNITY_TRUSTED,
                verification_docs=None,
                contact_info={},
            )
        return await intelligence_sharing_service.confirm_flag(  # type: ignore
            flag_id=flag_id,
            investigator_id=inv_id,
            additional_evidence=additional_evidence or [],
        )
    except Exception as e:  # pragma: no cover
        logger.error(f"intelligence_confirm_flag_tool error: {e}")
        return {"error": str(e)}


async def intelligence_list_flags_tool(status: Optional[str] = None, reason: Optional[str] = None, chain: Optional[str] = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """List Intelligence Network flags with optional filters (status, reason, chain) and pagination."""
    try:
        flags = list(intelligence_sharing_service.flags_db.values())  # type: ignore
        if status:
            s = status.lower()
            valid = {fs.value for fs in FlagStatus}
            if s not in valid:
                return {"error": f"Unsupported status: {status}"}
            flags = [f for f in flags if f.get("status") == s]
        if reason:
            flags = [f for f in flags if f.get("reason") == reason.lower()]
        if chain:
            flags = [f for f in flags if f.get("chain") == chain]
        flags.sort(key=lambda x: x.get("flagged_at", ""), reverse=True)
        total = len(flags)
        return {"flags": flags[offset: offset + limit], "total": total, "limit": limit, "offset": offset}
    except Exception as e:  # pragma: no cover
        logger.error(f"intelligence_list_flags_tool error: {e}")
        return {"error": str(e)}


async def intelligence_stats_tool() -> Dict[str, Any]:
    """Return Intelligence Network statistics (investigators, members, flags, amounts, effectiveness)."""
    try:
        return await intelligence_sharing_service.get_network_stats()  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.error(f"intelligence_stats_tool error: {e}")
        return {"error": str(e)}

# Export for easy import
__all__ = [
    "ALL_TOOLS",
    "FORENSIC_TOOLS",
    "CASE_TOOLS",
    "REPORTING_TOOLS",
    "ANALYTICS_TOOLS",
    "DEFI_TOOLS",
    "NFT_TOOLS",
    "DARKWEB_TOOLS",
    "AUTOMATION_TOOLS",
    "COLLAB_TOOLS",
    "DISCOVERY_TOOLS",
    # Individual tools
    "risk_score_tool",
    "bridge_lookup_tool",
    "trigger_alert_tool",
    "list_alert_rules_tool",
    "simulate_alerts_tool",
    "trace_address_tool",
    "code_extract_tool",
    "text_extract_tool",
    # Legacy aliases for tests
    "trace_address",
    "risk_score",
    "create_case",
    "get_available_cryptocurrencies",
    "create_crypto_payment",
    # Intelligence Network tools
    "intelligence_check_tool",
    "intelligence_flag_tool",
    "intelligence_confirm_flag_tool",
    "intelligence_list_flags_tool",
    "intelligence_stats_tool",
]
