"""
i18n API endpoints for language preference management.
"""
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class LanguagePreference(BaseModel):
    """Language preference payload"""
    language: str = Field(..., min_length=2, max_length=10, description="Language code (e.g., 'en', 'de', 'es')")


@router.post("/i18n/set-language")
async def set_language(
    language_pref: LanguagePreference,
    response: Response,
    request: Request
):
    """
    Set user's language preference.
    
    This endpoint accepts the user's preferred language and:
    1. Sets a cookie for server-side rendering
    2. Logs the preference (optional: can be stored in user profile)
    
    **Public endpoint** - no authentication required
    """
    lang = language_pref.language
    
    # Validate language code format (basic check)
    if not lang or len(lang) < 2:
        return {"status": "error", "message": "Invalid language code"}
    
    # Set cookie for server-side language preference (30 days)
    response.set_cookie(
        key="user_language",
        value=lang,
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=False,  # Allow JS access
        samesite="lax",
        path="/"
    )
    
    logger.info(f"Language preference set to: {lang}")
    
    # Optional: Store in user profile if authenticated
    # user_id = request.state.user.get("user_id") if hasattr(request.state, "user") else None
    # if user_id:
    #     await update_user_language(user_id, lang)
    
    return {
        "status": "ok",
        "language": lang,
        "message": f"Language preference set to {lang}"
    }


@router.get("/i18n/get-language")
async def get_language(request: Request):
    """
    Get user's current language preference.
    
    Checks (in order):
    1. Cookie
    2. Accept-Language header
    3. Default to 'en'
    
    **Public endpoint**
    """
    # Check cookie first
    lang_cookie = request.cookies.get("user_language")
    if lang_cookie:
        return {"language": lang_cookie, "source": "cookie"}
    
    # Check Accept-Language header
    accept_lang = request.headers.get("Accept-Language", "")
    if accept_lang:
        # Parse first language from Accept-Language header
        # Format: "en-US,en;q=0.9,de;q=0.8"
        primary = accept_lang.split(",")[0].split(";")[0].strip()
        if primary:
            # Extract just the language code (en-US -> en)
            lang_code = primary.split("-")[0].lower()
            return {"language": lang_code, "source": "accept-language"}
    
    # Default
    return {"language": "en", "source": "default"}
