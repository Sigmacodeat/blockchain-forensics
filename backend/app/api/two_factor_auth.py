"""
2FA API Endpunkte für Blockchain-Forensik-Anwendung

Bietet REST-API für Zwei-Faktor-Authentifizierung.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio

from app.services.two_factor_auth import two_fa_manager
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/2fa", tags=["2fa"])

# Pydantic Models
class Setup2FAResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]
    setup_complete: bool

class Verify2FARequest(BaseModel):
    token: str = Field(..., description="6-stelliger TOTP-Token")

class BackupCodeVerifyRequest(BaseModel):
    code: str = Field(..., description="Backup-Code")

# API Endpunkte

@router.post("/setup", response_model=Setup2FAResponse)
async def setup_2fa(
    account_name: str,
    current_user = Depends(get_current_user)
):
    """Richtet 2FA für den aktuellen Benutzer ein"""
    try:
        user_id = current_user.id
        result = two_fa_manager.setup_2fa_for_user(user_id, account_name)

        return Setup2FAResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"2FA-Setup fehlgeschlagen: {str(e)}")

@router.post("/verify-setup", response_model=Dict[str, bool])
async def verify_2fa_setup(
    request: Verify2FARequest,
    current_user = Depends(get_current_user)
):
    """Verifiziert die 2FA-Einrichtung"""
    try:
        user_id = current_user.id
        success = two_fa_manager.verify_2fa_setup(user_id, request.token)

        if success:
            # 2FA ist jetzt aktiviert
            return {"verified": True, "enabled": True}
        else:
            raise HTTPException(status_code=400, detail="Ungültiger Token")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"2FA-Verifikation fehlgeschlagen: {str(e)}")

@router.post("/verify-login", response_model=Dict[str, bool])
async def verify_2fa_login(
    request: Verify2FARequest,
    current_user = Depends(get_current_user)
):
    """Verifiziert 2FA-Token für Login"""
    try:
        user_id = current_user.id
        success = two_fa_manager.verify_2fa_login(user_id, request.token)

        if success:
            return {"verified": True}
        else:
            raise HTTPException(status_code=401, detail="Ungültiger 2FA-Token")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"2FA-Login-Verifikation fehlgeschlagen: {str(e)}")

@router.post("/verify-backup", response_model=Dict[str, bool])
async def verify_backup_code(
    request: BackupCodeVerifyRequest,
    current_user = Depends(get_current_user)
):
    """Verifiziert einen Backup-Code"""
    try:
        user_id = current_user.id
        success = two_fa_manager.verify_backup_code(user_id, request.code)

        if success:
            return {"verified": True}
        else:
            raise HTTPException(status_code=401, detail="Ungültiger Backup-Code")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Backup-Code-Verifikation fehlgeschlagen: {str(e)}")

@router.get("/status", response_model=Dict[str, Any])
async def get_2fa_status(current_user = Depends(get_current_user)):
    """Holt 2FA-Status für den aktuellen Benutzer"""
    try:
        user_id = current_user.id
        status = two_fa_manager.get_2fa_status(user_id)

        return status

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Laden des 2FA-Status: {str(e)}")

@router.delete("/disable")
async def disable_2fa(current_user = Depends(get_current_user)):
    """Deaktiviert 2FA für den aktuellen Benutzer"""
    try:
        user_id = current_user.id
        success = two_fa_manager.disable_2fa_for_user(user_id)

        if success:
            return {"message": "2FA erfolgreich deaktiviert"}
        else:
            raise HTTPException(status_code=400, detail="2FA konnte nicht deaktiviert werden")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Deaktivieren von 2FA: {str(e)}")

@router.get("/generate-backup-codes", response_model=List[str])
async def generate_new_backup_codes(current_user = Depends(get_current_user)):
    """Generiert neue Backup-Codes für 2FA"""
    try:
        user_id = current_user.id

        # Prüfen ob 2FA aktiviert ist
        if user_id not in two_fa_manager.user_secrets:
            raise HTTPException(status_code=400, detail="2FA ist nicht aktiviert")

        # Neue Backup-Codes generieren
        new_codes = []
        for _ in range(10):
            new_codes.append(secrets.token_hex(4).upper())

        # Alte Codes ersetzen
        two_fa_manager.backup_codes[user_id] = new_codes

        return new_codes

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Generieren neuer Backup-Codes: {str(e)}")

@router.get("/qr-code/{secret}")
async def get_qr_code_for_secret(
    secret: str,
    account_name: str,
    current_user = Depends(get_current_user)
):
    """Generiert QR-Code für einen gegebenen Secret (nur für Setup)"""
    try:
        # QR-Code generieren
        qr_code = two_fa_manager.two_fa.generate_qr_code(secret, account_name)

        return {
            "qr_code": base64.b64encode(qr_code).decode(),
            "secret": secret  # Nur zurückgeben wenn für Setup benötigt
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Generieren des QR-Codes: {str(e)}")

# Import für secrets
import secrets
import base64
