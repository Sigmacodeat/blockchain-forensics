"""
Wallet API Endpunkte für Blockchain-Forensik-Plattform

Bietet REST-API für Wallet-Operationen mit KI-Integration.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio

from app.services.wallet_service import wallet_service
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/wallet", tags=["wallet"])

# Pydantic Models
class CreateWalletRequest(BaseModel):
    chain: str = Field(..., description="Blockchain-Netzwerk (ethereum, bitcoin, solana, etc.)")
    mnemonic: Optional[str] = Field(None, description="Optionaler Mnemonic für deterministische Wallets")

class WalletResponse(BaseModel):
    id: str
    chain: str
    address: str
    public_key: str
    balance: Dict[str, Any]
    created_at: float
    risk_score: Optional[float] = None
    risk_factors: Optional[List[str]] = None

class TransactionRequest(BaseModel):
    chain: str
    to_address: str
    amount: str  # Als String für präzise Dezimaldarstellung
    private_key: str
    gas_price: Optional[str] = None
    gas_limit: Optional[int] = None

class TransactionResponse(BaseModel):
    tx_hash: str
    status: str
    analysis: Dict[str, Any]
    timestamp: float

class WalletHistoryResponse(BaseModel):
    transactions: List[Dict[str, Any]]
    total_count: int

class BroadcastRequest(BaseModel):
    chain: str
    signed_tx: str

# API Endpunkte

@router.post("/create", response_model=WalletResponse)
async def create_wallet(
    request: CreateWalletRequest,
    current_user = Depends(get_current_user)
):
    """Erstellt eine neue Wallet für eine spezifische Chain"""
    try:
        wallet_data = await wallet_service.create_wallet(
            chain=request.chain,
            mnemonic=request.mnemonic
        )

        return WalletResponse(
            id=wallet_data["id"],
            chain=wallet_data["chain"],
            address=wallet_data["address"],
            public_key=wallet_data["public_key"],
            balance=wallet_data["balance"],
            created_at=wallet_data["created_at"],
            risk_score=wallet_data["balance"].get("risk_score"),
            risk_factors=wallet_data["balance"].get("risk_factors")
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Erstellen der Wallet: {str(e)}")

@router.get("/{wallet_id}/balance", response_model=Dict[str, Any])
async def get_wallet_balance(
    wallet_id: str,
    current_user = Depends(get_current_user)
):
    """Holt den aktuellen Kontostand einer Wallet"""
    try:
        wallet_data = await wallet_service.load_wallet_data(wallet_id)
        if not wallet_data:
            raise HTTPException(status_code=404, detail="Wallet nicht gefunden")

        balance = await wallet_service.get_balance(
            chain=wallet_data["chain"],
            address=wallet_data["address"]
        )

        return balance

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden des Balances: {str(e)}")

@router.post("/sign", response_model=Dict[str, Any])
async def sign_transaction(
    request: TransactionRequest,
    current_user = Depends(get_current_user)
):
    """Signiert eine Transaktion"""
    try:
        # Transaktionsdaten vorbereiten
        tx_data = {
            "to": request.to_address,
            "value": str(request.amount),
            "chainId": 1  # Standard Chain ID
        }

        if request.gas_price:
            tx_data["gasPrice"] = request.gas_price
        if request.gas_limit:
            tx_data["gasLimit"] = request.gas_limit

        # Transaktion signieren
        signed_tx = await wallet_service.sign_transaction(
            chain=request.chain,
            tx_data=tx_data,
            private_key_hex=request.private_key
        )

        return signed_tx

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Signieren: {str(e)}")

@router.post("/broadcast", response_model=TransactionResponse)
async def broadcast_transaction(
    request: BroadcastRequest,
    current_user = Depends(get_current_user)
):
    """Broadcastet eine signierte Transaktion"""
    try:
        result = await wallet_service.broadcast_transaction(
            chain=request.chain,
            signed_tx=request.signed_tx
        )

        return TransactionResponse(
            tx_hash=result["tx_hash"],
            status=result["status"],
            analysis=result["analysis"],
            timestamp=result["timestamp"]
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Broadcasten: {str(e)}")

@router.get("/{wallet_id}/history", response_model=WalletHistoryResponse)
async def get_wallet_history(
    wallet_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user = Depends(get_current_user)
):
    """Holt die Transaktionshistorie einer Wallet"""
    try:
        wallet_data = await wallet_service.load_wallet_data(wallet_id)
        if not wallet_data:
            raise HTTPException(status_code=404, detail="Wallet nicht gefunden")

        transactions = await wallet_service.get_wallet_history(
            chain=wallet_data["chain"],
            address=wallet_data["address"]
        )

        # Pagination anwenden
        paginated_txs = transactions[offset:offset + limit]

        return WalletHistoryResponse(
            transactions=paginated_txs,
            total_count=len(transactions)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden der Historie: {str(e)}")

@router.get("/list", response_model=List[Dict[str, Any]])
async def list_wallets(current_user = Depends(get_current_user)):
    """Listet gespeicherte Wallets (Server-Persistenz)."""
    try:
        return await wallet_service.list_wallets()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Auflisten der Wallets: {str(e)}")

@router.get("/chains", response_model=List[str])
async def get_supported_chains(current_user = Depends(get_current_user)):
    """Gibt alle unterstützten Chains zurück"""
    return [
        "ethereum", "bitcoin", "solana", "polygon", "bsc",
        "avalanche", "arbitrum", "optimism", "fantom", "harmony"
    ]

@router.post("/{wallet_id}/analyze", response_model=Dict[str, Any])
async def analyze_wallet(
    wallet_id: str,
    current_user = Depends(get_current_user)
):
    """Führt eine KI-basierte Wallet-Analyse durch"""
    try:
        wallet_data = await wallet_service.load_wallet_data(wallet_id)
        if not wallet_data:
            raise HTTPException(status_code=404, detail="Wallet nicht gefunden")

        # Umfassende Wallet-Analyse
        balance = await wallet_service.get_balance(
            chain=wallet_data["chain"],
            address=wallet_data["address"]
        )

        history = await wallet_service.get_wallet_history(
            chain=wallet_data["chain"],
            address=wallet_data["address"]
        )

        # KI-Agent für detaillierte Analyse
        analysis = await wallet_service.ai_agent.analyze_wallet_comprehensive(
            chain=wallet_data["chain"],
            address=wallet_data["address"],
            balance=balance,
            transaction_history=history[:100]  # Letzte 100 TXs
        )

        return {
            "wallet_id": wallet_id,
            "analysis": analysis,
            "recommendations": analysis.get("recommendations", []),
            "risk_level": analysis.get("risk_level", "unknown"),
            "timestamp": asyncio.get_event_loop().time()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler bei der Analyse: {str(e)}")

@router.get("/{wallet_id}/export")
async def export_wallet(
    wallet_id: str,
    format: str = "json",
    current_user = Depends(get_current_user)
):
    """Exportiert Wallet-Daten"""
    try:
        wallet_data = await wallet_service.load_wallet_data(wallet_id)
        if not wallet_data:
            raise HTTPException(status_code=404, detail="Wallet nicht gefunden")

        if format == "json":
            return wallet_data
        elif format == "csv":
            # CSV-Export implementieren
            import csv
            import io

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=wallet_data.keys())
            writer.writeheader()
            writer.writerow(wallet_data)

            return {"data": output.getvalue(), "format": "csv"}
        else:
            raise HTTPException(status_code=400, detail="Nicht unterstütztes Format")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Export: {str(e)}")
