"""
AI-Agent Tools für Wallet-Management
====================================

Vollständige Wallet-Steuerung über Chat für alle 50+ Chains.
"""

import logging
from typing import Optional, List, Dict, Any
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field

from app.services.wallet_service import wallet_service
from app.services.wallet_ai_service import wallet_ai_agent
from app.services.multisig_wallet_service import multisig_manager
from app.services.hardware_wallet_service import hardware_wallet_manager, HardwareWalletType

logger = logging.getLogger(__name__)


# ==========================================
# INPUT SCHEMAS
# ==========================================

class CreateWalletInput(BaseModel):
    """Input for create_wallet tool"""
    chain: str = Field(..., description="Blockchain (ethereum, bitcoin, solana, polygon, bsc, avalanche, arbitrum, optimism, base, etc.)")
    wallet_name: Optional[str] = Field(None, description="Optional wallet name")


class ImportWalletInput(BaseModel):
    """Input for import_wallet tool"""
    chain: str = Field(..., description="Blockchain network")
    mnemonic: str = Field(..., description="12 or 24-word BIP39 mnemonic phrase")


class GetBalanceInput(BaseModel):
    """Input for get_wallet_balance tool"""
    chain: str = Field(..., description="Chain name")
    address: str = Field(..., description="Wallet address to check")


class SendTxInput(BaseModel):
    """Input for send_transaction tool"""
    from_wallet_id: str = Field(..., description="Source wallet ID")
    to_address: str = Field(..., description="Destination address")
    amount: str = Field(..., description="Amount to send")
    chain: str = Field(..., description="Blockchain network")
    private_key: str = Field(..., description="Private key for signing")


class ListWalletsInput(BaseModel):
    """Input for list_wallets tool"""
    chain_filter: Optional[str] = Field(None, description="Optional chain filter")


class GetHistoryInput(BaseModel):
    """Input for get_wallet_history tool"""
    wallet_id: str = Field(..., description="Wallet ID")
    limit: int = Field(default=50, description="Number of transactions")


class AnalyzeWalletInput(BaseModel):
    """Input for analyze_wallet tool"""
    wallet_id: str = Field(..., description="Wallet ID to analyze")


class EstimateGasInput(BaseModel):
    """Input for estimate_gas tool"""
    chain: str = Field(..., description="Blockchain network")
    from_address: str = Field(..., description="Source address")
    to_address: str = Field(..., description="Destination address")
    value: str = Field(default="0", description="Value to send")


# ==========================================
# WALLET TOOLS
# ==========================================

@tool("create_wallet", args_schema=CreateWalletInput)
async def create_wallet_tool(chain: str, wallet_name: Optional[str] = None) -> str:
    """
    Create new HD Wallet for any chain.
    
    Supports 50+ chains: Ethereum, Bitcoin, Solana, Polygon, BSC, Avalanche, 
    Arbitrum, Optimism, Base, Fantom, Harmony, Cronos, Moonbeam, und mehr.
    
    Example: "Create an Ethereum wallet"
    """
    try:
        wallet_data = await wallet_service.create_wallet(chain=chain)
        
        return f"""✅ **Wallet erfolgreich erstellt!**

📋 **Wallet ID**: {wallet_data['id']}
🔗 **Chain**: {chain.upper()}
📫 **Address**: {wallet_data['address']}
🔑 **Public Key**: {wallet_data['public_key'][:20]}...

💰 **Balance**: {wallet_data.get('balance', {}).get('balance', '0')}

⚠️ **WICHTIG**: 
• Sichere die Wallet-Daten!
• Mnemonic wurde generiert (24 Wörter)
• Verwende 'export_wallet' um Backup zu erstellen"""
        
    except Exception as e:
        logger.error(f"Error creating wallet: {e}")
        return f"❌ Fehler beim Erstellen der Wallet: {str(e)}"


@tool("import_wallet", args_schema=ImportWalletInput)
async def import_wallet_tool(
    import_type: str,
    chain: str,
    mnemonic: Optional[str] = None,
    private_key: Optional[str] = None,
    hardware_type: Optional[str] = None
) -> str:
    """
    Import wallet via mnemonic, private key, or hardware wallet.
    
    Supports:
    - Mnemonic (BIP39)
    - Private Key (Hex)
    - Hardware Wallets (Ledger, Trezor)
    
    Example: "Import wallet with mnemonic 'abandon abandon ...'"
    """
    try:
        if import_type == "mnemonic" and mnemonic:
            wallet_data = await wallet_service.create_wallet(chain=chain, mnemonic=mnemonic)
        elif import_type == "private_key" and private_key:
            wallet_data = await wallet_service.import_wallet_from_private_key(chain=chain, private_key_hex=private_key)
        elif import_type == "hardware" and hardware_type:
            wallet_data = await wallet_service.import_wallet_from_hardware_wallet(chain=chain, hardware_type=hardware_type)
        
        return f"""✅ **Wallet via {import_type} importiert!**

📋 **Wallet ID**: {wallet_data['id']}
🔗 **Chain**: {chain.upper()}
📫 **Address**: {wallet_data['address']}

💰 **Balance**: {wallet_data.get('balance', {}).get('balance', '0')}

✅ Wallet ist einsatzbereit!"""
        
    except Exception as e:
        logger.error(f"Error importing wallet: {e}")
        return f"❌ Fehler beim Importieren: {str(e)}"


