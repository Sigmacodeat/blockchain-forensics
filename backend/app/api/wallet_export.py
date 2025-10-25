"""
Wallet Export/Import API Endpunkte

Erweitert die Wallet-API um Export- und Import-Funktionalitäten.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
from pathlib import Path

from app.services.wallet_export_service import wallet_export_service
from app.auth.dependencies import get_current_user_strict
from app.services.usage_service import check_and_consume_credits
from app.services.tenant_service import tenant_service

router = APIRouter(prefix="/api/v1/wallet", tags=["wallet"])

# Pydantic Models für Export/Import
class ExportWalletRequest(BaseModel):
    wallet_id: str = Field(..., description="ID der zu exportierenden Wallet")
    format: str = Field("json", description="Export-Format (json, csv, pdf)")
    include_history: bool = Field(True, description="Transaktionshistorie einschließen")
    include_analysis: bool = Field(True, description="KI-Analyse einschließen")

class ExportResponse(BaseModel):
    filename: str
    filepath: str
    format: str
    size: int
    rows: Optional[int] = None

class ImportWalletRequest(BaseModel):
    format: str = Field("auto", description="Import-Format (auto, json, csv)")

class ImportResponse(BaseModel):
    wallet_id: str
    chain: str
    address: str
    imported_transactions: int
    imported_analysis: bool

# API Endpunkte

@router.post("/export", response_model=ExportResponse)
async def export_wallet(
    request: ExportWalletRequest,
    current_user = Depends(get_current_user_strict)
):
    """Exportiert eine Wallet in verschiedenen Formaten"""
    try:
        # Credits: cost by format and options
        try:
            tenant_id = str(current_user["user_id"])
            plan_id = tenant_service.get_plan_id(tenant_id)
            base = {"json": 10, "csv": 15, "pdf": 30}.get(request.format.lower(), 10)
            extra = (5 if request.include_history else 0) + (10 if request.include_analysis else 0)
            amount = max(5, min(100, base + extra))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason=f"wallet_export_{request.format}")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Wallet-Export")
        except HTTPException:
            raise
        except Exception:
            # do not block on usage backend outage
            pass
        result = await wallet_export_service.export_wallet(
            wallet_id=request.wallet_id,
            format=request.format,
            include_history=request.include_history,
            include_analysis=request.include_analysis
        )

        return ExportResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Export fehlgeschlagen: {str(e)}")

@router.get("/{wallet_id}/exports", response_model=List[Dict[str, Any]])
async def get_wallet_exports(
    wallet_id: str,
    current_user = Depends(get_current_user_strict)
):
    """Holt die Export-Historie einer Wallet"""
    try:
        exports = await wallet_export_service.get_export_history(wallet_id)
        return exports

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden der Export-Historie: {str(e)}")

@router.get("/export/{filename}")
async def download_export(
    filename: str,
    current_user = Depends(get_current_user_strict)
):
    """Lädt eine Export-Datei herunter"""
    try:
        filepath = Path("exports/wallets") / filename

        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Export-Datei nicht gefunden")

        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Download: {str(e)}")

@router.post("/import", response_model=ImportResponse)
async def import_wallet(
    file: UploadFile = File(...),
    format: str = Form("auto"),
    current_user = Depends(get_current_user_strict)
):
    """Importiert eine Wallet aus einer Datei"""
    try:
        # Datei temporär speichern
        temp_path = Path(f"temp/import_{file.filename}")
        temp_path.parent.mkdir(exist_ok=True)

        content = await file.read()
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(content)

        # Wallet importieren
        result = await wallet_export_service.import_wallet(
            file_path=str(temp_path),
            format=format
        )

        # Temporäre Datei löschen
        temp_path.unlink(missing_ok=True)

        return ImportResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import fehlgeschlagen: {str(e)}")

@router.get("/formats")
async def get_supported_formats(current_user = Depends(get_current_user_strict)):
    """Gibt unterstützte Export/Import-Formate zurück"""
    return {
        "export_formats": ["json", "csv", "pdf"],
        "import_formats": ["json", "csv"],
        "auto_detection": True
    }

@router.delete("/export/{filename}")
async def delete_export(
    filename: str,
    current_user = Depends(get_current_user_strict)
):
    """Löscht eine Export-Datei"""
    try:
        filepath = Path("exports/wallets") / filename

        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Export-Datei nicht gefunden")

        filepath.unlink()

        return {"message": f"Export {filename} erfolgreich gelöscht"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Löschen: {str(e)}")

# Import für async file operations
try:
    import aiofiles
except ImportError:
    aiofiles = None

# Fallback für fehlende aiofiles
if not aiofiles:
    import json

    class MockAioFiles:
        @staticmethod
        async def open(file_path, mode):
            class MockFile:
                def __init__(self, path, mode):
                    self.path = path
                    self.mode = mode

                async def __aenter__(self):
                    return self

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

                async def write(self, data):
                    with open(self.path, self.mode) as f:
                        f.write(data)

                async def read(self):
                    with open(self.path, 'rb') as f:
                        return f.read()

            return MockFile(file_path, mode)

    aiofiles = MockAioFiles()
