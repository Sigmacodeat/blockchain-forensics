"""
NFT API Endpunkte für Blockchain-Forensik-Anwendung

Bietet REST-API für NFT-Verwaltung und Portfolio-Analyse.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio

from app.services.nft_service import nft_service, nft_analyzer
from app.auth.dependencies import get_current_user
from app.caching.cache_service import cache_service

router = APIRouter(prefix="/api/v1/nft", tags=["nft"])

# Pydantic Models
class GetNFTsRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet-Adresse")
    chain: str = Field(..., description="Blockchain-Netzwerk")

class GetNFTMetadataRequest(BaseModel):
    contract_address: str = Field(..., description="NFT-Contract-Adresse")
    token_id: str = Field(..., description="Token-ID")
    chain: str = Field(..., description="Blockchain-Netzwerk")

class GetCollectionInfoRequest(BaseModel):
    contract_address: str = Field(..., description="Collection-Contract-Adresse")
    chain: str = Field(..., description="Blockchain-Netzwerk")

class AnalyzePortfolioRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet-Adresse")
    chain: str = Field(..., description="Blockchain-Netzwerk")

# API Endpunkte

@router.post("/portfolio", response_model=List[Dict[str, Any]])
async def get_wallet_nfts(
    request: GetNFTsRequest,
    current_user = Depends(get_current_user)
):
    """Holt alle NFTs für eine Wallet-Adresse"""
    try:
        nfts = await nft_service.get_nfts_for_wallet(
            wallet_address=request.wallet_address,
            chain=request.chain
        )

        return [nft.to_dict() for nft in nfts]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"NFT-Laden fehlgeschlagen: {str(e)}")

@router.post("/metadata", response_model=Optional[Dict[str, Any]])
async def get_nft_metadata(
    request: GetNFTMetadataRequest,
    current_user = Depends(get_current_user)
):
    """Holt Metadaten für ein spezifisches NFT"""
    try:
        metadata = await nft_service.get_nft_metadata(
            contract_address=request.contract_address,
            token_id=request.token_id,
            chain=request.chain
        )

        return metadata.to_dict() if metadata else None

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"NFT-Metadaten-Laden fehlgeschlagen: {str(e)}")

@router.post("/collection", response_model=Dict[str, Any])
async def get_collection_info(
    request: GetCollectionInfoRequest,
    current_user = Depends(get_current_user)
):
    """Holt Informationen über eine NFT-Collection"""
    try:
        collection_info = await nft_service.get_collection_info(
            contract_address=request.contract_address,
            chain=request.chain
        )

        return collection_info

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Collection-Info-Laden fehlgeschlagen: {str(e)}")

@router.post("/analyze/portfolio", response_model=Dict[str, Any])
async def analyze_nft_portfolio(
    request: AnalyzePortfolioRequest,
    current_user = Depends(get_current_user)
):
    """Führt umfassende Portfolio-Analyse durch"""
    try:
        analysis = await nft_analyzer.analyze_portfolio(
            wallet_address=request.wallet_address,
            chain=request.chain
        )

        return analysis

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Portfolio-Analyse fehlgeschlagen: {str(e)}")

@router.get("/supported-chains", response_model=List[str])
async def get_supported_nft_chains(current_user = Depends(get_current_user)):
    """Holt unterstützte Blockchains für NFT-Operationen"""
    return ["ethereum", "polygon", "solana", "avalanche"]

@router.get("/stats", response_model=Dict[str, Any])
async def get_nft_stats(current_user = Depends(get_current_user)):
    """Holt NFT-Statistiken"""
    try:
        # Hier könnten echte Statistiken aus der Datenbank kommen
        return {
            "total_collections_tracked": 0,
            "total_nfts_tracked": 0,
            "total_portfolio_value": 0,
            "supported_chains": ["ethereum", "polygon", "solana"],
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Statistiken-Laden fehlgeschlagen: {str(e)}")

@router.post("/refresh/metadata", response_model=Dict[str, Any])
async def refresh_nft_metadata(
    contract_address: str,
    token_id: str,
    chain: str,
    current_user = Depends(get_current_user)
):
    """Aktualisiert NFT-Metadaten (Cache-Invalidierung)"""
    try:
        # Cache löschen
        cache_key = f"nft_metadata_{chain}_{contract_address}_{token_id}"
        await cache_service.delete([cache_key])

        # Neue Metadaten laden
        metadata = await nft_service.get_nft_metadata(contract_address, token_id, chain)

        return {
            "refreshed": True,
            "metadata": metadata.to_dict() if metadata else None,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Metadaten-Aktualisierung fehlgeschlagen: {str(e)}")

@router.get("/trending/collections", response_model=List[Dict[str, Any]])
async def get_trending_collections(
    limit: int = 10,
    current_user = Depends(get_current_user)
):
    """Holt trending NFT-Collections"""
    try:
        # Hier könnten echte Trending-Daten kommen
        trending = [
            {
                "name": "Bored Ape Yacht Club",
                "contract_address": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
                "chain": "ethereum",
                "floor_price": 12.5,
                "volume_24h": 450.2,
                "change_24h": 5.2
            },
            {
                "name": "CryptoPunks",
                "contract_address": "0xb47e3cd837dDF8e4c57f05d70ab865de6e193bbb",
                "chain": "ethereum",
                "floor_price": 45.0,
                "volume_24h": 320.8,
                "change_24h": -2.1
            }
        ]

        return trending[:limit]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Trending-Daten-Laden fehlgeschlagen: {str(e)}")

# Import für datetime
from datetime import datetime
