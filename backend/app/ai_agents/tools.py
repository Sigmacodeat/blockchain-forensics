"""LangChain Tools for Blockchain Forensics"""

import logging
import asyncio
from typing import Optional, List, Dict, Any

# Ensure patch targets exist even if aliasing later fails
trace_address = None  # patched in tests
risk_score = None
create_case = None
get_available_cryptocurrencies = None
create_crypto_payment = None
from langchain.tools import tool
# LangChain StructuredTool erwartet Pydantic v1 BaseModel
# LangChain StructuredTool erwartet pydantic v1 Schemas
from pydantic.v1 import BaseModel, Field

from app.db import neo4j_client
from app.tracing import TraceRequest, TraceDirection, TaintModel
from app.enrichment import labels_service
from app.ml.risk_scorer import risk_scorer
from app.services.alert_service import alert_service, Alert, AlertType, AlertSeverity
from app.bridge.registry import bridge_registry
from app.config import settings
from app.ai_agents.performance.tool_cache import tool_cache
from app.ml.wallet_clustering import wallet_clusterer
from app.services.crypto_payments import crypto_payment_service
from app.db.postgres_client import postgres_client
import uuid
from app.services.evidence_vault import evidence_vault
from app.services.soar_engine import soar_engine

logger = logging.getLogger(__name__)

# Intelligence Network service & enums
from app.services.intelligence_sharing_service import (
    intelligence_sharing_service,
    FlagReason,
    InvestigatorTier,
    FlagStatus,
)
from app.services.demo_service import demo_service
from app.services.support_service import support_service


# Tool Input Schemas
class TraceAddressInput(BaseModel):
    """Input for trace_address tool"""
    address: str = Field(..., description="Ethereum address to trace (0x...)")
    max_depth: int = Field(default=5, description="Maximum trace depth (1-10)")
    direction: str = Field(default="forward", description="Trace direction: forward, backward, or both")
    from_timestamp: Optional[str] = Field(None, description="ISO timestamp start filter, e.g., 2021-01-01T00:00:00Z")
    to_timestamp: Optional[str] = Field(None, description="ISO timestamp end filter, e.g., 2023-12-31T23:59:59Z")
    min_taint_threshold: Optional[float] = Field(0.01, description="Minimum taint threshold (0-1) to propagate")
    max_nodes: Optional[int] = Field(1000, description="Max nodes to explore (1-10000)")
    enable_native: Optional[bool] = Field(True, description="Enable native (coin) flows")
    enable_token: Optional[bool] = Field(True, description="Enable token (ERC20/721/1155) flows")
    enable_bridge: Optional[bool] = Field(True, description="Enable cross-chain bridge expansion")
    enable_utxo: Optional[bool] = Field(True, description="Enable UTXO flows")
    native_decay: Optional[float] = Field(1.0, description="Decay factor for native flows (0-1)")
    token_decay: Optional[float] = Field(1.0, description="Decay factor for token flows (0-1)")
    bridge_decay: Optional[float] = Field(0.9, description="Decay factor for bridge expansion (0-1)")
    utxo_decay: Optional[float] = Field(1.0, description="Decay factor for UTXO flows (0-1)")


class QueryGraphInput(BaseModel):
    """Input for query_graph tool"""
    query: str = Field(..., description="Natural language query about the blockchain graph")
    address: Optional[str] = Field(None, description="Specific address to focus on")


class GetLabelsInput(BaseModel):
    """Input for get_labels tool"""
    address: str = Field(..., description="Address to get labels for")


class FindPathInput(BaseModel):
    """Input for find_path tool"""
    from_address: str = Field(..., description="Source address")
    to_address: str = Field(..., description="Destination address")
    max_hops: int = Field(default=5, description="Maximum path length")


class RiskScoreInput(BaseModel):
    """Input for risk_score tool"""
    address: str = Field(..., description="Blockchain address to score")


class BridgeLookupInput(BaseModel):
    """Input for bridge_lookup tool"""
    chain: Optional[str] = Field(default=None, description="Chain name, e.g., ethereum, polygon")
    address: Optional[str] = Field(default=None, description="Contract address to check (0x...)")
    method_selector: Optional[str] = Field(default=None, description="4-byte method selector, e.g., 0xa9059cbb")