@tool("get_wallet_balance", args_schema=GetBalanceInput)
async def get_wallet_balance_tool(chain: str, address: str) -> str:
    """
    Get wallet balance for native currency.
    
    Returns balance + AI risk analysis.
    
    Example: "Check balance of 0x742d35..."
    """
    try:
        balance_data = await wallet_service.get_balance(chain, address)
        
        balance = balance_data.get("balance", "0")
        risk_score = balance_data.get("risk_score", 0)
        risk_emoji = "🟢" if risk_score < 0.3 else "🟡" if risk_score < 0.7 else "🔴"
        
        result = f"""💰 **Wallet Balance**

🔗 **Chain**: {chain.upper()}
📫 **Address**: {address}
💎 **Balance**: {balance}

{risk_emoji} **Risk Score**: {risk_score:.2f}"""
        
        if balance_data.get("risk_factors"):
            result += f"\n\n⚠️ **Risk Factors**:\n"
            for factor in balance_data["risk_factors"][:3]:
                result += f"  • {factor}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        return f"❌ Fehler beim Abrufen der Balance: {str(e)}"


@tool("send_transaction", args_schema=SendTxInput)
async def send_transaction_tool(
    from_wallet_id: str,
    to_address: str,
    amount: str,
    chain: str,
    private_key: str
) -> str:
    """
    Send transaction from wallet to address.
    
    ⚠️ WARNING: This broadcasts a real transaction!
    
    Example: "Send 0.1 ETH to 0x742d35..."
    """
    try:
        wallet_data = await wallet_service.load_wallet_data(from_wallet_id)
        if not wallet_data:
            return "❌ Wallet nicht gefunden"
        
        tx_data = {
            "to": to_address,
            "value": amount,
            "chainId": 1
        }
        
        signed_tx = await wallet_service.sign_transaction(
            chain=chain,
            tx_data=tx_data,
            private_key_hex=private_key
        )
        
        result = await wallet_service.broadcast_transaction(
            chain=chain,
            signed_tx=signed_tx["signed_tx"]
        )
        
        return f"""✅ **Transaktion gesendet!**

🔗 **TX Hash**: {result['tx_hash']}
📤 **From**: {wallet_data['address'][:10]}...
📥 **To**: {to_address[:10]}...
💰 **Amount**: {amount}
⛓️ **Chain**: {chain.upper()}

Status: {result['status'].upper()}"""
        
    except Exception as e:
        logger.error(f"Error sending transaction: {e}")
        return f"❌ Fehler beim Senden: {str(e)}"


@tool("list_wallets", args_schema=ListWalletsInput)
async def list_wallets_tool(chain_filter: Optional[str] = None) -> str:
    """
    List all created wallets.
    
    Optional: Filter by chain.
    
    Example: "Show me all my wallets"
    """
    try:
        wallets = await wallet_service.list_wallets()
        
        if chain_filter:
            wallets = [w for w in wallets if w.get("chain", "").lower() == chain_filter.lower()]
        
        if not wallets:
            return "📭 Keine Wallets gefunden.\n\nMöchtest du eine neue Wallet erstellen?"
        
        result = f"💼 **Deine Wallets** ({len(wallets)} total)\n\n"
        
        for i, w in enumerate(wallets, 1):
            result += f"{i}. **{w.get('chain', 'unknown').upper()}**\n"
            result += f"   📋 ID: {w.get('id', 'N/A')}\n"
            result += f"   📫 Address: {w.get('address', 'N/A')[:10]}...\n"
            result += f"   💰 Balance: {w.get('balance', {}).get('balance', '0')}\n\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing wallets: {e}")
        return f"❌ Fehler beim Auflisten: {str(e)}"


@tool("get_wallet_history", args_schema=GetHistoryInput)
async def get_wallet_history_tool(wallet_id: str, limit: int = 50) -> str:
    """
    Get transaction history for wallet.
    
    Returns last N transactions with AI analysis.
    
    Example: "Show transaction history"
    """
    try:
        wallet_data = await wallet_service.load_wallet_data(wallet_id)
        if not wallet_data:
            return "❌ Wallet nicht gefunden"
        
        transactions = await wallet_service.get_wallet_history(
            chain=wallet_data["chain"],
            address=wallet_data["address"]
        )
        
        if not transactions:
            return "📭 Keine Transaktionen gefunden."
        
        result = f"📜 **Transaction History** ({len(transactions)} total)\n\n"
        
        for i, tx in enumerate(transactions[:min(10, limit)], 1):
            tx_hash = tx.get("hash") or tx.get("tx_hash", "N/A")
            direction = "📤" if tx.get("from", "").lower() == wallet_data["address"].lower() else "📥"
            
            result += f"{i}. {direction} {tx_hash[:10]}...\n"
            
            analysis = tx.get("analysis", {})
            if analysis.get("risk_score", 0) > 0.7:
                result += f"   ⚠️ High Risk: {analysis.get('risk_score', 0):.2f}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return f"❌ Fehler: {str(e)}"


