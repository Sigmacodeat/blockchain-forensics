"""
Custom Ledgers API
==================

TRM Labs Mai 2025 Feature: Custom Ledgers für Bulk Transfer Data.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from app.services.custom_ledgers import (
    custom_ledgers_service,
    LedgerType,
    TransferDirection,
)
from app.auth.dependencies import get_current_user_optional, require_plan

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateLedgerRequest(BaseModel):
    """Request für Ledger-Erstellung"""
    name: str = Field(..., min_length=1, max_length=200)
    ledger_type: LedgerType
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AddTransferRequest(BaseModel):
    """Request für Transfer hinzufügen"""
    from_address: str
    to_address: str
    amount: float
    timestamp: str
    currency: str = "USD"
    chain_id: str = "ethereum"
    direction: TransferDirection = TransferDirection.OUTBOUND
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


@router.post(
    "/ledgers",
    summary="Create Custom Ledger",
    description="Erstelle Custom Ledger für Bulk Transfer Data (Subpoena Returns, Exchange Exports)",
    dependencies=[Depends(require_plan("plus"))],
)
async def create_ledger(
    request: CreateLedgerRequest,
    current_user = Depends(get_current_user_optional),
):
    """Erstelle Custom Ledger"""
    try:
        ledger = await custom_ledgers_service.create_ledger(
            name=request.name,
            ledger_type=request.ledger_type,
            description=request.description,
            metadata=request.metadata,
        )
        
        return {
            "success": True,
            "ledger": ledger.to_dict(),
            "message": f"Ledger '{request.name}' created",
        }
        
    except Exception as e:
        logger.error(f"Failed to create ledger: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/ledgers/{ledger_id}/upload-csv",
    summary="Upload CSV Bulk Data",
    description="Upload CSV mit Bulk Transfer Data (bis zu 10M Transfers, 500MB)",
    dependencies=[Depends(require_plan("plus"))],
)
async def upload_csv(
    ledger_id: str,
    file: UploadFile = File(...),
    mapping: Optional[Dict[str, str]] = None,
    current_user = Depends(get_current_user_optional),
):
    """Upload CSV"""
    try:
        # Read file
        content = await file.read()
        
        # Check size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > custom_ledgers_service.MAX_CSV_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {size_mb:.1f}MB (max {custom_ledgers_service.MAX_CSV_FILE_SIZE_MB}MB)",
            )
        
        # Decode
        csv_content = content.decode('utf-8')
        
        # Upload
        ledger = await custom_ledgers_service.upload_csv(
            ledger_id=ledger_id,
            csv_content=csv_content,
            mapping=mapping,
        )
        
        return {
            "success": True,
            "ledger": ledger.to_dict(),
            "message": f"Uploaded {ledger.total_transfers} transfers",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/ledgers/{ledger_id}/transfers",
    summary="Add Single Transfer",
    description="Füge einzelnen Transfer zu Ledger hinzu",
    dependencies=[Depends(require_plan("plus"))],
)
async def add_transfer(
    ledger_id: str,
    request: AddTransferRequest,
    current_user = Depends(get_current_user_optional),
):
    """Füge Transfer hinzu"""
    try:
        ledger = await custom_ledgers_service.add_transfer(
            ledger_id=ledger_id,
            transfer={
                "from_address": request.from_address,
                "to_address": request.to_address,
                "amount": request.amount,
                "timestamp": request.timestamp,
                "currency": request.currency,
                "chain_id": request.chain_id,
                "direction": request.direction,
                "metadata": request.metadata,
                "notes": request.notes,
            },
        )
        
        return {
            "success": True,
            "ledger": ledger.to_dict(),
            "message": "Transfer added",
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add transfer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ledgers/{ledger_id}",
    summary="Get Ledger",
    description="Hole Ledger Details",
    dependencies=[Depends(require_plan("plus"))],
)
async def get_ledger(
    ledger_id: str,
    current_user = Depends(get_current_user_optional),
):
    """Hole Ledger"""
    try:
        ledger = await custom_ledgers_service.get_ledger(ledger_id)
        
        if not ledger:
            raise HTTPException(status_code=404, detail="Ledger not found")
        
        return {
            "success": True,
            "ledger": ledger.to_dict(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ledger: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ledgers",
    summary="List Ledgers",
    description="Liste alle Custom Ledgers",
    dependencies=[Depends(require_plan("plus"))],
)
async def list_ledgers(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user = Depends(get_current_user_optional),
):
    """Liste Ledgers"""
    try:
        ledgers = await custom_ledgers_service.list_ledgers(limit=limit, offset=offset)
        
        return {
            "success": True,
            "total": len(ledgers),
            "ledgers": [l.to_dict() for l in ledgers],
        }
        
    except Exception as e:
        logger.error(f"Failed to list ledgers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ledgers/{ledger_id}/transfers",
    summary="Get Transfers",
    description="Hole Transfers aus Ledger mit Filtering",
    dependencies=[Depends(require_plan("plus"))],
)
async def get_transfers(
    ledger_id: str,
    limit: int = Query(default=100, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    chain_id: Optional[str] = None,
    direction: Optional[TransferDirection] = None,
    current_user = Depends(get_current_user_optional),
):
    """Hole Transfers mit Filtering"""
    try:
        # Build filters
        filters = {}
        if min_amount is not None:
            filters["min_amount"] = min_amount
        if max_amount is not None:
            filters["max_amount"] = max_amount
        if chain_id:
            filters["chain_id"] = chain_id
        if direction:
            filters["direction"] = direction
        
        transfers = await custom_ledgers_service.get_transfers(
            ledger_id=ledger_id,
            limit=limit,
            offset=offset,
            filters=filters if filters else None,
        )
        
        return {
            "success": True,
            "total": len(transfers),
            "transfers": [t.to_dict() for t in transfers],
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get transfers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ledgers/{ledger_id}/analyze",
    summary="Analyze Ledger",
    description="Generiere Insights für Ledger (Top Counterparties, Patterns, Risk)",
    dependencies=[Depends(require_plan("plus"))],
)
async def analyze_ledger(
    ledger_id: str,
    current_user = Depends(get_current_user_optional),
):
    """Analysiere Ledger"""
    try:
        analysis = await custom_ledgers_service.analyze_ledger(ledger_id)
        
        return {
            "success": True,
            "analysis": analysis,
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ledger analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/ledgers/{ledger_id}",
    summary="Delete Ledger",
    description="Lösche Custom Ledger",
    dependencies=[Depends(require_plan("plus"))],
)
async def delete_ledger(
    ledger_id: str,
    current_user = Depends(get_current_user_optional),
):
    """Lösche Ledger"""
    try:
        success = await custom_ledgers_service.delete_ledger(ledger_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Ledger not found")
        
        return {
            "success": True,
            "message": "Ledger deleted",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete ledger: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