class TriggerAlertInput(BaseModel):
    """Input for trigger_alert tool (event-based rule evaluation)"""
    alert_type: str = Field(..., description="Target rule to trigger: high_risk, sanctioned, large_transfer, mixer")
    address: Optional[str] = Field(default=None, description="Related address")
    tx_hash: Optional[str] = Field(default=None, description="Transaction hash if applicable")
    risk_score: Optional[float] = Field(default=None, description="Risk score for high_risk rule")
    labels: Optional[List[str]] = Field(default=None, description="Labels for sanctioned/mixer rules")
    value_usd: Optional[float] = Field(default=None, description="USD value for large_transfer rule")
    # manual alert fields (optional)
    severity: Optional[str] = Field(default=None, description="Severity: low|medium|high|critical")
    title: Optional[str] = Field(default=None, description="Alert title (manual mode)")
    description: Optional[str] = Field(default=None, description="Alert description (manual mode)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class CodeExtractInput(BaseModel):
    code: str = Field(..., description="Source code to extract information from")


class ContactSupportInput(BaseModel):
    """Input for contact_support tool"""
    name: str = Field(..., description="User's name")
    email: str = Field(..., description="User's email address")
    subject: str = Field(..., description="Support request subject")
    message: str = Field(..., description="Detailed description of the issue or question")
    urgency: Optional[str] = Field(None, description="Urgency level: low, medium, high, critical")
    language: Optional[str] = Field(None, description="Programming language, e.g., python, solidity")
    task: Optional[str] = Field(None, description="Optional extraction task hint, e.g., 'entities', 'functions'")


class TextExtractInput(BaseModel):
    text: str = Field(..., description="Free-form text to extract structured data from")
    task: Optional[str] = Field(None, description="Optional extraction task hint, e.g., 'ner', 'summary'")
    schema_: Optional[Dict[str, Any]] = Field(
        None,
        alias="schema",
        description="Optional JSON schema guiding the extraction"
    )


class ThreatIntelEnrichInput(BaseModel):
    """Input for threat_intel_enrich tool"""
    chain: str = Field(..., description="Blockchain name (ethereum, bitcoin, etc.)")
    address: str = Field(..., description="Address to enrich with threat intelligence")


class CommunityReportInput(BaseModel):
    """Input for submit_community_report tool"""
    chain: str = Field(..., description="Blockchain name")
    address: str = Field(..., description="Address to report")
    category: str = Field(..., description="Threat category: scam, phishing, ransomware, etc.")
    threat_level: str = Field(..., description="Threat level: critical, high, medium, low, info")
    title: str = Field(..., description="Report title")
    description: str = Field(..., description="Detailed description of the threat")

    class Config:
        allow_population_by_field_name = True


class AnalyzeCrossChainBridgeInput(BaseModel):
    """Input for analyze_cross_chain_bridge tool"""
    address: str = Field(..., description="Blockchain address to analyze for bridge activities")
    chain: str = Field(..., description="Primary chain of the address (ethereum, polygon, bsc, etc.)")
    max_depth: int = Field(default=3, description="Maximum bridge hop depth to analyze (1-5)")
    include_incoming: bool = Field(default=True, description="Include incoming bridge transfers")
    include_outgoing: bool = Field(default=True, description="Include outgoing bridge transfers")
    from_timestamp: Optional[str] = Field(None, description="Start timestamp for bridge analysis (ISO format)")
    to_timestamp: Optional[str] = Field(None, description="End timestamp for bridge analysis (ISO format)")
    min_value_usd: Optional[float] = Field(None, description="Minimum bridge transfer value in USD to include")


# ================================
# Intelligence Network: Input Schemas
# ================================
class IntelligenceCheckInput(BaseModel):
    """Input for intelligence_check tool"""
    address: str = Field(..., description="Blockchain address to check")
    chain: str = Field(..., description="Chain name (ethereum, bitcoin, polygon, etc.)")
    check_related: bool = Field(default=True, description="Also check related addresses")


class IntelligenceFlagInput(BaseModel):
    """Input for intelligence_flag tool"""
    address: str = Field(..., description="Address to flag")
    chain: str = Field(..., description="Chain name")
    reason: str = Field(..., description="Reason: hack, fraud, sanctions, ransomware, scam, mixer_abuse, terrorism_financing, money_laundering, other_illicit")
    description: str = Field(..., description="Detailed description (max ~2000 chars)")
    amount_usd: Optional[float] = Field(None, description="Estimated amount in USD")
    evidence: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Evidence list: [{type, value}]")
    related_addresses: Optional[List[str]] = Field(default_factory=list, description="Related addresses")
    auto_trace: bool = Field(default=True, description="Initiate auto-trace on flag")


class IntelligenceConfirmInput(BaseModel):
    """Input for intelligence_confirm_flag tool"""
    flag_id: str = Field(..., description="Flag ID to confirm")
    additional_evidence: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Additional evidence")


class IntelligenceListFlagsInput(BaseModel):
    """Input for intelligence_list_flags tool"""
    status: Optional[str] = Field(None, description="Filter by status: active, confirmed, disputed, resolved, expired")
    reason: Optional[str] = Field(None, description="Filter by reason")
    chain: Optional[str] = Field(None, description="Filter by chain")
    limit: int = Field(default=50, description="Max results (1-500)")
    offset: int = Field(default=0, description="Offset for pagination")


class IntelligenceRegisterInvestigatorInput(BaseModel):
    """Input for intelligence_register_investigator tool"""
    user_id: str = Field(..., description="Current user id for investigator mapping")
    org_name: str = Field(..., description="Organization name")
    tier: str = Field(..., description="Tier: verified_law_enforcement, verified_exchange, verified_security_firm, verified_analyst, community_trusted")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")


class IntelligenceRegisterMemberInput(BaseModel):
    """Input for intelligence_register_member tool"""
    user_id: str = Field(..., description="Current user id for member mapping")
    org_name: str = Field(..., description="Organization name")
    member_type: str = Field(..., description="exchange, defi, stablecoin_issuer, custodian")
    alert_webhook: Optional[str] = Field(None, description="Webhook URL for alerts")
    auto_freeze_enabled: bool = Field(default=False, description="Enable automatic freezing")


# ================================
# Intelligence Network: Tools
# ================================
@tool("intelligence_check", args_schema=IntelligenceCheckInput)
async def intelligence_check_tool(address: str, chain: str, check_related: bool = True) -> Dict[str, Any]:
    """
    Check an address against the Intelligence Network (direct + related flags),
    returning risk_score (0-1) and a recommended action (freeze/review/monitor/allow).
    """
    try:
        result = await intelligence_sharing_service.check_address_against_network(
            address=address,
            chain=chain,
            check_related=check_related,
        )
        return result
    except Exception as e:
        logger.error(f"Error in intelligence_check_tool: {e}")
        return {"error": str(e)}


@tool("intelligence_flag", args_schema=IntelligenceFlagInput)
async def intelligence_flag_tool(
    address: str,
    chain: str,
    reason: str,
    description: str,
    amount_usd: Optional[float] = None,
    evidence: Optional[List[Dict[str, Any]]] = None,
    related_addresses: Optional[List[str]] = None,
    auto_trace: bool = True,
) -> Dict[str, Any]:
    """
    Create a new intelligence flag for an address with optional evidence and auto-trace.
    Requires that the caller is (or maps to) a registered investigator.
    """
    try:
        # In agent-context, we map to a synthetic investigator id. In real use, pass from session.
        investigator_id = "inv-agent"
        # Ensure default investigator exists for robustness
        if investigator_id not in intelligence_sharing_service.investigators:
            await intelligence_sharing_service.register_investigator(
                investigator_id=investigator_id,
                org_name="AI Agent",
                tier=InvestigatorTier.COMMUNITY_TRUSTED,
                verification_docs=None,
                contact_info={}
            )

        # Map reason string to enum; be permissive with common aliases
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

        flag = await intelligence_sharing_service.flag_address(
            address=address,
            chain=chain,
            reason=r,
            investigator_id=investigator_id,
            incident_id=None,
            amount_usd=amount_usd,
            description=description,
            evidence=evidence or [],
            related_addresses=related_addresses or [],
            auto_trace=auto_trace,
        )
        return flag
    except Exception as e:
        logger.error(f"Error in intelligence_flag_tool: {e}")
        return {"error": str(e)}


@tool("intelligence_confirm_flag", args_schema=IntelligenceConfirmInput)
async def intelligence_confirm_flag_tool(flag_id: str, additional_evidence: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Confirm an existing intelligence flag, optionally adding more evidence.
    Auto-confirms after 3+ trusted confirmations.
    """
    try:
        investigator_id = "inv-agent"
        if investigator_id not in intelligence_sharing_service.investigators:
            await intelligence_sharing_service.register_investigator(
                investigator_id=investigator_id,
                org_name="AI Agent",
                tier=InvestigatorTier.COMMUNITY_TRUSTED,
                verification_docs=None,
                contact_info={}
            )
        flag = await intelligence_sharing_service.confirm_flag(
            flag_id=flag_id,
            investigator_id=investigator_id,
            additional_evidence=additional_evidence or [],
        )
        return flag
    except Exception as e:
        logger.error(f"Error in intelligence_confirm_flag_tool: {e}")
        return {"error": str(e)}


@tool("intelligence_list_flags", args_schema=IntelligenceListFlagsInput)
async def intelligence_list_flags_tool(
    status: Optional[str] = None,
    reason: Optional[str] = None,
    chain: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List flags from the Intelligence Network with optional filters and pagination.
    """
    try:
        flags = list(intelligence_sharing_service.flags_db.values())
        if status:
            # accept both API status and service enums
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
    except Exception as e:
        logger.error(f"Error in intelligence_list_flags_tool: {e}")
        return {"error": str(e)}


@tool("intelligence_stats")
async def intelligence_stats_tool() -> Dict[str, Any]:
    """
    Get Intelligence Network statistics (investigators, members, flags, amounts, effectiveness).
    """
    try:
        stats = await intelligence_sharing_service.get_network_stats()
        return stats
    except Exception as e:
        logger.error(f"Error in intelligence_stats_tool: {e}")
        return {"error": str(e)}


@tool("intelligence_register_investigator", args_schema=IntelligenceRegisterInvestigatorInput)
async def intelligence_register_investigator_tool(user_id: str, org_name: str, tier: str, contact_email: Optional[str] = None, contact_phone: Optional[str] = None) -> Dict[str, Any]:
    """
    Register current user as a verified investigator in the Intelligence Network.
    """
    try:
        tmap = {
            "verified_law_enforcement": InvestigatorTier.VERIFIED_LAW_ENFORCEMENT,
            "verified_exchange": InvestigatorTier.VERIFIED_EXCHANGE,
            "verified_security_firm": InvestigatorTier.VERIFIED_SECURITY_FIRM,
            "verified_analyst": InvestigatorTier.VERIFIED_ANALYST,
            "community_trusted": InvestigatorTier.COMMUNITY_TRUSTED,
        }
        t = tmap.get(tier.lower())
        if not t:
            return {"error": f"Unsupported tier: {tier}"}

        inv = await intelligence_sharing_service.register_investigator(
            investigator_id=f"inv-{user_id}",
            org_name=org_name,
            tier=t,
            verification_docs=None,
            contact_info={"email": contact_email or "", "phone": contact_phone or ""},
        )
        return inv
    except Exception as e:
        logger.error(f"Error in intelligence_register_investigator_tool: {e}")
        return {"error": str(e)}


@tool("intelligence_register_member", args_schema=IntelligenceRegisterMemberInput)
async def intelligence_register_member_tool(user_id: str, org_name: str, member_type: str, alert_webhook: Optional[str] = None, auto_freeze_enabled: bool = False) -> Dict[str, Any]:
    """
    Register an organization as a network member (exchange, DeFi, stablecoin issuer, custodian).
    """
    try:
        member = await intelligence_sharing_service.register_network_member(
            member_id=f"member-{user_id}",
            org_name=org_name,
            member_type=member_type,
            alert_webhook=alert_webhook,
            auto_freeze_enabled=auto_freeze_enabled,
        )
        return member
    except Exception as e:
        logger.error(f"Error in intelligence_register_member_tool: {e}")
        return {"error": str(e)}


class SimulateAlertsInput(BaseModel):
    """Input for simulate_alerts tool"""
    address: Optional[str] = Field(default=None, description="Subject address")
    tx_hash: Optional[str] = Field(default=None, description="Transaction hash if applicable")
    from_address: Optional[str] = Field(default=None, description="Sender address")
    to_address: Optional[str] = Field(default=None, description="Recipient address")
    value_usd: Optional[float] = Field(default=0, description="Transfer value in USD")
    risk_score: Optional[float] = Field(default=0.0, description="Precomputed risk score (0-1)")
    labels: Optional[List[str]] = Field(default_factory=list, description="Known labels for the address")
    # passthrough for bridge/cross-chain/time-window
    event_type: Optional[str] = Field(default=None, description="Optional event type, e.g., 'bridge'")
    bridge: Optional[str] = Field(default=None, description="Bridge name/id if applicable")
    chains_involved: Optional[int] = Field(default=None, description="Number of chains involved in exposure")
    cross_chain_hops: Optional[int] = Field(default=None, description="Hop distance across chains")
    from_timestamp: Optional[str] = Field(default=None, description="Start of time window (ISO)")
    to_timestamp: Optional[str] = Field(default=None, description="End of time window (ISO)")


# Forensic Tools
@tool("agent_health")
async def agent_health_tool() -> Dict[str, Any]:
    """
    Return basic health and configuration information about the AI agent subsystem.
    Useful for quick diagnostics and observability from within the agent runtime.
    """
    try:
        # dynamisch zur Laufzeit, um Zirkularitätsprobleme zu vermeiden
        tools_count = 0
        try:
            from app.ai_agents.tools import FORENSIC_TOOLS as _TOOLS
            tools_count = len(_TOOLS) if _TOOLS else 0
        except Exception:
            pass

        return {
            "enabled": getattr(settings, "ENABLE_AI_AGENTS", False),
            "tools_registered": tools_count,
            "model": getattr(settings, "OPENAI_MODEL", "unknown"),
        }
    except Exception as e:
        logger.error(f"Error in agent_health_tool: {e}")
        return {"error": str(e)}


@tool("code_extract", args_schema=CodeExtractInput)
async def code_extract_tool(code: str, language: Optional[str] = None, task: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform structured extraction from source code via the external Kilo/Grok service.
    Inputs: code (required), optional language hint (e.g., 'python', 'solidity'), optional task hint.
    Returns provider JSON with extracted entities/summary.
    """
    try:
        from app.services.extraction_service import ExtractionService
        service = ExtractionService()
        return service.extract_from_code(code, language=language, task=task)
    except Exception as e:
        logger.error(f"Error in code_extract_tool: {e}")
        return {"error": str(e)}


@tool("text_extract", args_schema=TextExtractInput)
async def text_extract_tool(text: str, task: Optional[str] = None, schema_: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Perform structured extraction from free-form text via the external Kilo/Grok service.
    Inputs: text (required), optional task hint, optional JSON schema guiding the extraction.
    Returns provider JSON with extracted entities/summary.
    """
    try:
        from app.services.extraction_service import ExtractionService
        service = ExtractionService()
        return service.extract_from_text(text, schema=schema_, task=task)
    except Exception as e:
        logger.error(f"Error in text_extract_tool: {e}")
        return {"error": str(e)}


@tool("trace_address", args_schema=TraceAddressInput)
async def trace_address_tool(
    address: str,
    max_depth: int = 5,
    direction: str = "forward",
    from_timestamp: Optional[str] = None,
    to_timestamp: Optional[str] = None,
    min_taint_threshold: Optional[float] = 0.01,
    max_nodes: Optional[int] = 1000,
    enable_native: Optional[bool] = True,
    enable_token: Optional[bool] = True,
    enable_bridge: Optional[bool] = True,
    enable_utxo: Optional[bool] = True,
    native_decay: Optional[float] = 1.0,
    token_decay: Optional[float] = 1.0,
    bridge_decay: Optional[float] = 0.9,
    utxo_decay: Optional[float] = 1.0,
) -> Dict[str, Any]:
    """
    Trace blockchain transactions from an address to find money flows.
    Useful for investigating fund movements, identifying recipients, and discovering connections.
    
    Returns detailed trace results including all addresses involved, transaction amounts, and risk indicators.
    """
    try:
        from app.tracing import TransactionTracer
        from app.db import neo4j_client
        
        # Create trace request
        trace_direction = TraceDirection(direction.lower())
        request = TraceRequest(
            source_address=address,
            direction=trace_direction,
            max_depth=max_depth,
            taint_model=TaintModel.PROPORTIONAL,
            start_timestamp=from_timestamp,
            end_timestamp=to_timestamp,
            min_taint_threshold=min_taint_threshold if min_taint_threshold is not None else 0.01,
            max_nodes=max_nodes if max_nodes is not None else 1000,
            enable_native=enable_native if enable_native is not None else True,
            enable_token=enable_token if enable_token is not None else True,
            enable_bridge=enable_bridge if enable_bridge is not None else True,
            enable_utxo=enable_utxo if enable_utxo is not None else True,
            native_decay=native_decay if native_decay is not None else 1.0,
            token_decay=token_decay if token_decay is not None else 1.0,
            bridge_decay=bridge_decay if bridge_decay is not None else 0.9,
            utxo_decay=utxo_decay if utxo_decay is not None else 1.0,
        )
        
        # Execute trace
        tracer = TransactionTracer(db_client=neo4j_client)
        result = await tracer.trace(request)
        
        # Format results for LLM
        key_findings: List[str] = []
        summary: Dict[str, Any] = {
            "trace_id": result.trace_id,
            "source_address": result.source_address,
            "total_addresses_found": result.total_nodes,
            "total_transactions": result.total_edges,
            "max_depth_reached": result.max_hop_reached,
            "high_risk_addresses": result.high_risk_addresses,
            "sanctioned_addresses": result.sanctioned_addresses,
            "execution_time": result.execution_time_seconds,
            "key_findings": key_findings
        }
        
        # Add key findings
        if result.sanctioned_addresses:
            key_findings.append(
                f"Found {len(result.sanctioned_addresses)} sanctioned addresses (OFAC list)"
            )
        
        if result.high_risk_addresses:
            key_findings.append(
                f"Identified {len(result.high_risk_addresses)} high-risk addresses"
            )
        
        # Top tainted transactions
        top_txs = sorted(
            result.tainted_transactions,
            key=lambda x: x.taint_score,
            reverse=True
        )[:5]
        
        summary["top_tainted_transactions"] = [
            {
                "tx_hash": tx.tx_hash,
                "from": tx.from_address,
                "to": tx.to_address,
                "value": str(tx.value),
                "taint_score": tx.taint_score,
                "hop": tx.hop_distance
            }
            for tx in top_txs
        ]
        
        return summary
        
    except Exception as e:
        logger.error(f"Error in trace_address_tool: {e}")
        return {"error": str(e)}


@tool("list_alert_rules")
async def list_alert_rules_tool() -> Dict[str, Any]:
    """
    List available alert rules and their metadata from the real-time Alert Engine.
    Useful to understand current detection capabilities before running simulations.
    """
    try:
        rules_info = []
        for r in alert_service.list_rules():
            rules_info.append({
                "rule_id": getattr(r, "rule_id", type(r).__name__),
                "name": getattr(r, "name", type(r).__name__),
                "enabled": getattr(r, "enabled", True)
            })
        return {"rules": rules_info, "total": len(rules_info)}
    except Exception as e:
        logger.error(f"Error in list_alert_rules_tool: {e}")
        return {"error": str(e)}


@tool("simulate_alerts", args_schema=SimulateAlertsInput)
async def simulate_alerts_tool(
    address: Optional[str] = None,
    tx_hash: Optional[str] = None,
    from_address: Optional[str] = None,
    to_address: Optional[str] = None,
    value_usd: Optional[float] = 0,
    risk_score: Optional[float] = 0.0,
    labels: Optional[List[str]] = None,
    event_type: Optional[str] = None,
    bridge: Optional[str] = None,
    chains_involved: Optional[int] = None,
    cross_chain_hops: Optional[int] = None,
    from_timestamp: Optional[str] = None,
    to_timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Simulate the Alert Engine against a provided event payload to see which rules would trigger.
    Provide any combination of address, labels, risk_score, value_usd, and tx context.
    Returns the list of triggered alerts with details.
    """
    try:
        event: Dict[str, Any] = {
            "address": address,
            "tx_hash": tx_hash,
            "from_address": from_address,
            "to_address": to_address,
            "value_usd": value_usd or 0,
            "risk_score": risk_score or 0.0,
            "labels": labels or [],
        }
        # passthrough optional fields
        if isinstance(event, dict):
            # add only if provided
            extras = {
                "event_type": locals().get("event_type"),
                "bridge": locals().get("bridge"),
                "chains_involved": locals().get("chains_involved"),
                "cross_chain_hops": locals().get("cross_chain_hops"),
                "from_timestamp": locals().get("from_timestamp"),
                "to_timestamp": locals().get("to_timestamp"),
            }
            for k, v in extras.items():
                if v is not None:
                    event[k] = v

        triggered = await alert_service.process_event(event)
        return {
            "event": {k: v for k, v in event.items() if v is not None},
            "triggered_count": len(triggered),
            "alerts": [a.to_dict() for a in triggered],
        }
    except Exception as e:
        logger.error(f"Error in simulate_alerts_tool: {e}")
        return {"error": str(e)}


@tool("risk_score", args_schema=RiskScoreInput)
async def risk_score_tool(address: str) -> Dict[str, Any]:
    """
    Calculate the risk score for a given address using the ML/heuristic RiskScorer.
    Returns risk_score (0-1), risk_level, factors and confidence.
    """
    try:
        # Try cache first (L1/L2)
        cached = await tool_cache.get("risk_score_tool", (address,), {}, use_l1=True, use_l2=True, use_l3=False)
        if cached is not None:
            return cached
        # Fast fail to avoid hanging backends
        result = await asyncio.wait_for(risk_scorer.calculate_risk_score(address), timeout=2.5)
        value = {"address": address, **result}
        # Store asynchronously (fire-and-forget)
        asyncio.create_task(tool_cache.set("risk_score_tool", (address,), {}, value, ttl=600, use_l1=True, use_l2=True, use_l3=False))
        return value
    except Exception as e:
        logger.error(f"Error in risk_score_tool: {e}")
        return {"error": str(e)}


@tool("query_graph", args_schema=QueryGraphInput)
async def query_graph_tool(query: str, address: Optional[str] = None) -> Dict[str, Any]:
    """
    Query the blockchain graph database to answer questions about addresses and transactions.
    Can find neighbors, connections, transaction patterns, and relationships.
    
    Examples:
    - "Show me all addresses that received funds from 0x123..."
    - "Find connections between address A and address B"
    - "What are the top senders to this address?"
    """
    try:
        result: Dict[str, Any] = {}
        
        if address:
            # Cache per address and query
            cached = await tool_cache.get("query_graph_tool", (query, address), {}, use_l1=True, use_l2=True, use_l3=False)
            if cached is not None:
                return cached
            # Execute graph queries in parallel with timeout
            neighbors_coro = neo4j_client.get_address_neighbors(
                address,
                direction="both",
                limit=50
            )
            risky_coro = neo4j_client.get_high_risk_connections(address)
            neighbors, risky = await asyncio.wait_for(
                asyncio.gather(neighbors_coro, risky_coro, return_exceptions=False),
                timeout=3.0,
            )
            result["address"] = address
            result["total_neighbors"] = len(neighbors)
            result["top_connections"] = neighbors[:10]
            if risky:
                result["high_risk_connections"] = risky
                result["warning"] = f"Found {len(risky)} connections to high-risk addresses"
            # Cache result
            asyncio.create_task(tool_cache.set("query_graph_tool", (query, address), {}, result, ttl=180, use_l1=True, use_l2=True, use_l3=False))
        
        return result if result else {"message": "Query processed, but no specific results"}
        
    except Exception as e:
        logger.error(f"Error in query_graph_tool: {e}")
        return {"error": str(e)}


@tool("get_labels", args_schema=GetLabelsInput)
async def get_labels_tool(address: str) -> Dict[str, Any]:
    """
    Get all known labels and classifications for a blockchain address.
    Returns information like: exchange, sanctioned, scam, mixer, etc.
    
    Essential for risk assessment and entity identification.
    """
    try:
        # Try cache first
        cached = await tool_cache.get("get_labels_tool", (address,), {}, use_l1=True, use_l2=True, use_l3=False)
        if cached is not None:
            return cached
        # Parallelize label lookups with timeout
        labels_coro = labels_service.get_labels(address)
        category_coro = labels_service.get_category(address)
        risky_coro = labels_service.is_high_risk(address)
        labels, category, is_risky = await asyncio.wait_for(
            asyncio.gather(labels_coro, category_coro, risky_coro, return_exceptions=False),
            timeout=2.5,
        )
        
        value = {
            "address": address,
            "labels": labels,
            "category": category,
            "is_high_risk": is_risky,
            "risk_factors": [l for l in labels if l in ["sanctioned", "scam", "mixer", "darknet"]]
        }
        asyncio.create_task(tool_cache.set("get_labels_tool", (address,), {}, value, ttl=900, use_l1=True, use_l2=True, use_l3=False))
        return value
        
    except Exception as e:
        logger.error(f"Error in get_labels_tool: {e}")
        return {"error": str(e)}


@tool("find_path", args_schema=FindPathInput)
async def find_path_tool(from_address: str, to_address: str, max_hops: int = 5) -> Dict[str, Any]:
    """
    Find the shortest path between two addresses in the transaction graph.
    Useful for establishing connections and tracing fund flows between entities.
    
    Returns the path of addresses and transactions connecting the two addresses.
    """
    try:
        # Cache per (from,to,max_hops)
        cache_key_args = (from_address, to_address, max_hops)
        cached = await tool_cache.get("find_path_tool", cache_key_args, {}, use_l1=True, use_l2=True, use_l3=False)
        if cached is not None:
            return cached
        paths = await asyncio.wait_for(neo4j_client.find_path(from_address, to_address, max_hops), timeout=3.0)
        
        if not paths:
            return {
                "found": False,
                "message": f"No path found between {from_address} and {to_address} within {max_hops} hops"
            }
        
        value = {
            "found": True,
            "from_address": from_address,
            "to_address": to_address,
            "path": paths[0] if isinstance(paths, list) else paths
        }
        asyncio.create_task(tool_cache.set("find_path_tool", cache_key_args, {}, value, ttl=900, use_l1=True, use_l2=True, use_l3=False))
        return value
        
    except Exception as e:
        logger.error(f"Error in find_path_tool: {e}")
        return {"error": str(e)}


 


@tool("bridge_lookup", args_schema=BridgeLookupInput)
async def bridge_lookup_tool(
    chain: Optional[str] = None,
    address: Optional[str] = None,
    method_selector: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Query the Bridge Registry to identify bridge contracts and methods.
    - Provide chain+address to get contract info
    - Provide method_selector to check if it belongs to a known bridge
    - Provide chain only to list all registered bridges on that chain
    """
    try:
        out: Dict[str, Any] = {"ok": True}

        if method_selector:
            out["is_bridge_method"] = bridge_registry.is_bridge_method(method_selector)

        if address and chain:
            out["is_bridge_contract"] = bridge_registry.is_bridge_contract(address, chain)
            contract = bridge_registry.get_contract(address, chain)
            if contract:
                out["contract"] = {
                    "address": contract.address,
                    "chain": contract.chain,
                    "name": contract.name,
                    "bridge_type": contract.bridge_type,
                    "counterpart_chains": contract.counterpart_chains,
                    "method_selectors": contract.method_selectors,
                    "added_at": contract.added_at.isoformat(),
                }

        if chain and not address:
            contracts = bridge_registry.get_contracts_by_chain(chain)
            out["contracts"] = [
                {
                    "address": c.address,
                    "name": c.name,
                    "bridge_type": c.bridge_type,
                    "method_selectors": c.method_selectors,
                }
                for c in contracts
            ]

        stats = bridge_registry.get_stats()
        out["stats"] = stats
        # Back-compat and tests expectation
        if "contracts" in out and "contracts_by_chain" not in out:
            out["contracts_by_chain"] = out["contracts"]
        out["registry_stats"] = stats
        return out
    except Exception as e:
        logger.error(f"Error in bridge_lookup_tool: {e}")
        return {"error": str(e)}


@tool("trigger_alert", args_schema=TriggerAlertInput)
async def trigger_alert_tool(
    alert_type: str,
    address: Optional[str] = None,
    tx_hash: Optional[str] = None,
    risk_score: Optional[float] = None,
    labels: Optional[List[str]] = None,
    value_usd: Optional[float] = None,
    severity: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create and dispatch an alert directly via the AlertEngine (manual mode) if title/description provided,
    otherwise fall back to rule-evaluation event (synthetic) for convenience.
    """
    try:
        # Manual mode preferred if title/description present
        if title and description:
            atype = AlertType(alert_type) if alert_type in AlertType._value2member_map_ else AlertType.SUSPICIOUS_PATTERN
            sev = AlertSeverity(severity) if severity in AlertSeverity._value2member_map_ else AlertSeverity.MEDIUM
            alert = Alert(
                alert_type=atype,
                severity=sev,
                title=title,
                description=description,
                metadata=metadata or {},
                address=address,
                tx_hash=tx_hash,
            )
            await alert_service.dispatch_manual_alert(alert)
            return {"alert": alert.to_dict(), "success": True}

        # Fallback: evaluate rules on synthetic event
        event: Dict[str, Any] = {}
        if alert_type == "high_risk":
            event.update({
                "address": address,
                "risk_score": risk_score if risk_score is not None else 0.71,
                "risk_factors": labels or [],
            })
        elif alert_type == "sanctioned":
            event.update({
                "address": address,
                "labels": labels or ["sanctioned"],
            })
        elif alert_type == "large_transfer":
            event.update({
                "tx_hash": tx_hash,
                "from_address": address,
                "to_address": address,
                "value_usd": value_usd if value_usd is not None else 100000.0,
            })
        elif alert_type == "mixer":
            event.update({
                "address": address,
                "tx_hash": tx_hash,
                "labels": labels or ["mixer"],
            })
        else:
            return {"error": f"Unsupported alert_type: {alert_type}"}

        alerts = await alert_service.process_event(event)
        return {
            "submitted_event": event,
            "alerts_triggered": [a.to_dict() for a in alerts],
            "count": len(alerts),
            "success": True,
        }
    except Exception as e:
        logger.error(f"Error in trigger_alert_tool: {e}")
class AdvancedTraceInput(BaseModel):
    """Input for advanced_trace tool"""
    address: str = Field(..., description="Address to trace")
    max_depth: int = Field(default=10, description="Max trace depth")
    include_clusters: bool = Field(default=True, description="Include cluster analysis")
    include_cross_chain: bool = Field(default=True, description="Include cross-chain links")
    risk_threshold: float = Field(default=0.5, description="Risk threshold for filtering")
    output_format: str = Field(default="summary", description="Output format: summary, detailed, graph")


class ClusterAnalysisInput(BaseModel):
    """Input for cluster_analysis tool"""
    addresses: List[str] = Field(..., description="List of addresses to analyze")
    max_depth: int = Field(default=3, description="Clustering depth")
    min_cluster_size: int = Field(default=2, description="Minimum cluster size")


class CrossChainAnalysisInput(BaseModel):
    """Input for cross_chain_analysis tool"""
    address: str = Field(..., description="Address to analyze")
    chains: List[str] = Field(default_factory=list, description="Specific chains to analyze")
    max_hops: int = Field(default=5, description="Max cross-chain hops")


@tool("advanced_trace", args_schema=AdvancedTraceInput)
async def advanced_trace_tool(
    address: str,
    max_depth: int = 10,
    include_clusters: bool = True,
    include_cross_chain: bool = True,
    risk_threshold: float = 0.5,
    output_format: str = "summary",
) -> Dict[str, Any]:
    """
    Advanced tracing with clustering and cross-chain analysis.
    Premium feature: Provides comprehensive tracing with risk filtering and cluster insights.
    """
    try:
        from app.tracing import TransactionTracer
        from app.db import neo4j_client

        # Basic trace
        request = TraceRequest(
            source_address=address,
            direction=TraceDirection.BOTH,
            max_depth=max_depth,
            taint_model=TaintModel.PROPORTIONAL,
            min_taint_threshold=0.01,
            max_nodes=5000,
            enable_native=True,
            enable_token=True,
            enable_bridge=True,
            enable_utxo=True,
        )
        tracer = TransactionTracer(db_client=neo4j_client)
        basic_result = await tracer.trace(request)

        result = {
            "trace_id": basic_result.trace_id,
            "source_address": address,
            "total_addresses": basic_result.total_nodes,
            "total_transactions": basic_result.total_edges,
            "high_risk_count": len(basic_result.high_risk_addresses),
            "sanctioned_count": len(basic_result.sanctioned_addresses),
        }

        # Add clustering if requested
        if include_clusters:
            try:
                clusters = await wallet_clusterer.cluster_addresses([address], depth=2)
                result["clusters"] = {k: len(v) for k, v in clusters.items()}
            except Exception as e:
                result["cluster_error"] = str(e)

        # Add cross-chain if requested
        if include_cross_chain:
            try:
                cross_chain_data = await neo4j_client.get_cross_chain_summary(address)
                result["cross_chain"] = cross_chain_data
            except Exception as e:
                result["cross_chain_error"] = str(e)

        # Format output
        if output_format == "detailed":
            result["tainted_transactions"] = [
                {"tx_hash": tx.tx_hash, "taint_score": tx.taint_score, "hop": tx.hop_distance}
                for tx in basic_result.tainted_transactions[:10]
            ]
        elif output_format == "graph":
            # Simplified graph representation
            result["graph_nodes"] = [{"id": addr, "type": "address"} for addr in basic_result.addresses_found[:50]]
            result["graph_edges"] = [{"source": tx.from_address, "target": tx.to_address, "type": "transaction"} for tx in basic_result.tainted_transactions[:20]]

        return result
    except Exception as e:
        logger.error(f"Error in advanced_trace_tool: {e}")
        return {"error": str(e)}


@tool("cluster_analysis", args_schema=ClusterAnalysisInput)
async def cluster_analysis_tool(addresses: List[str], max_depth: int = 3, min_cluster_size: int = 2) -> Dict[str, Any]:
    """
    Analyze clusters for given addresses.
    Premium feature: Identifies wallet clusters and their characteristics.
    """
    try:
        clusters = await wallet_clusterer.cluster_addresses(addresses, depth=max_depth)
        filtered_clusters = {k: v for k, v in clusters.items() if len(v) >= min_cluster_size}

        stats = {}
        for cid, members in filtered_clusters.items():
            try:
                stats[cid] = await wallet_clusterer.calculate_cluster_stats(cid)
            except Exception as e:
                stats[cid] = {"cluster_id": cid, "size": len(members), "error": str(e)}

        return {
            "total_clusters": len(filtered_clusters),
            "clusters": {k: {"size": len(v), "members": v} for k, v in filtered_clusters.items()},
            "stats": stats,
        }
    except Exception as e:
        logger.error(f"Error in cluster_analysis_tool: {e}")
        return {"error": str(e)}


@tool("cross_chain_analysis", args_schema=CrossChainAnalysisInput)
async def cross_chain_analysis_tool(
    address: str,
    chains: List[str] = None,
    max_hops: int = 5,
) -> Dict[str, Any]:
    """
    Analyze cross-chain connections for an address.
    Premium feature: Provides insights into multi-chain activities.
    """
    try:
        # Get cross-chain summary
        summary = await neo4j_client.get_cross_chain_summary(address)

        # Get cross-chain neighbors if chains specified
        neighbors = []
        if chains:
            for chain in chains:
                chain_neighbors = await neo4j_client.get_address_neighbors(address, chain=chain, limit=50)
                neighbors.extend(chain_neighbors)

        # Get paths if max_hops > 0
        paths = []
        if max_hops > 0:
            try:
                paths = await neo4j_client.find_cross_chain_paths(address, max_hops)
            except Exception as e:
                logger.warning(f"Could not get cross-chain paths: {e}")

        return {
            "address": address,
            "summary": summary,
            "neighbors": neighbors[:100],  # Limit for performance
            "paths": paths[:10],  # Limit for performance
        }
    except Exception as e:
        logger.error(f"Error in cross_chain_analysis_tool: {e}")
        return {"error": str(e)}


@tool("threat_intel_enrich", args_schema=ThreatIntelEnrichInput)
async def threat_intel_enrich_tool(chain: str, address: str) -> Dict[str, Any]:
    """
    Enrich an address with threat intelligence from multiple sources.
    Returns threat scores, risk factors, and recommended actions.
    Sources: dark web monitoring, community reports, public feeds, law enforcement.
    """
    try:
        from app.intel.service import get_threat_intel_service
        
        service = get_threat_intel_service()
        result = await service.enrich_address(chain=chain, address=address)
        
        return {
            "chain": result.chain,
            "address": result.address,
            "threat_score": result.threat_score,
            "confidence": result.confidence,
            "threat_level": result.highest_threat_level,
            "categories": result.categories,
            "sources": result.sources,
            "recommended_action": result.recommended_action,
            "risk_factors": result.risk_factors,
            "matches_count": len(result.matches),
            "enriched_at": result.enriched_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error in threat_intel_enrich_tool: {e}")
        return {"error": str(e)}


@tool("submit_community_report", args_schema=CommunityReportInput)
async def submit_community_report_tool(
    chain: str,
    address: str,
    category: str,
    threat_level: str,
    title: str,
    description: str
) -> Dict[str, Any]:
    """
    Submit a community intelligence report for a suspicious address.
    Reports are verified by analysts before becoming active intelligence.
    Similar to Chainalysis Signals network.
    """
    try:
        from app.intel.service import get_threat_intel_service
        from app.intel.models import IntelCategory, ThreatLevel
        
        # Map string to enum
        category_map = {
            "scam": IntelCategory.SCAM,
            "phishing": IntelCategory.PHISHING,
            "ransomware": IntelCategory.RANSOMWARE,
            "darknet_market": IntelCategory.DARKNET_MARKET,
            "mixer": IntelCategory.MIXER,
            "stolen_funds": IntelCategory.STOLEN_FUNDS,
            "hack": IntelCategory.HACK,
            "fraud": IntelCategory.FRAUD,
            "money_laundering": IntelCategory.MONEY_LAUNDERING
        }
        
        level_map = {
            "critical": ThreatLevel.CRITICAL,
            "high": ThreatLevel.HIGH,
            "medium": ThreatLevel.MEDIUM,
            "low": ThreatLevel.LOW,
            "info": ThreatLevel.INFO
        }
        
        service = get_threat_intel_service()
        report = await service.submit_community_report(
            reporter_id="ai_agent",  # AI agent as reporter
            chain=chain,
            address=address,
            category=category_map.get(category.lower(), IntelCategory.FRAUD),
            threat_level=level_map.get(threat_level.lower(), ThreatLevel.MEDIUM),
            title=title,
            description=description,
            evidence={"source": "ai_agent"}
        )
        
        return {
            "report_id": report.id,
            "status": report.status,
            "chain": report.chain,
            "address": report.address,
            "category": report.category,
            "threat_level": report.threat_level,
            "submitted_at": report.submitted_at.isoformat(),
            "message": "Report submitted successfully and pending verification"
        }
    except Exception as e:
        logger.error(f"Error in submit_community_report_tool: {e}")
        return {"error": str(e)}


# ================================
# SOAR & Evidence Tools
# ================================
class WriteEvidenceInput(BaseModel):
    """Input for write_evidence tool"""
    event_type: str = Field(..., description="Event type for evidence chain")
    payload: Any = Field(..., description="Evidence payload (JSON-serializable)")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")


@tool("write_evidence", args_schema=WriteEvidenceInput)
async def write_evidence_tool(event_type: str, payload: Any, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Append a new record to the court-admissible Evidence Vault (append-only, signed, optionally anchored on-chain).
    Use this to persist investigation artifacts, alerts, audit events or chain-of-custody data.
    """
    try:
        rec = await evidence_vault.append(event_type, payload, meta or {})
        return {"success": True, "record": rec}
    except Exception as e:
        logger.error(f"Error in write_evidence_tool: {e}")
        return {"error": str(e)}


class RunPlaybooksInput(BaseModel):
    """Input for run_playbooks tool"""
    event: Dict[str, Any] = Field(..., description="Event context for playbook evaluation/execution")
    evaluate_only: bool = Field(default=False, description="If true, only evaluate matches without executing actions")


@tool("run_playbooks", args_schema=RunPlaybooksInput)
async def run_playbooks_tool(event: Dict[str, Any], evaluate_only: bool = False) -> Dict[str, Any]:
    """
    Evaluate and optionally execute SOAR playbooks for a given event.
    Returns matches (and action results when executed).
    """
    try:
        if evaluate_only:
            res = soar_engine.evaluate_only(event)
        else:
            res = soar_engine.run(event)
        return res
    except Exception as e:
        logger.error(f"Error in run_playbooks_tool: {e}")
        return {"error": str(e)}


# ============================================================================
# Crypto Payment Tools
# ============================================================================

class GetAvailableCurrenciesInput(BaseModel):
    """Input for getting available cryptocurrencies"""
    pass


@tool("get_available_cryptocurrencies", args_schema=GetAvailableCurrenciesInput, return_direct=False)
async def get_available_cryptocurrencies_tool() -> str:
    """
    Get list of all available cryptocurrencies for payments.
    Use this when user asks about payment options or which coins are supported.
    Returns list of 30+ cryptocurrencies with names and symbols.
    """
    try:
        currencies = await crypto_payment_service.get_available_currencies()
        
        result = "📋 **Verfügbare Kryptowährungen** (30+):\n\n**Top Cryptos:**\n"
        popular = ["btc", "eth", "usdt", "usdc", "bnb", "sol", "matic", "avax"]
        for curr in popular:
            if curr in currencies:
                info = crypto_payment_service.get_currency_info(curr)
                result += f"- {info['logo']} **{info['name']}** ({info['symbol'].upper()})\n"
        
        result += f"\n... und {len(currencies) - len(popular)} weitere Coins!\n"
        result += "\n💡 Du kannst mit jeder dieser Währungen bezahlen!"
        return result
    except Exception as e:
        logger.error(f"Error getting currencies: {e}")
        return "❌ Fehler beim Abrufen der Währungen."


class RecommendBestCurrencyInput(BaseModel):
    """Input for recommending best cryptocurrency"""
    plan: str = Field(..., description="Subscription plan (e.g., 'pro', 'business', 'plus')")


@tool("recommend_best_currency", args_schema=RecommendBestCurrencyInput, return_direct=False)
async def recommend_best_currency_tool(plan: str) -> str:
    """
    Recommends the most cost-effective cryptocurrency for payment.
    Considers transaction speed, fees, and liquidity.
    Use when user asks 'Which coin should I use?' or 'What's cheapest?'.
    Returns top 3 recommendations with reasons.
    """
    try:
        price_usd = crypto_payment_service.PLAN_PRICES.get(plan.lower())
        if not price_usd:
            return f"❌ Plan '{plan}' nicht gefunden."
        
        # Top currencies to compare
        currencies = ["usdt", "usdc", "eth", "matic", "sol", "bnb"]
        recommendations = []
        
        for curr in currencies:
            try:
                estimate = await crypto_payment_service.get_estimate(
                    amount_usd=price_usd,
                    currency_from="usd",
                    currency_to=curr
                )
                
                if estimate:
                    # Simplified fee estimation (actual would need network data)
                    fee_estimates = {
                        "usdt": 2,    # ERC-20 on Ethereum
                        "usdc": 2,    # ERC-20 on Ethereum  
                        "eth": 5,     # Native ETH gas
                        "matic": 0.1, # Polygon low fees
                        "sol": 0.01,  # Solana very low
                        "bnb": 0.5    # BSC medium fees
                    }
                    
                    speed_ratings = {
                        "usdt": "10-20 Min",
                        "usdc": "10-20 Min",
                        "eth": "5-15 Min",
                        "matic": "2-5 Min",
                        "sol": "1-2 Min",
                        "bnb": "3-5 Min"
                    }
                    
                    fee = fee_estimates.get(curr, 1)
                    total_cost_usd = price_usd + fee
                    
                    recommendations.append({
                        "currency": curr,
                        "amount": estimate.get("estimated_amount", 0),
                        "fee_usd": fee,
                        "total_usd": total_cost_usd,
                        "speed": speed_ratings.get(curr, "~10 Min"),
                        "score": (1 / total_cost_usd) * (1 / (speed_ratings.get(curr, "10").split("-")[0] or "10").replace(" Min", ""))
                    })
            except:
                continue
        
        if not recommendations:
            return "❌ Keine Empfehlungen verfügbar. Bitte später versuchen."
        
        # Sort by score (lower cost + faster = higher score)
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        top3 = recommendations[:3]
        
        result = f"💡 **Top Crypto-Empfehlungen für {plan.title()} (${price_usd}):**\n\n"
        
        medals = ["🥇", "🥈", "🥉"]
        for i, rec in enumerate(top3):
            currency_info = crypto_payment_service.get_currency_info(rec["currency"])
            result += f"{medals[i]} **{currency_info['name']}** ({currency_info['symbol'].upper()})\n"
            result += f"   • Amount: {rec['amount']:.6f} {rec['currency'].upper()}\n"
            result += f"   • Fee: ~${rec['fee_usd']:.2f}\n"
            result += f"   • Total: ${rec['total_usd']:.2f}\n"
            result += f"   • Speed: {rec['speed']}\n\n"
        
        result += f"💰 **Spare ${recommendations[-1]['total_usd'] - top3[0]['total_usd']:.2f}** mit {top3[0]['currency'].upper()} vs {recommendations[-1]['currency'].upper()}!\n\n"
        result += f"💡 Empfehlung: **{top3[0]['currency'].upper()}** (Best Cost/Speed-Ratio)"
        
        return result
    except Exception as e:
        logger.error(f"Error recommending currency: {e}")
        return "❌ Fehler bei der Empfehlung."


class GetPaymentEstimateInput(BaseModel):
    """Input for getting payment estimate"""
    plan: str = Field(..., description="Subscription plan (e.g., 'pro', 'business', 'plus')")
    currency: str = Field(..., description="Crypto currency code (e.g., 'btc', 'eth', 'usdt')")


@tool("get_payment_estimate", args_schema=GetPaymentEstimateInput, return_direct=False)
async def get_payment_estimate_tool(plan: str, currency: str) -> str:
    """
    Get payment estimate for a subscription plan in cryptocurrency.
    Use when user asks 'How much is Pro plan in Bitcoin?' or similar.
    Returns estimated crypto amount, exchange rate, and USD price.
    """
    try:
        price_usd = crypto_payment_service.PLAN_PRICES.get(plan.lower())
        if not price_usd:
            return f"❌ Plan '{plan}' nicht gefunden. Verfügbar: community, starter, pro, business, plus, enterprise"
        
        estimate = await crypto_payment_service.get_estimate(
            amount_usd=price_usd,
            currency_from="usd",
            currency_to=currency.lower()
        )
        
        if not estimate:
            return f"❌ Fehler beim Abrufen der Schätzung für {currency.upper()}"
        
        crypto_amount = estimate.get("estimated_amount", 0)
        currency_info = crypto_payment_service.get_currency_info(currency.lower())
        
        result = "💰 **Payment-Schätzung**\n\n"
        result += f"**Plan**: {plan.title()}\n**Preis**: ${price_usd} USD\n\n"
        result += f"**Du zahlst**: {currency_info['logo']} **{crypto_amount:.8f} {currency_info['symbol'].upper()}**\n\n"
        result += "💡 Finale Amount wird bei Erstellung berechnet (Live Exchange-Rate)."
        return result
    except Exception as e:
        logger.error(f"Error getting estimate: {e}")
        return "❌ Fehler beim Berechnen der Schätzung."


class CreateCryptoPaymentInput(BaseModel):
    """Input for creating crypto payment"""
    user_id: str = Field(..., description="User ID from context")
    plan: str = Field(..., description="Subscription plan (e.g., 'pro', 'business')")
    currency: str = Field(..., description="Crypto currency code (e.g., 'eth', 'btc')")


@tool("create_crypto_payment", args_schema=CreateCryptoPaymentInput, return_direct=False)
async def create_crypto_payment_tool(user_id: str, plan: str, currency: str) -> str:
    """
    Create a new cryptocurrency payment for a subscription plan.
    Use when user confirms they want to pay with crypto.
    Returns payment details including deposit address, amount, and payment_id.
    IMPORTANT: User must be authenticated. Check user_id first.
    """
    try:
        if not user_id:
            return "❌ Du musst eingeloggt sein. Bitte melde dich an."
        
        order_id = f"order_{uuid.uuid4().hex[:16]}"
        payment_data = await crypto_payment_service.create_payment(
            plan_name=plan.lower(),
            currency=currency.lower(),
            user_id=user_id,
            order_id=order_id
        )
        
        if not payment_data:
            return "❌ Fehler beim Erstellen der Zahlung."
        
        # Save to database
        try:
            query = """
                INSERT INTO crypto_payments (
                    payment_id, order_id, user_id, plan_name,
                    price_amount, price_currency, pay_amount, pay_currency,
                    pay_address, payin_extra_id, payment_status,
                    invoice_url, purchase_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """
            await postgres_client.execute(
                query,
                payment_data["payment_id"], order_id, user_id, plan.lower(),
                float(payment_data["price_amount"]), payment_data["price_currency"],
                float(payment_data["pay_amount"]), payment_data["pay_currency"],
                payment_data.get("pay_address"), payment_data.get("payin_extra_id"),
                payment_data["payment_status"],
                crypto_payment_service.get_payment_url(payment_data["payment_id"]),
                payment_data.get("purchase_id")
            )
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
        
        currency_info = crypto_payment_service.get_currency_info(currency.lower())
        
        result = "✅ **Payment erstellt!**\n\n"
        result += f"**Plan**: {plan.title()}\n**Order ID**: `{order_id}`\n\n"
        result += f"💰 **Zu zahlender Betrag**:\n{currency_info['logo']} **{payment_data['pay_amount']} {currency_info['symbol'].upper()}**\n"
        result += f"≈ ${payment_data['price_amount']} USD\n\n"
        result += f"📍 **Zahlungsadresse**:\n```\n{payment_data['pay_address']}\n```\n\n"
        
        if payment_data.get("payin_extra_id"):
            result += f"🔖 **Extra ID**: `{payment_data['payin_extra_id']}`\n\n"
        
        result += "⏰ **Gültigkeit**: 15 Minuten\n\n"
        result += f"⚠️ **WICHTIG**: Nur **{currency_info['symbol'].upper()}** an diese Adresse senden!\n\n"
        result += f"🔗 [Payment-Page]({crypto_payment_service.get_payment_url(payment_data['payment_id'])})\n\n"
        result += "💡 Zahlung wird automatisch erkannt und Plan aktiviert!\n\n"
        result += f"[PAYMENT_ID:{payment_data['payment_id']}]"
        
        return result
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        return f"❌ Fehler: {str(e)}"


class GetUserPlanInput(BaseModel):
    """Input for getting user's current plan"""
    user_id: str = Field(..., description="User ID from context")


@tool("get_user_plan", args_schema=GetUserPlanInput, return_direct=False)
async def get_user_plan_tool(user_id: str) -> str:
    """
    Get user's current subscription plan and suggest upgrades.
    Use when user asks 'What's my plan?' or 'Can I upgrade?'.
    Returns current plan, features, and upgrade suggestions.
    """
    try:
        if not user_id:
            return "❌ Du musst eingeloggt sein."
        
        user = await postgres_client.fetchrow(
            "SELECT plan, created_at FROM users WHERE id = $1",
            user_id
        )
        
        if not user:
            return "❌ User nicht gefunden."
        
        current_plan = user["plan"] or "community"
        
        # Plan info
        plan_info = {
            "community": {
                "name": "Community",
                "price": "$0",
                "features": ["Transaction Tracing", "Basic Cases", "Community Support"],
                "next": "starter",
                "upgrade_cost": "$49/mo",
                "upgrade_features": ["10 Cases/mo", "Priority Support", "Email Alerts"]
            },
            "starter": {
                "name": "Starter",
                "price": "$49/mo",
                "features": ["10 Cases/mo", "Priority Support", "Email Alerts"],
                "next": "pro",
                "upgrade_cost": "+$200/mo",
                "upgrade_features": ["Graph Explorer", "Correlation Analysis", "AI Agent"]
            },
            "pro": {
                "name": "Pro",
                "price": "$299/mo",
                "features": ["Graph Explorer", "Correlation", "AI Agent", "50 Cases/mo"],
                "next": "business",
                "upgrade_cost": "+$200/mo",
                "upgrade_features": ["Unlimited Cases", "API Access", "White-Label"]
            },
            "business": {
                "name": "Business",
                "price": "$599/mo",
                "features": ["Unlimited Cases", "API Access", "100 Requests/min"],
                "next": "plus",
                "upgrade_cost": "+$400/mo",
                "upgrade_features": ["Advanced ML", "Dark Web Monitoring", "Compliance Tools"]
            },
            "plus": {
                "name": "Plus",
                "price": "$999/mo",
                "features": ["Advanced ML", "Dark Web Monitoring", "Compliance"],
                "next": "enterprise",
                "upgrade_cost": "Custom",
                "upgrade_features": ["Dedicated Support", "Custom Integrations", "SLA"]
            },
            "enterprise": {
                "name": "Enterprise",
                "price": "Custom",
                "features": ["Everything", "Dedicated Support", "Custom Integrations", "SLA"],
                "next": None,
                "upgrade_cost": None,
                "upgrade_features": []
            }
        }
        
        info = plan_info.get(current_plan, plan_info["community"])
        
        result = "📊 **Dein aktueller Plan**\n\n"
        result += f"**{info['name']}** - {info['price']}\n\n"
        result += "**Features**:\n"
        for feature in info['features']:
            result += f"• {feature}\n"
        
        if info['next']:
            result += f"\n💡 **Upgrade-Empfehlung**: {plan_info[info['next']]['name']}\n"
            result += f"**Kosten**: {info['upgrade_cost']}\n"
            result += "**Zusätzliche Features**:\n"
            for feature in info['upgrade_features']:
                result += f"• {feature}\n"
            result += f"\nMöchtest du upgraden? Sage einfach 'Upgrade auf {plan_info[info['next']]['name']}'!"
        else:
            result += "\n🎉 Du hast bereits den höchsten Plan!"
        
        return result
    except Exception as e:
        logger.error(f"Error getting user plan: {e}")
        return "❌ Fehler beim Abrufen deines Plans."


@tool("analyze_cross_chain_bridge", args_schema=AnalyzeCrossChainBridgeInput)
async def analyze_cross_chain_bridge_tool(
    address: str,
    chain: str,
    max_depth: int = 3,
    include_incoming: bool = True,
    include_outgoing: bool = True,
    from_timestamp: Optional[str] = None,
    to_timestamp: Optional[str] = None,
    min_value_usd: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Analyze cross-chain bridge activities for a blockchain address.
    Useful for detecting money laundering, bridge exploits, and multi-chain fund movements.
    Returns bridge transfers, volumes, and risk indicators.
    """
    try:
        # Use Neo4j to query bridge transactions
        # This is a simplified implementation - in production would use specialized bridge indexer
        bridge_transfers = []

        # Query for outgoing bridge transfers
        if include_outgoing:
            outgoing_query = """
            MATCH (a:Address {address: $address, chain: $chain})-[r:BRIDGE_TRANSFER]->(t:BridgeTransaction)
            WHERE ($from_timestamp IS NULL OR r.timestamp >= datetime($from_timestamp))
            AND ($to_timestamp IS NULL OR r.timestamp <= datetime($to_timestamp))
            AND ($min_value_usd IS NULL OR r.value_usd >= $min_value_usd)
            RETURN r, t ORDER BY r.timestamp DESC LIMIT 50
            """
            outgoing_result = await neo4j_client.query(outgoing_query, {
                "address": address,
                "chain": chain,
                "from_timestamp": from_timestamp,
                "to_timestamp": to_timestamp,
                "min_value_usd": min_value_usd
            })

            for record in outgoing_result:
                bridge_transfers.append({
                    "type": "outgoing",
                    "timestamp": record["r"]["timestamp"].isoformat(),
                    "from_chain": chain,
                    "to_chain": record["r"]["to_chain"],
                    "value_usd": record["r"]["value_usd"],
                    "bridge_name": record["t"]["bridge_name"],
                    "tx_hash": record["r"]["tx_hash"],
                    "risk_score": record["r"].get("risk_score", 0.0)
                })

        # Query for incoming bridge transfers
        if include_incoming:
            incoming_query = """
            MATCH (a:Address {address: $address, chain: $chain})<-[r:BRIDGE_TRANSFER]-(t:BridgeTransaction)
            WHERE ($from_timestamp IS NULL OR r.timestamp >= datetime($from_timestamp))
            AND ($to_timestamp IS NULL OR r.timestamp <= datetime($to_timestamp))
            AND ($min_value_usd IS NULL OR r.value_usd >= $min_value_usd)
            RETURN r, t ORDER BY r.timestamp DESC LIMIT 50
            """
            incoming_result = await neo4j_client.query(incoming_query, {
                "address": address,
                "chain": chain,
                "from_timestamp": from_timestamp,
                "to_timestamp": to_timestamp,
                "min_value_usd": min_value_usd
            })

            for record in incoming_result:
                bridge_transfers.append({
                    "type": "incoming",
                    "timestamp": record["r"]["timestamp"].isoformat(),
                    "from_chain": record["r"]["from_chain"],
                    "to_chain": chain,
                    "value_usd": record["r"]["value_usd"],
                    "bridge_name": record["t"]["bridge_name"],
                    "tx_hash": record["r"]["tx_hash"],
                    "risk_score": record["r"].get("risk_score", 0.0)
                })

        # Sort by timestamp descending
        bridge_transfers.sort(key=lambda x: x["timestamp"], reverse=True)

        # Calculate summary statistics
        total_volume_usd = sum(t["value_usd"] for t in bridge_transfers)
        total_transfers = len(bridge_transfers)
        high_risk_count = sum(1 for t in bridge_transfers if t["risk_score"] > 0.7)
        chains_involved = set()
        bridges_used = set()

        for transfer in bridge_transfers:
            chains_involved.add(transfer["from_chain"])
            chains_involved.add(transfer["to_chain"])
            bridges_used.add(transfer["bridge_name"])

        # Risk assessment
        risk_factors = []
        if high_risk_count > 0:
            risk_factors.append(f"{high_risk_count} high-risk transfers detected")
        if len(bridges_used) > 3:
            risk_factors.append("Multiple bridge protocols used")
        if len(chains_involved) > 5:
            risk_factors.append("Activity across many chains")

        return {
            "address": address,
            "primary_chain": chain,
            "total_bridge_transfers": total_transfers,
            "total_volume_usd": total_volume_usd,
            "chains_involved": list(chains_involved),
            "bridges_used": list(bridges_used),
            "high_risk_count": high_risk_count,
            "risk_factors": risk_factors,
            "recent_transfers": bridge_transfers[:10],  # Return most recent 10
            "analysis_period": {
                "from_timestamp": from_timestamp,
                "to_timestamp": to_timestamp,
                "min_value_usd": min_value_usd
            }
        }

    except Exception as e:
        logger.error(f"Error in analyze_cross_chain_bridge_tool: {e}")
        return {"error": str(e)}


class RetryFailedPaymentInput(BaseModel):
    """Input for retrying failed payment"""
    payment_id: int = Field(..., description="Failed payment ID to retry")
    user_id: str = Field(..., description="User ID from context")


@tool("retry_failed_payment", args_schema=RetryFailedPaymentInput, return_direct=False)
async def retry_failed_payment_tool(payment_id: int, user_id: str) -> str:
    """
    Automatically retries a failed or expired payment.
    Use when user says 'Retry payment' or 'My payment failed, try again'.
    Creates a new payment with same parameters.
    """
    try:
        if not user_id:
            return "❌ Du musst eingeloggt sein."
        
        # Get original payment
        original = await postgres_client.fetchrow(
            "SELECT * FROM crypto_payments WHERE payment_id = $1 AND user_id = $2",
            payment_id,
            user_id
        )
        
        if not original:
            return f"❌ Payment {payment_id} nicht gefunden."
        
        if original["payment_status"] not in ["failed", "expired"]:
            return f"❌ Kann nur failed/expired payments retries. Status: {original['payment_status']}"
        
        # Create new payment with same params
        order_id = f"retry_{uuid.uuid4().hex[:16]}"
        new_payment = await crypto_payment_service.create_payment(
            plan_name=original["plan_name"],
            currency=original["pay_currency"],
            user_id=user_id,
            order_id=order_id
        )
        
        if not new_payment:
            return "❌ Fehler beim Erstellen des neuen Payments."
        
        # Save to database
        query = """
            INSERT INTO crypto_payments (
                payment_id, order_id, user_id, plan_name,
                price_amount, price_currency, pay_amount, pay_currency,
                pay_address, payin_extra_id, payment_status,
                invoice_url, purchase_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """
        await postgres_client.execute(
            query,
            new_payment["payment_id"], order_id, user_id, original["plan_name"],
            float(new_payment["price_amount"]), new_payment["price_currency"],
            float(new_payment["pay_amount"]), new_payment["pay_currency"],
            new_payment.get("pay_address"), new_payment.get("payin_extra_id"),
            new_payment["payment_status"],
            crypto_payment_service.get_payment_url(new_payment["payment_id"]),
            new_payment.get("purchase_id")
        )
        
        currency_info = crypto_payment_service.get_currency_info(original["pay_currency"])
        
        result = "🔄 **Payment neu erstellt!**\n\n"
        result += f"**Original**: Payment {payment_id} ({original['payment_status']})\n"
        result += f"**Neu**: Payment {new_payment['payment_id']}\n\n"
        result += f"💰 **Amount**: {new_payment['pay_amount']} {currency_info['symbol'].upper()}\n"
        result += f"📍 **Address**: `{new_payment['pay_address']}`\n\n"
        result += "⏰ **Gültigkeit**: 15 Minuten\n\n"
        result += f"[PAYMENT_ID:{new_payment['payment_id']}]"
        
        return result
    except Exception as e:
        logger.error(f"Error retrying payment: {e}")
        return f"❌ Fehler: {str(e)}"


class CheckPaymentStatusInput(BaseModel):
    """Input for checking payment status"""
    payment_id: int = Field(..., description="Payment ID to check")


@tool("check_payment_status", args_schema=CheckPaymentStatusInput, return_direct=False)
async def check_payment_status_tool(payment_id: int) -> str:
    """
    Check the status of a crypto payment.
    Use when user asks 'Is my payment confirmed?' or 'What's the status?'.
    Returns current payment status, transaction hash if confirmed.
    """
    try:
        payment = await postgres_client.fetchrow(
            "SELECT * FROM crypto_payments WHERE payment_id = $1",
            payment_id
        )
        
        if not payment:
            return f"❌ Payment {payment_id} nicht gefunden."
        
        status = payment["payment_status"]
        currency = payment["pay_currency"].upper()
        amount = payment["pay_amount"]
        
        status_messages = {
            "pending": "⏳ **Warte auf Zahlung**\n\nBitte sende Krypto an die Adresse.",
            "waiting": "⏳ **Warte auf Confirmations**\n\nTransaktion erkannt...",
            "confirming": "🔄 **Bestätigung läuft**\n\nWird bestätigt...",
            "confirmed": "✅ **Bestätigt!**\n\nWird verarbeitet...",
            "sending": "📤 **Wird verarbeitet**",
            "finished": "🎉 **Erfolgreich!**\n\nPlan aktiviert! Willkommen!",
            "failed": "❌ **Fehlgeschlagen**\n\nBitte Support kontaktieren.",
            "expired": "⏱️ **Abgelaufen**\n\nBitte neue Zahlung erstellen."
        }
        
        result = f"📊 **Payment-Status**\n\n**Order**: `{payment['order_id']}`\n"
        result += f"**Betrag**: {amount} {currency}\n\n"
        result += status_messages.get(status, f"Status: {status}")
        
        if payment.get("pay_in_hash"):
            result += f"\n\n**TX-Hash**: `{payment['pay_in_hash'][:16]}...`"
        
        return result
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return "❌ Fehler beim Abrufen des Status."


class SuggestWeb3PaymentInput(BaseModel):
    """Input for suggesting Web3 payment"""
    user_id: str = Field(..., description="User ID from context")
    plan: str = Field(..., description="Subscription plan")
    currency: str = Field(..., description="Crypto currency code")


@tool("suggest_web3_payment", args_schema=SuggestWeb3PaymentInput, return_direct=False)
async def suggest_web3_payment_tool(user_id: str, plan: str, currency: str) -> str:
    """
    Suggests Web3 one-click payment option to user.
    Use when user confirms payment and currency supports Web3 (ETH, TRX, BNB, MATIC).
    Returns suggestion with benefits of Web3 payment.
    """
    try:
        if not user_id:
            return "❌ Du musst eingeloggt sein."
        
        # Check if currency supports Web3
        web3_currencies = ["eth", "trx", "bnb", "matic"]
        if currency.lower() not in web3_currencies:
            return ""  # Silent skip for non-Web3 currencies
        
        wallet_names = {
            "eth": "MetaMask",
            "trx": "TronLink",
            "bnb": "MetaMask (BSC)",
            "matic": "MetaMask (Polygon)"
        }
        
        wallet_name = wallet_names.get(currency.lower(), "MetaMask")
        
        result = "\n\n💡 **TIPP: Web3 One-Click-Payment verfügbar!**\n\n"
        result += f"Statt manuell zu bezahlen, kannst du mit **{wallet_name}** direkt aus dem Chat bezahlen:\n\n"
        result += "✅ **Vorteile**:\n"
        result += "• 🚀 **One-Click**: Wallet öffnet sich automatisch\n"
        result += "• ⚡ **Schneller**: Keine Copy-Paste von Adressen\n"
        result += "• 🔒 **Sicherer**: Keine Tippfehler möglich\n"
        result += "• 💎 **Komfortabel**: Wie PayPal, aber mit Crypto\n\n"
        result += f"Wenn du eine Zahlung erstellst, erscheint automatisch ein **'Connect {wallet_name} & Pay'** Button im Widget!\n\n"
        result += "Möchtest du das Payment jetzt erstellen?"
        
        return result
    except Exception as e:
        logger.error(f"Error suggesting Web3 payment: {e}")
        return ""


class CreateBTCInvoiceInput(BaseModel):
    """Input for create_btc_invoice tool"""
    plan_name: str = Field(..., description="Subscription plan: community, pro, business, enterprise")
    amount_btc: float = Field(..., description="Amount in BTC to charge")
    user_id: str = Field(..., description="User ID from context")


class GetBTCInvoiceStatusInput(BaseModel):
    """Input for get_btc_invoice_status tool"""
    order_id: str = Field(..., description="BTC invoice order ID to check")


@tool("create_btc_invoice", args_schema=CreateBTCInvoiceInput, return_direct=False)
async def create_btc_invoice_tool(user_id: str, plan_name: str, amount_btc: float) -> str:
    """
    Create a new BTC invoice with unique address.
    Use when user wants to pay with BTC directly (no NOWPayments fees).
    Returns invoice details with QR code and payment instructions.
    IMPORTANT: User must be authenticated. Check user_id first.
    """
    try:
        if not user_id:
            return "❌ Du musst eingeloggt sein. Bitte melde dich an."

        # Import here to avoid circular imports
        from app.services.btc_invoice_service import btc_invoice_service

        invoice = btc_invoice_service.create_invoice(
            user_id=user_id,
            plan_name=plan_name.lower(),
            amount_btc=amount_btc,
            expires_hours=24
        )

        if not invoice:
            return "❌ Fehler beim Erstellen der BTC-Invoice."

        result = "✅ **BTC-Invoice erstellt!**\n\n"
        result += f"**Plan**: {plan_name.title()}\n"
        result += f"**Order ID**: `{invoice['order_id']}`\n\n"
        result += f"💰 **Zu zahlender Betrag**:\n₿ **{invoice['expected_amount_btc']} BTC**\n"
        result += f"≈ ${float(invoice['expected_amount_btc']) * 45000:.2f} USD\n\n"
        result += f"📍 **BTC-Adresse**:\n```\n{invoice['address']}\n```\n\n"
        result += f"⏰ **Gültigkeit**: 24 Stunden\n\n"
        result += "⚠️ **WICHTIG**: Nur **BTC** an diese Adresse senden!\n\n"
        result += "🔗 QR-Code: Wird im Checkout angezeigt\n\n"
        result += "💡 Zahlung wird automatisch erkannt und Plan aktiviert!\n\n"
        result += f"[ORDER_ID:{invoice['order_id']}]"

        return result
    except Exception as e:
        logger.error(f"Error creating BTC invoice: {e}")
        return f"❌ Fehler: {str(e)}"


@tool("get_btc_invoice_status", args_schema=GetBTCInvoiceStatusInput, return_direct=False)
async def get_btc_invoice_status_tool(order_id: str) -> str:
    """
    Check the status of a BTC invoice payment.
    Use when user asks about invoice status or payment confirmation.
    Returns current status, received amount, and transaction details if available.
    """
    try:
        # Import here to avoid circular imports
        from app.services.btc_invoice_service import btc_invoice_service

        status = btc_invoice_service.check_payment_status(order_id)

        if status.get("status") == "not_found":
            return f"❌ BTC-Invoice {order_id} nicht gefunden."

        status_emoji = {
            "pending": "⏳",
            "paid": "✅",
            "expired": "⏱️"
        }.get(status.get("status"), "❓")

        result = f"📊 **BTC-Invoice Status**\n\n"
        result += f"**Order ID**: `{order_id}`\n"
        result += f"**Status**: {status_emoji} {status.get('status', 'unknown').title()}\n\n"

        if status.get("plan_name"):
            result += f"**Plan**: {status.get('plan_name').title()}\n"

        result += f"**Erwartet**: ₿ {status.get('expected_amount_btc', '0')} BTC\n"

        if status.get("received_amount_btc"):
            received = float(status.get("received_amount_btc", 0))
            expected = float(status.get("expected_amount_btc", 1))
            percentage = min(100, (received / expected) * 100) if expected > 0 else 0

            result += f"**Erhalten**: ₿ {status.get('received_amount_btc')} BTC ({percentage:.1f}%)\n"

            # Progress bar
            filled = int(percentage / 10)
            bar = "█" * filled + "░" * (10 - filled)
            result += f"**Fortschritt**: [{bar}] {percentage:.1f}%\n"

        if status.get("txid"):
            result += f"**TX-Hash**: `{status.get('txid')[:16]}...`\n"

        if status.get("paid_at"):
            result += f"**Bezahlt am**: {status.get('paid_at')}\n"

        if status.get("expires_at"):
            result += f"**Läuft ab**: {status.get('expires_at')}\n"

        # Action hints
        if status.get("status") == "pending":
            result += "\n💡 **Tipp**: Öffne die Checkout-Seite um QR-Code und Live-Updates zu sehen!"
        elif status.get("status") == "paid":
            result += "\n🎉 **Erfolgreich!** Dein Plan wurde aktiviert!"
        elif status.get("status") == "expired":
            result += "\n⏱️ **Abgelaufen**. Erstelle eine neue Invoice!"

        return result
    except Exception as e:
        logger.error(f"Error checking BTC invoice status: {e}")
        return f"❌ Fehler beim Abrufen des Status: {str(e)}"


# ==========================================
# DEMO SYSTEM TOOLS (Marketing Chatbot)
# ==========================================

class OfferSandboxDemoInput(BaseModel):
    """Input for offer_sandbox_demo tool"""
    context: Optional[str] = Field(None, description="User's context or question that triggered demo offer")

@tool("offer_sandbox_demo", args_schema=OfferSandboxDemoInput)
async def offer_sandbox_demo_tool(context: Optional[str] = None) -> str:
    """
    Offer Sandbox Demo (Tier 1 - Instant Access)
    
    Use this when user wants to:
    - See how the platform looks
    - Understand features quickly
    - Get instant preview without signup
    
    This offers INSTANT ACCESS with mock data (no registration needed).
    
    Returns a message with demo information and link.
    """
    try:
        # Get sandbox demo data
        data = await demo_service.get_sandbox_demo_data()
        
        return f"""🎯 **Sandbox Demo verfügbar!**

✨ **Sofort testen - ohne Registrierung!**

📊 Was du sehen wirst:
• {len(data['mock_data']['recent_cases'])} Beispiel-Cases mit echten Analysen
• {len(data['mock_data']['sample_addresses'])} Sample-Adressen (Bitcoin, Ethereum)
• Live-Analytics-Dashboard
• Alle Features zum Anschauen

🔹 **Features:**
{chr(10).join(f"  • {f.replace('_', ' ').title()}" for f in data['features'][:5])}

⚡ **DEMO_LINK**: [SANDBOX_DEMO_START]

💡 **Tipp**: Nach der Sandbox kannst du eine **30-Min Live-Demo** mit echten Daten starten!

Möchtest du die Sandbox jetzt öffnen? 🚀"""
    except Exception as e:
        logger.error(f"Error offering sandbox demo: {e}")
        return "❌ Fehler beim Laden der Demo."


class OfferLiveDemoInput(BaseModel):
    """Input for offer_live_demo tool"""
    user_interest: Optional[str] = Field(None, description="What the user is interested in testing")

@tool("contact_support", args_schema=ContactSupportInput)
async def contact_support_tool(
    name: str,
    email: str,
    subject: str,
    message: str,
    urgency: Optional[str] = None
) -> str:
    """
    Contact Support Team - Submit a support ticket
    
    Use this when user:
    - Requests help with a technical issue
    - Wants to report a bug
    - Has a billing question
    - Needs assistance from support team
    - Says "contact support" or "send email to support"
    
    This creates a support ticket and sends email to the team.
    User will receive a confirmation with ticket number.
    
    Args:
        name: User's full name
        email: User's email address
        subject: Brief description of the issue
        message: Detailed description
        urgency: Optional urgency level
    
    Returns:
        Confirmation message with ticket ID and response time
    """
    try:
        # Submit ticket via support service
        result = await support_service.submit_contact_form(
            name=name,
            email=email,
            subject=subject,
            message=message,
            language="de",  # Can be extracted from context
            metadata={"source": "chatbot", "urgency": urgency}
        )
        
        if result.get("success"):
            ticket_id = result.get("ticket_id")
            priority = result.get("priority")
            estimated_time = result.get("estimated_response_time")
            ai_reply = result.get("ai_reply")
            
            response = f"""✅ **Support-Ticket erstellt!**

📋 **Ticket-ID**: #{ticket_id}
⚡ **Priorität**: {priority.upper()}
⏱️ **Geschätzte Antwortzeit**: {estimated_time}

📧 Eine Bestätigungs-E-Mail wurde an **{email}** gesendet.

"""
            
            if ai_reply:
                response += f"""🤖 **Automatische Vorab-Antwort**:
{ai_reply}

"""
            
            response += """💼 Unser Support-Team wird sich so schnell wie möglich bei Ihnen melden.

📌 **Tipp**: Sie können den Ticket-Status jederzeit in Ihrem Dashboard einsehen."""
            
            return response
        else:
            return f"❌ Fehler beim Erstellen des Tickets: {result.get('error', 'Unbekannter Fehler')}"
        
    except Exception as e:
        logger.error(f"Error in contact_support_tool: {e}")
        return f"❌ Fehler beim Kontakt mit dem Support: {str(e)}"


@tool("offer_live_demo", args_schema=OfferLiveDemoInput)
async def offer_live_demo_tool(user_interest: Optional[str] = None) -> str:
    """
    Offer Live Demo (Tier 2 - 30 Minutes Test Drive)
    
    Use this when user:
    - Wants to try real features
    - Has seen the sandbox and wants more
    - Asks about "trying it" or "test account"
    - Needs to test with real data
    
    This creates a TEMPORARY 30-minute account with Pro access.
    NO signup required, auto-expires.
    
    Returns message with offer and benefits.
    """
    
    try:
        interest = user_interest or "alle Features"
        
        return f"""🚀 **30-Minuten Live-Demo**

🎁 **Kostenlos testen - ohne Registrierung!**

Was du bekommst:
• ✅ **Voller Pro-Plan Zugang** (30 Minuten)
• ✅ Echte Blockchain-Traces durchführen
• ✅ Eigene Adressen analysieren
• ✅ Cases erstellen und verwalten
• ✅ AI-Agent nutzen
• ✅ Graph-Explorer testen

⏱️ **30 Minuten** voller Zugriff auf {interest}

🔐 **Keine Kreditkarte nötig** - Account wird automatisch gelöscht

💡 **Perfect für:**
• Evaluierung der Platform
• Feature-Testing mit deinen Daten
• Proof-of-Concept für dein Team
• Sofortige Hands-on Experience

🎯 **DEMO_LINK**: [LIVE_DEMO_START]

⚡ Möchtest du jetzt starten? Klick einfach und du bist in 5 Sekunden drin!

📌 **Hinweis**: Nach Ablauf kannst du kostenlos einen Account erstellen und deine Arbeit speichern."""
    except Exception as e:
        logger.error(f"Error offering live demo: {e}")
        return "❌ Fehler beim Laden der Demo-Info."


# Import Wallet Management Tools
from app.ai_agents.tools.wallet_management_tools import WALLET_MANAGEMENT_TOOLS
from app.ai_agents.tools.smart_contract_tools import SMART_CONTRACT_TOOLS
from app.ai_agents.tools.defi_trading_tools import DEFI_TRADING_TOOLS
from app.ai_agents.tools.nft_management_tools import NFT_MANAGEMENT_TOOLS

# Import Firewall Tools
try:
    from app.ai_agents.firewall_tools import (
        scan_transaction_firewall,
        scan_token_approval,
        scan_url_phishing,
        get_firewall_stats,
        add_to_firewall_whitelist,
        add_to_firewall_blacklist
    )
    FIREWALL_TOOLS_AVAILABLE = True
except ImportError:
    FIREWALL_TOOLS_AVAILABLE = False
    logger.warning("Firewall tools not available")

# List of all forensic tools
FORENSIC_TOOLS = [
    trace_address_tool,
    advanced_trace_tool,
    query_graph_tool,
    get_labels_tool,
    find_path_tool,
    list_alert_rules_tool,
    simulate_alerts_tool,
    risk_score_tool,
    bridge_lookup_tool,
    analyze_cross_chain_bridge_tool,
    trigger_alert_tool,
    write_evidence_tool,
    run_playbooks_tool,
    cluster_analysis_tool,
    cross_chain_analysis_tool,
    threat_intel_enrich_tool,
    submit_community_report_tool,
    # Intelligence Network Tools
    intelligence_check_tool,
    intelligence_flag_tool,
    intelligence_confirm_flag_tool,
    intelligence_list_flags_tool,
    intelligence_stats_tool,
    intelligence_register_investigator_tool,
    intelligence_register_member_tool,
    code_extract_tool,
    text_extract_tool,
    # Crypto Payment Tools
    get_available_cryptocurrencies_tool,
    recommend_best_currency_tool,
    get_payment_estimate_tool,
    suggest_web3_payment_tool,
    create_crypto_payment_tool,
    create_btc_invoice_tool,  # NEW: Direct BTC invoice creation
    get_btc_invoice_status_tool,  # NEW: BTC invoice status checking
    get_user_plan_tool,
    retry_failed_payment_tool,
    check_payment_status_tool,
    get_payment_history_tool,
    # Demo System Tools (Marketing Chatbot)
    offer_sandbox_demo_tool,
    offer_live_demo_tool,
    contact_support_tool,  # NEW: Support-Tickets via Chat
    # WALLET MANAGEMENT TOOLS (Phase 1) - 8 Tools
    *WALLET_MANAGEMENT_TOOLS,
    # SMART CONTRACT TOOLS (Phase 2) - 5 Tools
    *SMART_CONTRACT_TOOLS,
    # DeFi & TRADING TOOLS (Phase 3) - 4 Tools
    *DEFI_TRADING_TOOLS,
    # NFT MANAGEMENT TOOLS (Phase 4) - 3 Tools
    *NFT_MANAGEMENT_TOOLS,
]

# Legacy alias exports for tests expecting short names
try:
    trace_address = trace_address_tool  # noqa: F401
except Exception:
    pass
try:
    risk_score = risk_score_tool  # noqa: F401
except Exception:
    pass
try:
    # create_case may live in case_management_tools; alias if present
    from app.ai_agents.tools.case_management_tools import create_case_tool as _create_case_tool  # type: ignore
    create_case = _create_case_tool  # noqa: F401
except Exception:
    try:
        from app.ai_agents.tools.case_management import create_case_tool as _create_case_tool2  # type: ignore
        create_case = _create_case_tool2  # noqa: F401
    except Exception:
        pass
try:
    get_available_cryptocurrencies = get_available_cryptocurrencies_tool  # noqa: F401
except Exception:
    pass
try:
    create_crypto_payment = create_crypto_payment_tool  # noqa: F401
except Exception:
    pass

# Add Firewall Tools if available
if FIREWALL_TOOLS_AVAILABLE:
    # Convert async functions to LangChain tools
    from langchain.tools import StructuredTool
    
    FIREWALL_TOOLS = [
        StructuredTool.from_function(
            func=scan_transaction_firewall,
            name="scan_transaction_firewall",
            description="Scan transaction with AI Firewall before sending. Detects token approvals, scams, phishing. Use when user asks if TX is safe.",
            coroutine=scan_transaction_firewall
        ),
        StructuredTool.from_function(
            func=scan_token_approval,
            name="scan_token_approval",
            description="Analyze token approval for unlimited approvals, unknown spenders. Use when user wants to approve token spending.",
            coroutine=scan_token_approval
        ),
        StructuredTool.from_function(
            func=scan_url_phishing,
            name="scan_url_phishing",
            description="Scan URL for phishing (typosquatting, malicious domains). Use when user asks if website is safe.",
            coroutine=scan_url_phishing
        ),
        StructuredTool.from_function(
            func=get_firewall_stats,
            name="get_firewall_stats",
            description="Get firewall statistics (blocked threats, scanned transactions). Use when user asks about firewall status.",
            coroutine=get_firewall_stats
        ),
        StructuredTool.from_function(
            func=add_to_firewall_whitelist,
            name="add_to_firewall_whitelist",
            description="Add address to whitelist (always allow). Use when user explicitly trusts an address.",
            coroutine=add_to_firewall_whitelist
        ),
        StructuredTool.from_function(
            func=add_to_firewall_blacklist,
            name="add_to_firewall_blacklist",
            description="Add address to blacklist (always block). Use when user wants to permanently block an address.",
            coroutine=add_to_firewall_blacklist
        ),
    ]
    
    # Add to FORENSIC_TOOLS
    FORENSIC_TOOLS.extend(FIREWALL_TOOLS)
    logger.info("🛡️ Firewall Tools registered: 6 tools added")

# Import Institutional Verification Tools
try:
    from app.ai_agents.tools.institutional_verification_tools import (
        INSTITUTIONAL_VERIFICATION_TOOLS
    )
    FORENSIC_TOOLS.extend(INSTITUTIONAL_VERIFICATION_TOOLS)
    logger.info("🏛️ Institutional Verification Tools registered: 3 tools added")
except ImportError as e:
    logger.warning(f"Institutional verification tools not available: {e}")

# Import Case Management Tools
try:
    from app.ai_agents.tools.case_management_tools import CASE_MANAGEMENT_TOOLS
    FORENSIC_TOOLS.extend(CASE_MANAGEMENT_TOOLS)
    logger.info(f"📁 Case Management Tools registered: {len(CASE_MANAGEMENT_TOOLS)} tools added")
except ImportError as e:
    logger.warning(f"Case management tools not available: {e}")

# Import Report Generation Tools
try:
    from app.ai_agents.tools.report_generation_tools import REPORT_GENERATION_TOOLS
    FORENSIC_TOOLS.extend(REPORT_GENERATION_TOOLS)
    logger.info(f"📄 Report Generation Tools registered: {len(REPORT_GENERATION_TOOLS)} tools added")
except ImportError as e:
    logger.warning(f"Report generation tools not available: {e}")

# backfill dynamic count for agent_health_tool output
try:
    # mutate default response for tools_registered
    if hasattr(agent_health_tool, "func"):
        pass  # LangChain wraps the function; keep simple for compatibility
    else:
        pass
    # no-op: the actual count can be computed by callers if needed
    # to avoid tight coupling or side-effects here
except Exception:
    pass
