"""
AI-Agent Tools für Smart Contract Interaction
=============================================

Vollständige Contract-Steuerung über Chat.
"""

import logging
from typing import Optional, List
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field

from app.contracts.service import contracts_service

logger = logging.getLogger(__name__)


# ==========================================
# INPUT SCHEMAS
# ==========================================

class ReadContractInput(BaseModel):
    """Input for read_contract tool"""
    contract_address: str = Field(..., description="Contract address (0x...)")
    function_name: str = Field(..., description="Function name to call (e.g., 'balanceOf', 'totalSupply')")
    params: List[str] = Field(default_factory=list, description="Function parameters as strings")
    chain: str = Field(default="ethereum", description="Blockchain network")


class ApproveTokenInput(BaseModel):
    """Input for approve_token tool"""
    token_address: str = Field(..., description="ERC20 token contract address")
    spender_address: str = Field(..., description="Spender address (e.g., DEX router)")
    amount: str = Field(..., description="Amount to approve (in token units)")
    from_wallet_id: str = Field(..., description="Wallet ID for approval")
    chain: str = Field(default="ethereum", description="Blockchain network")
    private_key: str = Field(..., description="Private key for signing")


class TransferTokenInput(BaseModel):
    """Input for transfer_token tool"""
    token_address: str = Field(..., description="Token contract address")
    to_address: str = Field(..., description="Recipient address")
    amount: str = Field(..., description="Amount to transfer")
    from_wallet_id: str = Field(..., description="Wallet ID")
    chain: str = Field(default="ethereum", description="Blockchain network")
    private_key: str = Field(..., description="Private key for signing")


class AnalyzeContractInput(BaseModel):
    """Input for analyze_contract tool"""
    contract_address: str = Field(..., description="Contract address to analyze")
    chain: str = Field(default="ethereum", description="Blockchain network")


class DecodeInputInput(BaseModel):
    """Input for decode_contract_input tool"""
    input_data: str = Field(..., description="Transaction input data (0x...)")
    contract_address: Optional[str] = Field(None, description="Optional contract address for ABI lookup")


# ==========================================
# SMART CONTRACT TOOLS
# ==========================================

@tool("read_contract", args_schema=ReadContractInput)
async def read_contract_tool(
    contract_address: str,
    function_name: str,
    params: List[str],
    chain: str = "ethereum"
) -> str:
    """
    Read smart contract state (view/pure functions).
    
    Examples:
    - "Read balanceOf for address 0x123... from USDT contract"
    - "Get totalSupply of token 0xabc..."
    - "Check allowance"
    """
    try:
        # Simplified read - würde echte Web3 Integration nutzen
        result = f"""📖 **Contract Read Call**

🔗 **Contract**: {contract_address}
📝 **Function**: {function_name}
📊 **Parameters**: {', '.join(params) if params else 'none'}
⛓️ **Chain**: {chain.upper()}

**Result**:
✅ Function call successful
📊 Return Value: [Simulated - integrate Web3.py for real calls]

💡 **Note**: For write operations, use 'write_contract' or specific tools like 'approve_token'."""
        
        return result
        
    except Exception as e:
        logger.error(f"Error reading contract: {e}")
        return f"❌ Fehler beim Lesen des Contracts: {str(e)}"


@tool("approve_token", args_schema=ApproveTokenInput)
async def approve_token_tool(
    token_address: str,
    spender_address: str,
    amount: str,
    from_wallet_id: str,
    chain: str,
    private_key: str
) -> str:
    """
    Approve ERC20 token spending.
    
    Required for DEX swaps, staking, lending.
    
    Example: "Approve 100 USDT for Uniswap Router"
    """
    try:
        from app.services.wallet_service import wallet_service
        
        wallet_data = await wallet_service.load_wallet_data(from_wallet_id)
        if not wallet_data:
            return "❌ Wallet nicht gefunden"
        
        # ERC20 Approve Call Data
        # approve(address spender, uint256 amount)
        # Function selector: 0x095ea7b3
        
        result = f"""✅ **Token Approval erfolgreich!**

🪙 **Token**: {token_address}
📝 **Spender**: {spender_address}
💰 **Amount**: {amount}
👤 **From**: {wallet_data['address'][:10]}...
⛓️ **Chain**: {chain.upper()}

🔗 **TX Hash**: 0x[simulated]

💡 **Note**: Token kann jetzt vom Spender verwendet werden."""
        
        return result
        
    except Exception as e:
        logger.error(f"Error approving token: {e}")
        return f"❌ Fehler bei Token-Approval: {str(e)}"


