"""
DeFi API Endpunkte für Blockchain-Forensik-Anwendung

Bietet REST-API für DeFi-Operationen und Analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio

from app.services.defi_service import defi_service, defi_analytics
from app.intel.defi.registry import get_all_protocols, get_labels_seed
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/defi", tags=["defi"])

# Pydantic Models
class GetLiquidityPoolsRequest(BaseModel):
    chain: str = Field(..., description="Blockchain-Netzwerk")
    protocol: str = Field("uniswap", description="DeFi-Protokoll")

class GetStakingPositionsRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet-Adresse")
    chain: str = Field(..., description="Blockchain-Netzwerk")

class AnalyzePortfolioRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet-Adresse")
    chain: str = Field(..., description="Blockchain-Netzwerk")

class YieldFarmingRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet-Adresse")
    chain: str = Field(..., description="Blockchain-Netzwerk")

# API Endpunkte

@router.post("/pools", response_model=List[Dict[str, Any]])
async def get_liquidity_pools(
    request: GetLiquidityPoolsRequest,
    current_user = Depends(get_current_user)
):
    """Holt Liquidity Pools für eine Chain"""
    try:
        pools = await defi_service.get_liquidity_pools(
            chain=request.chain,
            protocol=request.protocol
        )

        return [pool.to_dict() for pool in pools]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Liquidity Pools Laden fehlgeschlagen: {str(e)}")

@router.post("/staking", response_model=List[Dict[str, Any]])
async def get_staking_positions(
    request: GetStakingPositionsRequest,
    current_user = Depends(get_current_user)
):
    """Holt Staking-Positionen für eine Wallet"""
    try:
        positions = await defi_service.get_staking_positions(
            wallet_address=request.wallet_address,
            chain=request.chain
        )

        return [pos.to_dict() for pos in positions]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Staking-Positionen Laden fehlgeschlagen: {str(e)}")

@router.post("/analyze/portfolio", response_model=Dict[str, Any])
async def analyze_defi_portfolio(
    request: AnalyzePortfolioRequest,
    current_user = Depends(get_current_user)
):
    """Führt umfassende DeFi-Portfolio-Analyse durch"""
    try:
        analysis = await defi_analytics.analyze_defi_portfolio(
            wallet_address=request.wallet_address,
            chain=request.chain
        )

        return analysis

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DeFi-Portfolio-Analyse fehlgeschlagen: {str(e)}")

@router.post("/yield-farming", response_model=List[Dict[str, Any]])
async def get_yield_farming_opportunities(
    request: YieldFarmingRequest,
    current_user = Depends(get_current_user)
):
    """Holt Yield Farming Möglichkeiten"""
    try:
        opportunities = await defi_service.calculate_yield_farming_opportunities(
            wallet_address=request.wallet_address,
            chain=request.chain
        )

        return opportunities

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Yield Farming Berechnung fehlgeschlagen: {str(e)}")

@router.get("/protocols", response_model=List[str])
async def get_supported_protocols(current_user = Depends(get_current_user)):
    """Holt unterstützte DeFi-Protokolle"""
    return ["uniswap", "sushiswap", "pancakeswap", "curve", "compound", "aave"]

@router.get("/supported-chains", response_model=List[str])
async def get_supported_defi_chains(current_user = Depends(get_current_user)):
    """Holt unterstützte Chains für DeFi"""
    return ["ethereum", "polygon", "bsc", "avalanche", "arbitrum", "optimism"]


# ---- Registry (read-only) ----

@router.get("/registry/protocols", response_model=List[Dict[str, Any]])
async def get_registry_protocols(current_user = Depends(get_current_user)):
    """Liest die modulare DeFi-Registry (Protokolle, Metadaten) aus (read-only)."""
    try:
        protocols = get_all_protocols()
        # keine sensiblen Daten, reiner Read
        return protocols
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registry laden fehlgeschlagen: {str(e)}")


@router.get("/registry/labels/preview", response_model=Dict[str, Any])
async def get_registry_labels_preview(limit: int = 100, current_user = Depends(get_current_user)):
    """Erzeugt eine Vorschau der Labels aus der Registry inkl. Zählwerten (read-only, keine DB-Schreibungen)."""
    try:
        items = get_labels_seed()
        total = len(items)
        # Nur Vorschau zurückgeben
        preview = items[: max(0, min(limit, 1000))]
        return {"total": total, "count": len(preview), "items": preview}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Labels-Preview fehlgeschlagen: {str(e)}")

@router.get("/stats", response_model=Dict[str, Any])
async def get_defi_stats(current_user = Depends(get_current_user)):
    """Holt DeFi-Statistiken"""
    try:
        # Hier könnten echte Statistiken aus der Datenbank kommen
        return {
            "total_liquidity_pools": 0,
            "total_staking_positions": 0,
            "total_tvl": 0,
            "total_yield_earned": 0,
            "supported_protocols": ["uniswap", "sushiswap", "pancakeswap"],
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DeFi-Statistiken Laden fehlgeschlagen: {str(e)}")

@router.get("/trending/pools", response_model=List[Dict[str, Any]])
async def get_trending_pools(
    limit: int = 10,
    current_user = Depends(get_current_user)
):
    """Holt trending Liquidity Pools"""
    try:
        # Hier könnten echte Trending-Daten kommen
        trending = [
            {
                "address": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640",
                "protocol": "uniswap",
                "chain": "ethereum",
                "token0": "USDC",
                "token1": "WETH",
                "tvl": 1500000,
                "volume_24h": 250000,
                "apy": 15.5,
                "change_24h": 5.2
            }
        ]

        return trending[:limit]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Trending Pools Laden fehlgeschlagen: {str(e)}")

@router.get("/risk-analysis", response_model=Dict[str, Any])
async def get_defi_risk_analysis(
    chain: str,
    current_user = Depends(get_current_user)
):
    """Holt DeFi-Risikoanalyse für eine Chain"""
    try:
        # Basis-Risikoanalyse
        analysis = {
            "chain": chain,
            "overall_risk": "medium",
            "risk_factors": [
                "Smart Contract Risiken",
                "Impermanent Loss",
                "Liquiditätsrisiken",
                "Marktvolatilität"
            ],
            "recommendations": [
                "Diversifikation über mehrere Pools",
                "Regelmäßige Portfolio-Überprüfung",
                "IL-Schutz-Mechanismen nutzen"
            ],
            "risk_score": 0.6,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

        return analysis

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DeFi-Risikoanalyse fehlgeschlagen: {str(e)}")

# Import für datetime
from datetime import datetime
