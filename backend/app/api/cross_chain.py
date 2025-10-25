"""
Cross-Chain API Endpunkte für Blockchain-Forensik-Anwendung

Bietet REST-API für Cross-Chain-Swaps und Bridge-Operationen.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio

from app.services.cross_chain_service import cross_chain_service, cross_chain_analytics
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/cross-chain", tags=["cross-chain"])

# Pydantic Models
class SwapQuoteRequest(BaseModel):
    from_token: str = Field(..., description="Token zum Verkaufen")
    to_token: str = Field(..., description="Token zum Kaufen")
    amount: str = Field(..., description="Betrag zum Swappen")
    from_chain: str = Field(..., description="Source Blockchain")
    to_chain: Optional[str] = Field(None, description="Target Blockchain (optional für Same-Chain)")

class BridgeTransactionRequest(BaseModel):
    bridge_id: str = Field(..., description="Bridge ID")
    from_token: str = Field(..., description="Source Token")
    from_amount: str = Field(..., description="Betrag zum Bridgen")
    to_address: str = Field(..., description="Empfänger-Adresse auf Ziel-Chain")
    wallet_address: str = Field(..., description="Ihre Wallet-Adresse")

class GetBridgesRequest(BaseModel):
    from_chain: str = Field(..., description="Source Blockchain")
    to_chain: str = Field(..., description="Target Blockchain")

class SupportedTokensRequest(BaseModel):
    chain: str = Field(..., description="Blockchain-Netzwerk")

class ArbitrageAnalysisRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet-Adresse für Analyse")

# API Endpunkte

@router.post("/swap-quote", response_model=Dict[str, Any])
async def get_swap_quote(
    request: SwapQuoteRequest,
    current_user = Depends(get_current_user)
):
    """Holt ein Swap-Quote für Cross-Chain oder Same-Chain-Swaps"""
    try:
        quote = await cross_chain_service.get_swap_quote(
            from_token=request.from_token,
            to_token=request.to_token,
            amount=request.amount,
            from_chain=request.from_chain,
            to_chain=request.to_chain
        )

        if quote:
            return quote.to_dict()
        else:
            raise HTTPException(status_code=404, detail="Kein Quote verfügbar")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Swap-Quote fehlgeschlagen: {str(e)}")

@router.post("/bridges", response_model=List[Dict[str, Any]])
async def get_available_bridges(
    request: GetBridgesRequest,
    current_user = Depends(get_current_user)
):
    """Holt verfügbare Bridges zwischen zwei Chains"""
    try:
        bridges = await cross_chain_service.get_available_bridges(
            from_chain=request.from_chain,
            to_chain=request.to_chain
        )

        return [bridge.to_dict() for bridge in bridges]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bridges Laden fehlgeschlagen: {str(e)}")

@router.post("/bridge/initiate", response_model=Dict[str, Any])
async def initiate_bridge_transaction(
    request: BridgeTransactionRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Initiiert eine Bridge-Transaktion"""
    try:
        tx_hash = await cross_chain_service.initiate_bridge_transaction(
            bridge_id=request.bridge_id,
            from_token=request.from_token,
            from_amount=request.from_amount,
            to_address=request.to_address,
            wallet_address=request.wallet_address
        )

        if tx_hash:
            return {
                "tx_hash": tx_hash,
                "status": "initiated",
                "message": "Bridge-Transaktion wurde gestartet"
            }
        else:
            raise HTTPException(status_code=400, detail="Bridge-Transaktion konnte nicht gestartet werden")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bridge-Initiierung fehlgeschlagen: {str(e)}")

@router.get("/bridge/status/{tx_hash}", response_model=Dict[str, Any])
async def get_bridge_transaction_status(
    tx_hash: str,
    current_user = Depends(get_current_user)
):
    """Holt den Status einer Bridge-Transaktion"""
    try:
        tx = await cross_chain_service.get_bridge_transaction_status(tx_hash)

        if tx:
            return tx.to_dict()
        else:
            raise HTTPException(status_code=404, detail="Bridge-Transaktion nicht gefunden")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bridge-Status fehlgeschlagen: {str(e)}")

@router.post("/tokens", response_model=List[Dict[str, Any]])
async def get_supported_tokens(
    request: SupportedTokensRequest,
    current_user = Depends(get_current_user)
):
    """Holt unterstützte Token für eine Chain"""
    try:
        tokens = await cross_chain_service.get_supported_tokens(request.chain)

        return tokens

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token Laden fehlgeschlagen: {str(e)}")

@router.post("/arbitrage/analyze", response_model=Dict[str, Any])
async def analyze_arbitrage_opportunities(
    request: ArbitrageAnalysisRequest,
    current_user = Depends(get_current_user)
):
    """Analysiert Cross-Chain-Arbitrage-Möglichkeiten"""
    try:
        analysis = await cross_chain_analytics.analyze_cross_chain_opportunities(
            wallet_address=request.wallet_address
        )

        return analysis

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Arbitrage-Analyse fehlgeschlagen: {str(e)}")

@router.get("/supported-chains", response_model=List[str])
async def get_supported_cross_chain_chains(current_user = Depends(get_current_user)):
    """Holt unterstützte Chains für Cross-Chain-Operationen"""
    return ["ethereum", "polygon", "bsc", "avalanche", "arbitrum", "optimism"]

@router.get("/swap-providers", response_model=List[str])
async def get_swap_providers(current_user = Depends(get_current_user)):
    """Holt verfügbare Swap-Provider"""
    return ["1inch", "uniswap", "sushiswap", "pancakeswap", "0x", "paraswap"]

@router.get("/bridge-protocols", response_model=List[str])
async def get_bridge_protocols(current_user = Depends(get_current_user)):
    """Holt verfügbare Bridge-Protokolle"""
    return ["polygon_bridge", "hop", "celer", "multichain", "arbitrum_bridge", "optimism_gateway"]

@router.get("/stats", response_model=Dict[str, Any])
async def get_cross_chain_stats(current_user = Depends(get_current_user)):
    """Holt Cross-Chain-Statistiken"""
    try:
        return {
            "total_bridges": 12,
            "total_swaps_today": 156,
            "average_bridge_time": 15,  # Minuten
            "supported_token_pairs": 245,
            "total_volume_24h": 1250000,  # USD
            "active_routes": [
                "ethereum ↔ polygon",
                "ethereum ↔ arbitrum",
                "polygon ↔ bsc",
                "avalanche ↔ ethereum"
            ],
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cross-Chain-Statistiken fehlgeschlagen: {str(e)}")

@router.get("/fees/{from_chain}/{to_chain}", response_model=Dict[str, Any])
async def get_bridge_fees(
    from_chain: str,
    to_chain: str,
    current_user = Depends(get_current_user)
):
    """Holt Bridge-Fees für eine Route"""
    try:
        bridges = await cross_chain_service.get_available_bridges(from_chain, to_chain)

        if not bridges:
            return {"fees": [], "message": "Keine Bridges verfügbar"}

        fees = []
        for bridge in bridges:
            fees.append({
                "bridge_id": bridge.bridge_id,
                "protocol": bridge.protocol,
                "fee": bridge.fee,
                "fee_percent": (bridge.fee or 0) / 100,
                "min_amount": bridge.min_amount,
                "max_amount": bridge.max_amount,
                "estimated_time": bridge.estimated_time
            })

        return {
            "from_chain": from_chain,
            "to_chain": to_chain,
            "fees": fees,
            "best_bridge": min(fees, key=lambda x: x["fee"]) if fees else None
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bridge-Fees fehlgeschlagen: {str(e)}")

# Import für datetime
from datetime import datetime