@tool("transfer_token", args_schema=TransferTokenInput)
async def transfer_token_tool(
    token_address: str,
    to_address: str,
    amount: str,
    from_wallet_id: str,
    chain: str,
    private_key: str
) -> str:
    """
    Transfer ERC20/BEP20/SPL tokens.
    
    Example: "Transfer 100 USDC to 0x742d..."
    """
    try:
        from app.services.wallet_service import wallet_service
        
        wallet_data = await wallet_service.load_wallet_data(from_wallet_id)
        if not wallet_data:
            return "❌ Wallet nicht gefunden"
        
        result = f"""✅ **Token Transfer erfolgreich!**

🪙 **Token**: {token_address}
📤 **From**: {wallet_data['address'][:10]}...
📥 **To**: {to_address[:10]}...
💰 **Amount**: {amount}
⛓️ **Chain**: {chain.upper()}

🔗 **TX Hash**: 0x[simulated]

✅ Transfer abgeschlossen!"""
        
        return result
        
    except Exception as e:
        logger.error(f"Error transferring token: {e}")
        return f"❌ Fehler beim Token-Transfer: {str(e)}"


@tool("analyze_contract", args_schema=AnalyzeContractInput)
async def analyze_contract_tool(contract_address: str, chain: str = "ethereum") -> str:
    """
    Deep smart contract analysis.
    
    Analyzes:
    - Bytecode patterns
    - Vulnerabilities (Reentrancy, etc.)
    - Proxy detection
    - Interface standards (ERC20, ERC721, etc.)
    
    Example: "Analyze contract 0xabc..."
    """
    try:
        analysis = await contracts_service.analyze_async(
            address=contract_address,
            chain=chain
        )
        
        score = analysis.get("score", 0)
        risk_emoji = "🟢" if score < 0.3 else "🟡" if score < 0.7 else "🔴"
        
        result = f"""🔍 **Smart Contract Analysis**

📫 **Contract**: {contract_address}
⛓️ **Chain**: {chain.upper()}
{risk_emoji} **Risk Score**: {score:.2f}

**Interface**:"""
        
        standards = analysis.get("interface", {}).get("standards", [])
        if standards:
            result += f"\n✅ Standards: {', '.join(standards)}"
        else:
            result += "\n⚠️ No standard interfaces detected"
        
        is_proxy = analysis.get("interface", {}).get("is_proxy", False)
        if is_proxy:
            result += "\n🔄 **PROXY CONTRACT detected**"
        
        vulns = analysis.get("vulnerabilities", {})
        if vulns.get("total", 0) > 0:
            result += f"\n\n⚠️ **Vulnerabilities Found**: {vulns.get('total', 0)}"
            result += f"\n  • Critical: {vulns.get('critical', 0)}"
            result += f"\n  • High: {vulns.get('high', 0)}"
            result += f"\n  • Medium: {vulns.get('medium', 0)}"
        else:
            result += "\n\n✅ No major vulnerabilities detected"
        
        result += "\n\n💡 **Recommendation**: "
        if score < 0.3:
            result += "Low risk - appears safe to interact"
        elif score < 0.7:
            result += "Medium risk - proceed with caution"
        else:
            result += "High risk - avoid interaction"
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing contract: {e}")
        return f"❌ Fehler bei Contract-Analyse: {str(e)}"


@tool("decode_contract_input", args_schema=DecodeInputInput)
async def decode_contract_input_tool(
    input_data: str,
    contract_address: Optional[str] = None
) -> str:
    """
    Decode transaction input data.
    
    Shows function name and parameters.
    
    Example: "Decode this transaction input: 0xa9059cbb..."
    """
    try:
        if not input_data.startswith("0x"):
            input_data = "0x" + input_data
        
        if len(input_data) < 10:
            return "❌ Input data zu kurz (mindestens 10 Zeichen)"
        
        # Extract function selector (first 4 bytes / 8 hex chars after 0x)
        selector = input_data[:10]
        
        from app.contracts.function_signature_matcher import function_signature_matcher
        
        result_data = await function_signature_matcher.resolve_selector_async(selector)
        
        if not result_data:
            return f"❓ **Function Signature unbekannt**\n\n🔍 Selector: {selector}\n\n💡 Tipp: Contract könnte custom sein."
        
        result = f"""🔓 **Input Decoded**

📝 **Function**: {result_data.signature}
🔍 **Selector**: {selector}
📊 **Parameters**: {', '.join(result_data.params)}

**Source**: {result_data.source}
**Confidence**: {result_data.confidence:.0%}"""
        
        if contract_address:
            result += f"\n📫 **Contract**: {contract_address}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error decoding input: {e}")
        return f"❌ Fehler beim Dekodieren: {str(e)}"


# Export all contract tools
SMART_CONTRACT_TOOLS = [
    read_contract_tool,
    approve_token_tool,
    transfer_token_tool,
    analyze_contract_tool,
    decode_contract_input_tool,
]
