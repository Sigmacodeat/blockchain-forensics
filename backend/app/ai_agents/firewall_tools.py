"""
🛡️ AI FIREWALL TOOLS für AI-Agents
=====================================

AI-Agent kann jetzt Firewall-Features nutzen:
- Transaction Scanning
- Token Approval Analysis
- Phishing URL Detection
- Whitelist/Blacklist Management
- Firewall Stats

**Integration:** Diese Tools werden in ai_agents/tools.py registriert
"""

import logging
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)


async def scan_transaction_firewall(
    chain: str,
    to_address: str,
    value_usd: float,
    data: str = "",
    user_id: str = "",
    wallet_address: str = ""
) -> str:
    """
    🔍 Scanne Transaction mit AI Firewall BEVOR sie gesendet wird.
    
    **Wann nutzen:**
    - User fragt "Ist diese Transaktion sicher?"
    - User möchte Token approval genehmigen
    - User möchte mit DApp interagieren
    
    Args:
        chain: Blockchain (ethereum, bitcoin, polygon, etc.)
        to_address: Zieladresse oder Contract
        value_usd: Wert in USD
        data: Transaction data (hex) für Contract-Calls
        user_id: User ID
        wallet_address: User's Wallet
    
    Returns:
        Detaillierter Scan-Report mit Risiko-Assessment
    """
    try:
        from app.services.ai_firewall_core import ai_firewall, Transaction
        from datetime import datetime
        
        # Create transaction object
        tx = Transaction(
            tx_hash=f"ai_scan_{datetime.now().timestamp()}",
            chain=chain,
            from_address=wallet_address or "0x0000000000000000000000000000000000000000",
            to_address=to_address,
            value=value_usd / 2000,  # Approximate ETH value
            value_usd=value_usd,
            timestamp=datetime.now(),
            data=data if data else None,
            contract_address=to_address if data else None
        )
        
        # Scan with firewall
        allowed, detection = await ai_firewall.intercept_transaction(
            user_id=user_id or "ai_agent",
            tx=tx,
            wallet_address=wallet_address or "unknown"
        )
        
        # Format response for AI
        if not allowed:
            return f"""🚨 **TRANSACTION BLOCKED!**

**Risk Level:** {detection.threat_level.value.upper()} ⚠️
**Confidence:** {detection.confidence * 100:.0f}%

**Block Reason:**
{detection.block_reason}

**Detected Threats ({len(detection.threat_types)}):**
{', '.join(detection.threat_types)}

**Evidence:**
{json.dumps(detection.evidence[:3], indent=2)}

**AI Models Used:** {', '.join(detection.ai_models_used)}
**Detection Time:** {detection.detection_time_ms:.1f}ms

⚠️ **RECOMMENDATION:** DO NOT proceed with this transaction!
"""
        elif detection.threat_level.value in ['high', 'medium']:
            return f"""⚠️ **WARNING: Medium-Risk Transaction**

**Risk Level:** {detection.threat_level.value.upper()}
**Confidence:** {detection.confidence * 100:.0f}%

**Detected Concerns ({len(detection.threat_types)}):**
{', '.join(detection.threat_types) if detection.threat_types else 'Minor concerns'}

**Evidence:**
{json.dumps(detection.evidence[:2], indent=2) if detection.evidence else 'No major issues'}

**Recommended Action:** {detection.recommended_action.value}

💡 **SUGGESTION:** Proceed with caution. Verify the recipient address carefully.
"""
        else:
            return f"""✅ **Transaction appears SAFE**

**Risk Level:** {detection.threat_level.value.upper()}
**Confidence:** {detection.confidence * 100:.0f}%

**Analysis:**
- No critical threats detected
- Passed {len(detection.ai_models_used)} security checks
- Detection time: {detection.detection_time_ms:.1f}ms

💡 **RECOMMENDATION:** Transaction can proceed safely.
"""
        
    except Exception as e:
        logger.error(f"Firewall scan error: {e}", exc_info=True)
        return f"❌ Error scanning transaction: {str(e)}"


