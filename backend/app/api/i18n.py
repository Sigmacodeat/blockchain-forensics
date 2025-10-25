"""
Internationalisierung API Endpunkte für Blockchain-Forensik-Anwendung

Bietet REST-API für Sprach-Management und Übersetzungen.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio

from app.services.i18n_service import translation_manager, i18n_middleware, t, get_current_language
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/i18n", tags=["i18n"])

# Pydantic Models
class TranslationRequest(BaseModel):
    key: str = Field(..., description="Übersetzungsschlüssel")
    language: Optional[str] = Field(None, description="Zielsprache (optional)")
    params: Optional[Dict[str, Any]] = Field(None, description="Parameter für Interpolation")

class AddTranslationRequest(BaseModel):
    language: str = Field(..., description="Sprachcode")
    key: str = Field(..., description="Übersetzungsschlüssel")
    value: str = Field(..., description="Übersetzungswert")

class LanguageRequest(BaseModel):
    language: str = Field(..., description="Sprachcode")

# API Endpunkte

@router.get("/languages", response_model=List[Dict[str, str]])
async def get_supported_languages():
    """Holt alle unterstützten Sprachen"""
    try:
        return translation_manager.get_supported_languages()

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sprachen Laden fehlgeschlagen: {str(e)}")

@router.post("/translate", response_model=str)
async def translate_text(
    request: TranslationRequest,
    req: Request,
    current_user = Depends(get_current_user)
):
    """Übersetzt einen Text in die angegebene Sprache"""
    try:
        # Sprache aus Request ermitteln wenn nicht angegeben
        if not request.language:
            request.language = get_current_language(req)

        # Parameter für Interpolation vorbereiten
        params = request.params or {}

        translation = translation_manager.translate(
            key=request.key,
            language=request.language,
            **params
        )

        return translation

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Übersetzung fehlgeschlagen: {str(e)}")

@router.get("/current-language", response_model=str)
async def get_current_language_endpoint(request: Request):
    """Holt die aktuelle Sprache des Benutzers"""
    try:
        return get_current_language(request)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sprache Ermittlung fehlgeschlagen: {str(e)}")

@router.post("/set-language")
async def set_user_language(
    request: LanguageRequest,
    response: Response,
):
    """Setzt die Sprache für den Benutzer"""
    try:
        if request.language not in translation_manager.supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Sprache '{request.language}' wird nicht unterstützt"
            )

        # Sprache in Cookie speichern
        response.set_cookie(
            key="user_language",
            value=request.language,
            max_age=30*24*60*60,  # 30 Tage
            httponly=True,
            secure=True,
            samesite="lax"
        )

        return {"message": f"Sprache auf {request.language} gesetzt", "language": request.language}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sprache Setzen fehlgeschlagen: {str(e)}")

@router.get("/translations/{language}", response_model=Dict[str, Any])
async def get_all_translations(
    language: str,
    current_user = Depends(get_current_user)
):
    """Holt alle Übersetzungen für eine Sprache"""
    try:
        if language not in translation_manager.supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Sprache '{language}' wird nicht unterstützt"
            )

        return translation_manager.translations.get(language, {})

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Übersetzungen Laden fehlgeschlagen: {str(e)}")

@router.post("/translations", response_model=Dict[str, str])
async def add_translation(
    request: AddTranslationRequest,
    current_user = Depends(get_current_user)
):
    """Fügt eine neue Übersetzung hinzu (nur für Admins)"""
    try:
        # Prüfen ob Benutzer Admin-Rechte hat (vereinfacht)
        # In einer echten Anwendung würde hier eine echte Berechtigungsprüfung stehen

        translation_manager.add_translation(
            language=request.language,
            key=request.key,
            value=request.value
        )

        return {
            "message": f"Übersetzung hinzugefügt",
            "language": request.language,
            "key": request.key,
            "value": request.value
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Übersetzung Hinzufügen fehlgeschlagen: {str(e)}")

@router.get("/detect-language", response_model=str)
async def detect_language(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Erkennt die Sprache basierend auf Accept-Language header"""
    try:
        accept_language = request.headers.get('accept-language')
        user_agent = request.headers.get('user-agent')

        detected_language = translation_manager.detect_language(accept_language, user_agent)

        return detected_language

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sprache Erkennung fehlgeschlagen: {str(e)}")

@router.get("/stats", response_model=Dict[str, Any])
async def get_i18n_stats(current_user = Depends(get_current_user)):
    """Holt Statistiken über Übersetzungen"""
    try:
        stats = {
            "supported_languages": len(translation_manager.supported_languages),
            "languages": translation_manager.get_supported_languages(),
            "default_language": translation_manager.default_language,
            "total_translations": sum(
                len(translations) if isinstance(translations, dict) else 0
                for translations in translation_manager.translations.values()
            ),
            "translations_per_language": {
                lang: _count_nested_keys(translations)
                for lang, translations in translation_manager.translations.items()
            }
        }

        return stats

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"i18n Statistiken fehlgeschlagen: {str(e)}")

def _count_nested_keys(obj: Any) -> int:
    """Zählt verschachtelte Schlüssel in einem Übersetzungs-Objekt"""
    if isinstance(obj, dict):
        return sum(_count_nested_keys(v) for v in obj.values())
    elif isinstance(obj, list):
        return sum(_count_nested_keys(item) for item in obj)
    else:
        return 1

# Middleware-Integration
@router.get("/test-middleware")
async def test_i18n_middleware(request: Request):
    """Test-Endpunkt für i18n Middleware"""
    language = get_current_language(request)
    test_translation = translation_manager.translate("common.loading", language)

    return {
        "detected_language": language,
        "test_translation": test_translation,
        "supported_languages": translation_manager.get_supported_languages()
    }
