from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from typing import Literal, Optional
import json
from pathlib import Path
from app.auth.dependencies import require_admin
import time
import os
import tempfile
import hashlib
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Config Model
class ChatbotConfig(BaseModel):
    # Core Features
    enabled: bool = True
    showRobotIcon: bool = True
    showUnreadBadge: bool = True
    showQuickReplies: bool = True
    showProactiveMessages: bool = True
    showVoiceInput: bool = True
    
    # Advanced Features
    enableCryptoPayments: bool = True
    enableIntentDetection: bool = True
    enableSentimentAnalysis: bool = True
    enableOfflineMode: bool = True
    enableDragDrop: bool = True
    enableKeyboardShortcuts: bool = True
    
    # UI/UX
    enableDarkMode: bool = True
    enableMinimize: bool = True
    enableExport: bool = True
    enableShare: bool = True
    showWelcomeTeaser: bool = True
    
    # Timing
    proactiveMessageDelay: int = Field(5, ge=0, le=3600, description="Delay for proactive messages in seconds")
    welcomeTeaserDelay: int = Field(10, ge=0, le=3600, description="Delay for welcome teaser in seconds")
    autoScrollEnabled: bool = True
    
    # Limits
    maxMessages: int = Field(50, ge=1, le=500)
    maxFileSize: int = Field(10, ge=1, le=100)  # MB
    rateLimitPerMinute: int = Field(20, ge=1, le=600)
    
    # Appearance
    primaryColor: str = "#6366f1"
    position: Literal["bottom-right", "bottom-left", "top-right", "top-left"] = "bottom-right"
    buttonSize: Literal["small", "medium", "large"] = "medium"

    # Meta / Versioning
    schemaVersion: int = 1

# Storage path
CONFIG_FILE = Path("data/chatbot_config.json")
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

_CACHE_VALUE: Optional[ChatbotConfig] = None
_CACHE_TS: float = 0.0
_CACHE_TTL_SEC = 30.0

def _merge_defaults(data: dict) -> ChatbotConfig:
    defaults = ChatbotConfig()
    try:
        merged = {**defaults.model_dump(), **(data or {})}
    except Exception:
        merged = defaults.model_dump()
    return ChatbotConfig(**merged)

def load_config() -> ChatbotConfig:
    global _CACHE_VALUE, _CACHE_TS
    now = time.time()
    if _CACHE_VALUE is not None and (now - _CACHE_TS) < _CACHE_TTL_SEC:
        return _CACHE_VALUE
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            cfg = _merge_defaults(raw if isinstance(raw, dict) else {})
            _CACHE_VALUE, _CACHE_TS = cfg, now
            return cfg
        except Exception as e:
            logger.warning(f"Failed to load chatbot config, using defaults: {e}")
            cfg = ChatbotConfig()
            _CACHE_VALUE, _CACHE_TS = cfg, now
            return cfg
    cfg = ChatbotConfig()
    _CACHE_VALUE, _CACHE_TS = cfg, now
    return cfg

def save_config(config: ChatbotConfig):
    global _CACHE_VALUE, _CACHE_TS
    tmp_dir = CONFIG_FILE.parent
    data = json.dumps(config.model_dump(), indent=2)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=tmp_dir, delete=False, encoding='utf-8') as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        os.replace(tmp_path, CONFIG_FILE)
        logger.info("Chatbot config saved successfully")
    except Exception as e:
        logger.error(f"Failed to save chatbot config: {e}")
        raise
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception as e:
            logger.debug(f"Failed to cleanup temp file: {e}")
    _CACHE_VALUE, _CACHE_TS = config, time.time()

@router.get("/chatbot-config", response_model=ChatbotConfig)
async def get_chatbot_config(admin_user=Depends(require_admin)):
    """Get current chatbot configuration (Admin only)"""
    return load_config()

@router.post("/chatbot-config", response_model=ChatbotConfig)
async def update_chatbot_config(
    config: ChatbotConfig,
    admin_user=Depends(require_admin)
):
    """Update chatbot configuration (Admin only)"""
    try:
        save_config(config)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")

@router.post("/chatbot-config/reset")
async def reset_chatbot_config(admin_user=Depends(require_admin)):
    """Reset chatbot configuration to defaults (Admin only)"""
    default_config = ChatbotConfig()
    save_config(default_config)
    return {"message": "Config reset to defaults", "config": default_config}

# Public endpoint (no auth) for frontend to fetch config
@router.get("/chatbot-config/public", tags=["public"])
async def get_public_chatbot_config(request: Request):
    try:
        cfg = load_config()
        body = cfg.model_dump_json(indent=None, exclude_none=False)
        etag = 'W/"' + hashlib.sha256(body.encode("utf-8")).hexdigest()[:16] + '"'
        
        # Conditional ETag
        inm = request.headers.get("if-none-match")
        if inm == etag:
            resp = Response(status_code=304)
        else:
            resp = Response(content=body, media_type="application/json")
        
        # Cache headers
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = "public, max-age=30, must-revalidate"
        
        # Last-Modified based on file mtime (or now)
        try:
            mtime = CONFIG_FILE.stat().st_mtime if CONFIG_FILE.exists() else time.time()
        except Exception:
            mtime = time.time()
        resp.headers["Last-Modified"] = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        # Security headers (safe for public JSON)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Content-Security-Policy"] = "default-src 'none'"
        
        # CORS headers for public config
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        resp.headers["Access-Control-Max-Age"] = "86400"
        
        return resp
    except Exception as e:
        logger.error(f"Error serving public chatbot config: {e}")
        # Return default config on error
        default = ChatbotConfig()
        return Response(
            content=default.model_dump_json(),
            media_type="application/json",
            headers={
                "Cache-Control": "no-cache",
                "X-Content-Type-Options": "nosniff",
                "Access-Control-Allow-Origin": "*"
            }
        )
