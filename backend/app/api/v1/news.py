from __future__ import annotations

import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.services import news_service

router = APIRouter(prefix="/news", tags=["News"])


@router.get("")
async def list_news(
    lang: Optional[str] = Query(None, description="Target language for translation"),
    q: Optional[str] = Query(None, description="Full-text query over title/summary"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    source: Optional[str] = Query(None, description="Filter by source key"),
    limit: int = Query(50, ge=1, le=200),
    since: Optional[str] = Query(None, description="ISO timestamp to filter newer items"),
) -> Dict[str, Any]:
    target_lang = lang or os.getenv("DEFAULT_LANGUAGE", "en")
    try:
        return await news_service.query_news(
            lang=target_lang,
            q=q,
            tag=tag,
            source=source,
            limit=limit,
            since_iso=since,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to list news: {e}")


@router.post("/refresh")
async def refresh_news() -> Dict[str, Any]:
    try:
        res = await news_service.run_once()
        return {"status": "ok", **res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to refresh news: {e}")


@router.get("/sitemap-news")
async def news_sitemap_news(lang: Optional[str] = None):
    base_url = os.getenv("FRONTEND_URL", os.getenv("PUBLIC_FRONTEND_URL", "http://localhost:5173"))
    target_lang = lang or os.getenv("DEFAULT_LANGUAGE", "en")
    xml = news_service.generate_google_news_sitemap(base_url=base_url, lang=target_lang, max_items=50)
    return Response(content=xml, media_type="application/xml")


@router.get("/sitemap")
async def news_sitemap():
    base_url = os.getenv("FRONTEND_URL", os.getenv("PUBLIC_FRONTEND_URL", "http://localhost:5173"))
    xml = news_service.generate_news_sitemap(base_url=base_url, max_items=200)
    return Response(content=xml, media_type="application/xml")


@router.get("/{item_id}")
async def get_news_item(item_id: str) -> Dict[str, Any]:
    it = news_service.get_news_item(item_id)
    if not it:
        raise HTTPException(status_code=404, detail="not found")
    return it
