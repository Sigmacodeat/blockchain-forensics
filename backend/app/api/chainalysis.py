"""
Chainalysis API Endpunkte für Blockchain-Forensik

Bietet REST-API für Chainalysis-Integration und Compliance-Prüfungen.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio

from app.services.chainalysis_integration import chainalysis_manager
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/chainalysis", tags=["chainalysis"])

# Pydantic Models
class AnalyzeAddressRequest(BaseModel):
    chain: str = Field(..., description="Blockchain-Netzwerk")
    address: str = Field(..., description="Zu analysierende Adresse")

class AnalyzeTransactionRequest(BaseModel):
    chain: str = Field(..., description="Blockchain-Netzwerk")
    tx_hash: str = Field(..., description="Transaktions-Hash")

class ComplianceCheckRequest(BaseModel):
    address: str = Field(..., description="Zu prüfende Adresse")
    chain: str = Field(..., description="Blockchain-Netzwerk")

class WalletAnalysisRequest(BaseModel):
    wallet_id: str = Field(..., description="Wallet-ID für umfassende Analyse")
    include_chainalysis: bool = Field(True, description="Chainalysis-Daten einschließen")

# API Endpunkte

@router.post("/analyze/address", response_model=Dict[str, Any])
async def analyze_address(
    request: AnalyzeAddressRequest,
    current_user = Depends(get_current_user)
):
    """Analysiert eine Adresse mit Chainalysis"""
    try:
        result = await chainalysis_manager.chainalysis_service.analyze_address(
            chain=request.chain,
            address=request.address
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Adressanalyse fehlgeschlagen: {str(e)}")

@router.post("/analyze/transaction", response_model=Dict[str, Any])
async def analyze_transaction(
    request: AnalyzeTransactionRequest,
    current_user = Depends(get_current_user)
):
    """Analysiert eine Transaktion mit Chainalysis"""
    try:
        result = await chainalysis_manager.chainalysis_service.analyze_transaction(
            chain=request.chain,
            tx_hash=request.tx_hash
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Transaktionsanalyse fehlgeschlagen: {str(e)}")

@router.post("/compliance/check", response_model=Dict[str, Any])
async def check_compliance(
    request: ComplianceCheckRequest,
    current_user = Depends(get_current_user)
):
    """Prüft Compliance-Status einer Adresse"""
    try:
        result = await chainalysis_manager.check_compliance_status(
            address=request.address,
            chain=request.chain
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Compliance-Prüfung fehlgeschlagen: {str(e)}")

@router.post("/wallet/analyze", response_model=Dict[str, Any])
async def analyze_wallet_comprehensive(
    request: WalletAnalysisRequest,
    current_user = Depends(get_current_user)
):
    """Führt umfassende Wallet-Analyse mit Chainalysis durch"""
    try:
        result = await chainalysis_manager.analyze_wallet_comprehensive(
            wallet_id=request.wallet_id,
            include_chainalysis=request.include_chainalysis
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Wallet-Analyse fehlgeschlagen: {str(e)}")

@router.get("/integration/status", response_model=Dict[str, Any])
async def get_integration_status(current_user = Depends(get_current_user)):
    """Holt Status der Chainalysis-Integration"""
    try:
        return chainalysis_manager.get_integration_status()

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden des Status: {str(e)}")

@router.get("/supported-chains", response_model=List[str])
async def get_supported_chains(current_user = Depends(get_current_user)):
    """Holt unterstützte Blockchains für Chainalysis"""
    try:
        status = chainalysis_manager.get_integration_status()
        return status.get("supported_chains", [])

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden der Chains: {str(e)}")

@router.post("/batch/analyze", response_model=List[Dict[str, Any]])
async def batch_analyze_addresses(
    addresses: List[Dict[str, str]],  # [{"chain": "bitcoin", "address": "1A1z..."}]
    current_user = Depends(get_current_user)
):
    """Analysiert mehrere Adressen in einem Batch"""
    try:
        results = []

        for addr_info in addresses:
            try:
                result = await chainalysis_manager.chainalysis_service.analyze_address(
                    chain=addr_info["chain"],
                    address=addr_info["address"]
                )
                results.append({
                    "chain": addr_info["chain"],
                    "address": addr_info["address"],
                    "analysis": result,
                    "success": True
                })
            except Exception as e:
                results.append({
                    "chain": addr_info["chain"],
                    "address": addr_info["address"],
                    "error": str(e),
                    "success": False
                })

        return results

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch-Analyse fehlgeschlagen: {str(e)}")

@router.post("/sanctions/screen", response_model=Dict[str, Any])
async def screen_sanctions(
    request: ComplianceCheckRequest,
    current_user = Depends(get_current_user)
):
    """Screening auf Sanktionen"""
    try:
        result = await chainalysis_manager.chainalysis_service.get_sanctions_data(
            address=request.address,
            chain=request.chain
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sanktions-Screening fehlgeschlagen: {str(e)}")

@router.get("/health", response_model=Dict[str, Any])
async def chainalysis_health_check(current_user = Depends(get_current_user)):
    """Health Check für Chainalysis-Integration"""
    try:
        # Basis-Health-Check
        basic_status = chainalysis_manager.get_integration_status()

        # Erweiterte Checks falls API verfügbar
        if basic_status["integration_enabled"]:
            try:
                # Test-API-Call mit bekannter Adresse
                test_result = await chainalysis_manager.chainalysis_service.analyze_address(
                    chain="bitcoin",
                    address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Satoshi's Genesis Address
                )
                api_available = True
            except Exception:
                api_available = False
        else:
            api_available = False

        return {
            **basic_status,
            "api_available": api_available,
            "health_status": "healthy" if basic_status["integration_enabled"] else "degraded"
        }

    except Exception as e:
        return {
            "integration_enabled": False,
            "api_available": False,
            "health_status": "error",
            "error": str(e)
        }

@router.get("/metrics", response_model=Dict[str, Any])
async def get_chainalysis_metrics(current_user = Depends(get_current_user)):
    """Holt Metriken für Chainalysis-Nutzung"""
    try:
        # Hier könnten echte Metriken aus der Chainalysis-Integration kommen
        return {
            "total_analyses": 0,  # Würde aus Datenbank kommen
            "cache_hits": 0,
            "api_calls": 0,
            "error_rate": 0.0,
            "supported_chains": ["bitcoin", "ethereum"],
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden der Metriken: {str(e)}")

# Import für datetime
from datetime import datetime