async def scan_token_approval(
    token_address: str,
    spender_address: str,
    amount: str,
    chain: str = "ethereum"
) -> str:
    """
    🔐 Analysiere Token Approval für gefährliche Patterns.
    
    **Wann nutzen:**
    - User will Token approval genehmigen
    - User fragt "Ist dieser Approval sicher?"
    - DApp fordert unlimited approval
    
    Args:
        token_address: ERC20/ERC721 Token Contract
        spender_address: Contract der Tokens ausgeben darf
        amount: Approval Amount oder "unlimited"
        chain: Blockchain
    
    Returns:
        Detaillierte Approval-Analyse mit Risiko-Assessment
    """
    try:
        from app.services.token_approval_scanner import token_approval_scanner
        
        # Create mock transaction data for approval
        # approve(address spender, uint256 amount)
        # Function signature: 0x095ea7b3
        
        # Convert amount to hex
        if amount.lower() == "unlimited":
            amount_hex = "f" * 64  # Max uint256
        else:
            try:
                amount_int = int(float(amount) * (10**18))  # Assume 18 decimals
                amount_hex = hex(amount_int)[2:].zfill(64)
            except:
                amount_hex = "0" * 64
        
        # Encode spender address (remove 0x, pad to 64 chars)
        spender_hex = spender_address[2:].lower().zfill(64) if spender_address.startswith("0x") else spender_address.zfill(64)
        
        # Build transaction data
        tx_data = "0x095ea7b3" + spender_hex + amount_hex
        
        # Scan
        approval = await token_approval_scanner.scan_transaction(
            tx_data=tx_data,
            to_address=token_address,
            chain=chain
        )
        
        if not approval:
            return "✅ No dangerous approval patterns detected."
        
        # Format response
        risk_emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "⚠️",
            "low": "ℹ️",
            "safe": "✅"
        }.get(approval.risk_level.value, "⚠️")
        
        response = f"""{risk_emoji} **TOKEN APPROVAL ANALYSIS**

**Token:** {approval.token_symbol} ({approval.token_name})
**Spender:** {approval.spender_label or approval.spender_address}
**Amount:** {approval.amount_human}
**Risk Level:** {approval.risk_level.value.upper()}

**Detected Issues ({len(approval.reasons)}):**
"""
        for reason in approval.reasons:
            response += f"\n• {reason}"
        
        if approval.is_unlimited:
            response += f"""

🚨 **UNLIMITED APPROVAL DETECTED!**

This gives the spender UNLIMITED access to ALL your {approval.token_symbol} tokens!

**Safer Alternative:**
Approve only the amount you need (e.g., {1000} {approval.token_symbol})
"""
        
        # Add revoke instructions
        if approval.risk_level.value in ['critical', 'high']:
            revoke_info = token_approval_scanner.get_revoke_instructions(approval)
            response += f"""

🔧 **How to Revoke (if needed):**
{revoke_info['human']}

**Tools:**
{', '.join(revoke_info['tools'])}
"""
        
        return response
        
    except Exception as e:
        logger.error(f"Token approval scan error: {e}", exc_info=True)
        return f"❌ Error scanning approval: {str(e)}"


async def scan_url_phishing(url: str) -> str:
    """
    🎣 Scanne URL auf Phishing-Versuche.
    
    **Wann nutzen:**
    - User fragt "Ist diese Website sicher?"
    - User möchte Wallet mit DApp verbinden
    - User hat Link erhalten (Discord, Twitter, Email)
    
    Args:
        url: URL zu scannen
    
    Returns:
        Phishing-Analyse mit Empfehlungen
    """
    try:
        from app.services.phishing_scanner import phishing_scanner
        
        result = await phishing_scanner.scan_url(url)
        
        risk_emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "⚠️",
            "low": "ℹ️",
            "safe": "✅"
        }.get(result.risk_level.value, "⚠️")
        
        response = f"""{risk_emoji} **URL PHISHING SCAN**

**URL:** {result.url}
**Domain:** {result.domain}
**Risk Level:** {result.risk_level.value.upper()}
**Confidence:** {result.confidence * 100:.0f}%
**Is Phishing:** {'YES ⚠️' if result.is_phishing else 'NO ✅'}

**Analysis ({len(result.reasons)}):**
"""
        for reason in result.reasons:
            response += f"\n• {reason}"
        
        if result.similar_to:
            response += f"""

⚠️ **TYPOSQUATTING DETECTED!**
This domain looks similar to: **{result.similar_to}**

Legitimate URL: https://{result.similar_to}
"""
        
        response += "\n\n**Recommendations:**\n"
        for rec in result.recommendations:
            response += f"\n{rec}"
        
        response += f"\n\n*Scan time: {result.detection_time_ms:.1f}ms*"
        
        return response
        
    except Exception as e:
        logger.error(f"Phishing scan error: {e}", exc_info=True)
        return f"❌ Error scanning URL: {str(e)}"


