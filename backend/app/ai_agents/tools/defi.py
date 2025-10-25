"""
DeFi Analysis Tools for AI Agent.
Analyze interactions with DeFi protocols, trace fund flows, and assess exposure.
"""

import logging
from typing import List, Optional, Dict, Any
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field

logger = logging.getLogger(__name__)


# Input Schemas
class AnalyzeProtocolInput(BaseModel):
    """Input for analyze_defi_protocol tool"""
    protocol: str = Field(..., description="Protocol name: uniswap, aave, curve, compound, etc.")
    address: str = Field(..., description="Ethereum address to analyze")
    include_positions: bool = Field(default=True, description="Include open positions")


class TraceDeFiFlowInput(BaseModel):
    """Input for trace_defi_flow tool"""
    address: str = Field(..., description="Address to trace")
    protocols: Optional[List[str]] = Field(None, description="Specific protocols to analyze")
    max_depth: int = Field(default=3, description="Maximum tracing depth")


class GetExposureInput(BaseModel):
    """Input for get_defi_exposure tool"""
    address: str = Field(..., description="Address to check")
    include_history: bool = Field(default=False, description="Include historical positions")


# Tools Implementation
@tool("analyze_defi_protocol", args_schema=AnalyzeProtocolInput)
async def analyze_defi_protocol_tool(
    protocol: str,
    address: str,
    include_positions: bool = True
) -> Dict[str, Any]:
    """
    Analyze interactions with DeFi protocols.
    
    Supported protocols:
    - Uniswap: DEX and liquidity pools
    - Aave: Lending and borrowing
    - Curve: Stablecoin swaps
    - Compound: Money markets
    - Lido: Staking
    - MakerDAO: CDP and DAI
    
    Returns:
    - Total value locked (TVL)
    - Open positions
    - Transaction history
    - Risk factors
    
    Examples:
    - "Analyze Uniswap activity for address 0xABC..."
    - "What are the Aave positions for this address?"
    """
    try:
        from app.services.defi_service import defi_service
        
        analysis = await defi_service.analyze_protocol_interaction(
            protocol=protocol.lower(),
            address=address,
            include_positions=include_positions
        )
        
        return {
            "success": True,
            "protocol": protocol,
            "address": address,
            "total_value_locked": analysis.get("tvl", 0),
            "positions": analysis.get("positions", []),
            "transaction_count": analysis.get("tx_count", 0),
            "risk_factors": analysis.get("risks", []),
            "last_activity": analysis.get("last_activity")
        }
        
    except ImportError:
        # Fallback with mock DeFi data
        mock_analysis = {
            "tvl": 125000.50,
            "positions": [
                {
                    "type": "liquidity_pool",
                    "pair": "ETH/USDC",
                    "value_usd": 75000,
                    "share": "0.02%"
                },
                {
                    "type": "lending",
                    "asset": "ETH",
                    "supplied": 25.5,
                    "value_usd": 50000.50
                }
            ],
            "tx_count": 234,
            "risks": ["impermanent_loss", "smart_contract_risk"],
            "last_activity": "2025-10-15T14:30:00Z"
        }
        
        return {
            "success": True,
            "protocol": protocol,
            "address": address,
            "total_value_locked": mock_analysis["tvl"],
            "positions": mock_analysis["positions"] if include_positions else [],
            "transaction_count": mock_analysis["tx_count"],
            "risk_factors": mock_analysis["risks"],
            "last_activity": mock_analysis["last_activity"],
            "message": "Using mock data - defi_service not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing DeFi protocol: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to analyze {protocol} for {address}"
        }


