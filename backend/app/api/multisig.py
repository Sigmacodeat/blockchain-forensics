"""
Multi-Signature Wallet API Endpunkte

Bietet REST-API für Multi-Sig Wallet-Operationen.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Any

from app.services.multisig_wallet_service import multisig_manager
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/multisig", tags=["multisig"])

# Pydantic Models
class CreateMultiSigWalletRequest(BaseModel):
    wallet_id: str = Field(..., description="Eindeutige Wallet-ID")
    required_signatures: int = Field(2, ge=1, le=10, description="Erforderliche Anzahl Signaturen")
    name: str = Field("", description="Wallet-Name (optional)")

class AddSignerRequest(BaseModel):
    wallet_id: str
    public_key: str = Field(..., description="Public Key des Unterzeichners")
    name: str = Field(..., description="Name des Unterzeichners")
    role: str = Field("signer", description="Rolle des Unterzeichners")

class CreateMultiSigTransactionRequest(BaseModel):
    wallet_id: str
    to_address: str = Field(..., description="Empfängeradresse")
    amount: str = Field(..., description="Transaktionsbetrag")
    chain: str = Field(..., description="Blockchain-Netzwerk")
    description: str = Field("", description="Transaktionsbeschreibung")
    expires_in: int = Field(86400, description="Ablaufzeit in Sekunden")

class SignTransactionRequest(BaseModel):
    wallet_id: str
    tx_id: str = Field(..., description="Transaktions-ID")
    signer_public_key: str = Field(..., description="Public Key des Unterzeichners")
    signature: str = Field(..., description="Digitale Signatur")

# API Endpunkte

@router.post("/wallets", response_model=Dict[str, Any])
async def create_multisig_wallet(
    request: CreateMultiSigWalletRequest,
    current_user = Depends(get_current_user)
):
    """Erstellt eine neue Multi-Signature Wallet"""
    try:
        wallet = multisig_manager.create_wallet(
            wallet_id=request.wallet_id,
            required_signatures=request.required_signatures,
            name=request.name
        )

        return {
            "wallet_id": wallet.wallet_id,
            "required_signatures": wallet.required_signatures,
            "signer_count": len(wallet.signers),
            "created_at": wallet.created_at.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Erstellen der Multi-Sig Wallet: {str(e)}")

@router.get("/wallets", response_model=List[Dict[str, Any]])
async def list_multisig_wallets(current_user = Depends(get_current_user)):
    """Listet alle Multi-Signature Wallets auf"""
    try:
        return multisig_manager.list_wallets()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden der Wallets: {str(e)}")

@router.get("/wallets/{wallet_id}", response_model=Dict[str, Any])
async def get_multisig_wallet(
    wallet_id: str,
    current_user = Depends(get_current_user)
):
    """Holt Details einer Multi-Signature Wallet"""
    try:
        wallet = multisig_manager.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Multi-Sig Wallet nicht gefunden")

        return {
            "wallet_id": wallet.wallet_id,
            "required_signatures": wallet.required_signatures,
            "signers": wallet.signers,
            "pending_transactions": len(wallet.get_pending_transactions()),
            "completed_transactions": len(wallet.completed_transactions),
            "created_at": wallet.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden der Wallet: {str(e)}")

@router.post("/wallets/{wallet_id}/signers", response_model=Dict[str, Any])
async def add_signer(
    wallet_id: str,
    request: AddSignerRequest,
    current_user = Depends(get_current_user)
):
    """Fügt einen Unterzeichner hinzu"""
    try:
        wallet = multisig_manager.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Multi-Sig Wallet nicht gefunden")

        success = wallet.add_signer(
            public_key=request.public_key,
            name=request.name,
            role=request.role
        )

        if not success:
            raise HTTPException(status_code=400, detail="Unterzeichner konnte nicht hinzugefügt werden")

        # Änderungen speichern
        multisig_manager._save_wallet(wallet)

        return {
            "wallet_id": wallet_id,
            "signer_added": True,
            "signer_count": len(wallet.signers)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Hinzufügen des Unterzeichners: {str(e)}")

@router.delete("/wallets/{wallet_id}/signers/{public_key}", response_model=Dict[str, Any])
async def remove_signer(
    wallet_id: str,
    public_key: str,
    current_user = Depends(get_current_user)
):
    """Entfernt einen Unterzeichner"""
    try:
        wallet = multisig_manager.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Multi-Sig Wallet nicht gefunden")

        success = wallet.remove_signer(public_key)

        if not success:
            raise HTTPException(status_code=404, detail="Unterzeichner nicht gefunden")

        # Änderungen speichern
        multisig_manager._save_wallet(wallet)

        return {
            "wallet_id": wallet_id,
            "signer_removed": True,
            "signer_count": len(wallet.signers)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Entfernen des Unterzeichners: {str(e)}")

@router.post("/transactions", response_model=Dict[str, Any])
async def create_multisig_transaction(
    request: CreateMultiSigTransactionRequest,
    current_user = Depends(get_current_user)
):
    """Erstellt eine neue Multi-Signature Transaktion"""
    try:
        wallet = multisig_manager.get_wallet(request.wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Multi-Sig Wallet nicht gefunden")

        tx_id = await wallet.create_transaction(
            to_address=request.to_address,
            amount=request.amount,
            chain=request.chain,
            description=request.description,
            expires_in=request.expires_in
        )

        # Änderungen speichern
        multisig_manager._save_wallet(wallet)

        return {
            "tx_id": tx_id,
            "wallet_id": request.wallet_id,
            "status": "pending",
            "required_signatures": wallet.required_signatures
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Erstellen der Transaktion: {str(e)}")

@router.post("/transactions/{tx_id}/sign", response_model=Dict[str, Any])
async def sign_multisig_transaction(
    tx_id: str,
    request: SignTransactionRequest,
    current_user = Depends(get_current_user)
):
    """Unterzeichnet eine Multi-Signature Transaktion"""
    try:
        wallet = multisig_manager.get_wallet(request.wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Multi-Sig Wallet nicht gefunden")

        result = await wallet.sign_transaction(
            tx_id=tx_id,
            signer_public_key=request.signer_public_key,
            signature=request.signature
        )

        # Änderungen speichern
        multisig_manager._save_wallet(wallet)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Unterzeichnen: {str(e)}")

@router.get("/wallets/{wallet_id}/transactions/pending", response_model=List[Dict[str, Any]])
async def get_pending_transactions(
    wallet_id: str,
    current_user = Depends(get_current_user)
):
    """Holt alle ausstehenden Transaktionen einer Wallet"""
    try:
        wallet = multisig_manager.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Multi-Sig Wallet nicht gefunden")

        return wallet.get_pending_transactions()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden der Transaktionen: {str(e)}")

@router.get("/transactions/{tx_id}", response_model=Dict[str, Any])
async def get_transaction_status(
    tx_id: str,
    current_user = Depends(get_current_user)
):
    """Holt den Status einer spezifischen Transaktion"""
    try:
        # Suche in allen Wallets nach der Transaktion
        for wallet in multisig_manager.wallets.values():
            tx_status = wallet.get_transaction_status(tx_id)
            if tx_status:
                return tx_status

        raise HTTPException(status_code=404, detail="Transaktion nicht gefunden")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden der Transaktion: {str(e)}")

@router.get("/stats", response_model=Dict[str, Any])
async def get_multisig_stats(current_user = Depends(get_current_user)):
    """Holt Statistiken über alle Multi-Signature Wallets"""
    try:
        wallets = multisig_manager.list_wallets()

        total_wallets = len(wallets)
        total_pending_txs = sum(w["pending_txs"] for w in wallets)
        total_completed_txs = sum(w["completed_txs"] for w in wallets)

        return {
            "total_wallets": total_wallets,
            "total_pending_transactions": total_pending_txs,
            "total_completed_transactions": total_completed_txs,
            "avg_signers_per_wallet": sum(w["signer_count"] for w in wallets) / total_wallets if total_wallets > 0 else 0
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden der Statistiken: {str(e)}")