async def get_firewall_stats(user_id: str = "") -> str:
    """
    📊 Zeige Firewall-Statistiken.
    
    **Wann nutzen:**
    - User fragt "Wie viele Threats wurden blockiert?"
    - User möchte Firewall-Status sehen
    
    Returns:
        Firewall-Statistiken
    """
    try:
        from app.services.ai_firewall_core import ai_firewall
        
        stats = ai_firewall.get_stats()
        
        return f"""📊 **FIREWALL STATISTICS**

**Protection Status:** {'🟢 ACTIVE' if stats['enabled'] else '🔴 INACTIVE'}
**Protection Level:** {stats['protection_level'].upper()}

**Scanned Transactions:** {stats['total_scanned']:,}
**Blocked:** {stats['blocked']:,} ({stats['block_rate']*100:.1f}%)
**Warned:** {stats['warned']:,}
**Allowed:** {stats['allowed']:,}

**Average Detection Time:** {stats['avg_detection_time_ms']:.1f}ms

**Threat Types:**
"""
        
        for threat_type, count in sorted(stats['threat_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
            response += f"• {threat_type}: {count}\n"
        
        response += f"""
**Lists:**
• Whitelisted: {stats['whitelist_size']} addresses
• Blacklisted: {stats['blacklist_size']} addresses
• Custom Rules: {stats['custom_rules']} rules

💡 Your wallet is protected by {7} AI defense layers!
"""
        
        return response
        
    except Exception as e:
        logger.error(f"Firewall stats error: {e}", exc_info=True)
        return f"❌ Error fetching stats: {str(e)}"


async def add_to_firewall_whitelist(
    address: str,
    reason: str = "User trusted"
) -> str:
    """
    ✅ Füge Adresse zur Firewall-Whitelist hinzu.
    
    **Wann nutzen:**
    - User sagt "Diese Adresse ist sicher, füge sie zur Whitelist hinzu"
    - User möchte Adresse immer erlauben
    
    Args:
        address: Blockchain-Adresse
        reason: Grund für Whitelisting
    
    Returns:
        Bestätigung
    """
    try:
        from app.services.ai_firewall_core import ai_firewall
        
        ai_firewall.add_to_whitelist(address)
        
        return f"""✅ **Address Whitelisted**

**Address:** {address}
**Reason:** {reason}

This address will now ALWAYS be allowed by the firewall.

💡 To remove: Use "remove from whitelist" command
"""
        
    except Exception as e:
        logger.error(f"Whitelist error: {e}", exc_info=True)
        return f"❌ Error adding to whitelist: {str(e)}"


async def add_to_firewall_blacklist(
    address: str,
    reason: str = "User blocked"
) -> str:
    """
    🚫 Füge Adresse zur Firewall-Blacklist hinzu.
    
    **Wann nutzen:**
    - User sagt "Blockiere diese Adresse permanent"
    - User hat schlechte Erfahrung mit Adresse
    
    Args:
        address: Blockchain-Adresse
        reason: Grund für Blacklisting
    
    Returns:
        Bestätigung
    """
    try:
        from app.services.ai_firewall_core import ai_firewall
        
        ai_firewall.add_to_blacklist(address)
        
        return f"""🚫 **Address Blacklisted**

**Address:** {address}
**Reason:** {reason}

This address will now ALWAYS be blocked by the firewall.

⚠️ No transactions to this address will be allowed!
"""
        
    except Exception as e:
        logger.error(f"Blacklist error: {e}", exc_info=True)
        return f"❌ Error adding to blacklist: {str(e)}"


# Tool definitions for AI Agent
FIREWALL_TOOLS = [
    {
        "name": "scan_transaction_firewall",
        "description": "Scan a transaction with AI Firewall before sending. Use when user asks if transaction is safe or wants to verify before signing.",
        "function": scan_transaction_firewall
    },
    {
        "name": "scan_token_approval",
        "description": "Analyze token approval for dangerous patterns (unlimited approvals, unknown spenders). Use when user wants to approve token spending.",
        "function": scan_token_approval
    },
    {
        "name": "scan_url_phishing",
        "description": "Scan URL for phishing attempts. Use when user asks if website is safe or before connecting wallet to DApp.",
        "function": scan_url_phishing
    },
    {
        "name": "get_firewall_stats",
        "description": "Get firewall statistics (blocked threats, scanned transactions, etc.). Use when user asks about firewall status.",
        "function": get_firewall_stats
    },
    {
        "name": "add_to_firewall_whitelist",
        "description": "Add address to firewall whitelist (always allow). Use when user explicitly trusts an address.",
        "function": add_to_firewall_whitelist
    },
    {
        "name": "add_to_firewall_blacklist",
        "description": "Add address to firewall blacklist (always block). Use when user wants to permanently block an address.",
        "function": add_to_firewall_blacklist
    }
]