@tool("trace_defi_flow", args_schema=TraceDeFiFlowInput)
async def trace_defi_flow_tool(
    address: str,
    protocols: Optional[List[str]] = None,
    max_depth: int = 3
) -> Dict[str, Any]:
    """
    Trace fund flows through DeFi protocols.
    
    Identifies patterns:
    - Flash loans
    - Arbitrage strategies
    - Liquidity mining
    - Yield farming
    - MEV extraction
    
    Examples:
    - "Trace DeFi flows for address 0xABC..."
    - "How did funds move through DeFi protocols?"
    """
    try:
        from app.services.defi_service import defi_service
        
        flow = await defi_service.trace_defi_flow(
            address=address,
            protocols=protocols,
            max_depth=max_depth
        )
        
        return {
            "success": True,
            "address": address,
            "protocols_used": flow.get("protocols", []),
            "total_volume": flow.get("total_volume", 0),
            "patterns": flow.get("patterns", []),
            "flow_diagram": flow.get("flow_diagram", {}),
            "suspicious_activity": flow.get("suspicious", False)
        }
        
    except ImportError:
        # Fallback with mock flow data
        mock_flow = {
            "protocols": ["Uniswap", "Aave", "Curve"],
            "total_volume": 2500000,
            "patterns": [
                {
                    "type": "arbitrage",
                    "description": "Swap ETH → USDC on Uniswap, deposit to Aave",
                    "profit": 1250
                },
                {
                    "type": "yield_farming",
                    "description": "Deposit USDC to Curve, stake LP tokens",
                    "apy": "8.5%"
                }
            ],
            "flow_diagram": {
                "steps": [
                    "Uniswap: Swap ETH → USDC",
                    "Aave: Deposit USDC",
                    "Curve: Add liquidity",
                    "Convex: Stake LP tokens"
                ]
            },
            "suspicious": False
        }
        
        return {
            "success": True,
            "address": address,
            "protocols_used": mock_flow["protocols"],
            "total_volume": mock_flow["total_volume"],
            "patterns": mock_flow["patterns"],
            "flow_diagram": mock_flow["flow_diagram"],
            "suspicious_activity": mock_flow["suspicious"],
            "message": "Using mock data - defi_service not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error tracing DeFi flow: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to trace DeFi flow"
        }


@tool("get_defi_exposure", args_schema=GetExposureInput)
async def get_defi_exposure_tool(
    address: str,
    include_history: bool = False
) -> Dict[str, Any]:
    """
    Get complete DeFi exposure for an address.
    
    Shows all:
    - Active positions across all protocols
    - Total value locked
    - Risk assessment
    - Historical positions (if requested)
    
    Risk factors analyzed:
    - Smart contract risk
    - Impermanent loss
    - Liquidation risk
    - Concentration risk
    
    Examples:
    - "What is the DeFi exposure for this address?"
    - "Show me all DeFi positions"
    """
    try:
        from app.services.defi_service import defi_service
        
        exposure = await defi_service.get_exposure(
            address=address,
            include_history=include_history
        )
        
        return {
            "success": True,
            "address": address,
            "total_exposure_usd": exposure.get("total_usd", 0),
            "protocols": exposure.get("protocols", []),
            "positions_count": len(exposure.get("protocols", [])),
            "risk_level": exposure.get("risk_level", "medium"),
            "risk_score": exposure.get("risk_score", 0.5),
            "recommendations": exposure.get("recommendations", []),
            "history": exposure.get("history", []) if include_history else None
        }
        
    except ImportError:
        # Fallback with mock exposure data
        mock_exposure = {
            "total_usd": 325000,
            "protocols": [
                {
                    "name": "Uniswap",
                    "tvl": 125000,
                    "positions": 3,
                    "risk": "low"
                },
                {
                    "name": "Aave",
                    "tvl": 150000,
                    "positions": 2,
                    "risk": "medium"
                },
                {
                    "name": "Curve",
                    "tvl": 50000,
                    "positions": 1,
                    "risk": "low"
                }
            ],
            "risk_level": "medium",
            "risk_score": 0.45,
            "recommendations": [
                "Consider diversifying across more protocols",
                "Monitor Aave health factor (currently 1.8)"
            ],
            "history": [
                {
                    "date": "2025-09-01",
                    "protocol": "Compound",
                    "action": "withdraw",
                    "amount_usd": 75000
                }
            ] if include_history else []
        }
        
        return {
            "success": True,
            "address": address,
            "total_exposure_usd": mock_exposure["total_usd"],
            "protocols": mock_exposure["protocols"],
            "positions_count": len(mock_exposure["protocols"]),
            "risk_level": mock_exposure["risk_level"],
            "risk_score": mock_exposure["risk_score"],
            "recommendations": mock_exposure["recommendations"],
            "history": mock_exposure["history"] if include_history else None,
            "message": "Using mock data - defi_service not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error getting DeFi exposure: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get DeFi exposure"
        }


# Export all DeFi tools
DEFI_TOOLS = [
    analyze_defi_protocol_tool,
    trace_defi_flow_tool,
    get_defi_exposure_tool,
]

logger.info(f"✅ DeFi Tools loaded: {len(DEFI_TOOLS)} tools")