@tool("analyze_wallet", args_schema=AnalyzeWalletInput)
async def analyze_wallet_tool(wallet_id: str) -> str:
    """
    Comprehensive forensic wallet analysis.
    
    Includes:
    - Transaction history
    - Risk scoring
    - Balance tracking
    - Counterparty analysis
    
    Example: "Analyze wallet abc123"
    """
    try:
        wallet_data = await wallet_service.load_wallet_data(wallet_id)
        if not wallet_data:
            return "❌ Wallet nicht gefunden"
        
        # Verwende die neue analyze_wallet Methode
        analysis = await wallet_service.analyze_wallet(
            chain=wallet_data["chain"],
            address=wallet_data["address"]
        )
        
        total_txs = analysis.get("total_transactions", 0)
        high_risk_txs = analysis.get("high_risk_transactions", 0)
        risk_score = analysis.get("risk_score", 0)
        
        # Risk Level basierend auf Score
        if risk_score < 0.3:
            risk_emoji = "🟢"
            risk_level = "LOW"
        elif risk_score < 0.7:
            risk_emoji = "🟡"
            risk_level = "MEDIUM"
        else:
            risk_emoji = "🔴"
            risk_level = "HIGH"
        
        result = f"""🔍 **Wallet Forensic Analysis**

📋 **Wallet ID**: {wallet_id}
🔗 **Chain**: {wallet_data['chain'].upper()}
📫 **Address**: {wallet_data['address'][:10]}...

{risk_emoji} **Risk Level**: {risk_level}
📊 **Risk Score**: {risk_score:.2f}

💰 **Balance**: {analysis.get('balance', '0')}
📈 **Total Transactions**: {total_txs}
🚨 **High-Risk TXs**: {high_risk_txs}
📥 **Total Received**: {analysis.get('total_received', '0')}
📤 **Total Sent**: {analysis.get('total_sent', '0')}

"""
        
        if analysis.get("risk_factors"):
            result += f"⚠️ **Risk Factors** ({len(analysis['risk_factors'])}):\n"
            for factor in analysis['risk_factors'][:5]:
                result += f"  • {factor}\n"
            result += "\n"
        
        if analysis.get("recommendations"):
            result += f"💡 **Recommendations**:\n"
            for rec in analysis['recommendations'][:3]:
                result += f"  • {rec}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing wallet: {e}")
        return f"❌ Fehler bei der Analyse: {str(e)}"


@tool("estimate_gas", args_schema=EstimateGasInput)
async def estimate_gas_tool(
    chain: str,
    from_address: str,
    to_address: str,
    value: str = "0"
) -> str:
    """
    Estimate gas costs for transaction.
    
    Returns gas limit, price, total cost.
    
    Example: "Estimate gas for sending 1 ETH"
    """
    try:
        # Verwende wallet_service.estimate_gas
        gas_estimate = await wallet_service.estimate_gas(
            chain=chain,
            tx_type="transfer",
            to_address=to_address
        )
        
        gas_limit = gas_estimate.get("gas_limit", 21000)
        gas_price_gwei = gas_estimate.get("gas_price_gwei", 0)
        cost_eth = gas_estimate.get("estimated_cost_eth", 0)
        cost_usd = gas_estimate.get("estimated_cost_usd", 0)
        
        result = f"""⛽ **Gas Estimate**

🔗 **Chain**: {chain.upper()}
📤 **From**: {from_address[:10]}...
📥 **To**: {to_address[:10]}...
💰 **Value**: {value}

**Estimates**:
• Gas Limit: {gas_limit:,}
• Gas Price: {gas_price_gwei} Gwei
• Total Cost: {cost_eth} ETH (~${cost_usd})

💡 **Tip**: Actual costs may vary based on network congestion."""
        
        return result
        
    except Exception as e:
        logger.error(f"Error estimating gas: {e}")
        return f"❌ Fehler bei Gas-Schätzung: {str(e)}"


# Export all wallet tools
WALLET_MANAGEMENT_TOOLS = [
    create_wallet_tool,
    import_wallet_tool,
    get_wallet_balance_tool,
    send_transaction_tool,
    list_wallets_tool,
    get_wallet_history_tool,
    analyze_wallet_tool,
    estimate_gas_tool,
]
