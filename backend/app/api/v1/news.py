from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from typing import Optional
import os

from app.services import news_service
from app.config import settings

router = APIRouter()


@router.get("/")
async def list_news(
    q: Optional[str] = Query(None, description="Freitextsuche in Titel/Zusammenfassung"),
    tag: Optional[str] = Query(None, description="Tag-Filter (z.B. aml, sanctions, mixers)"),
    source: Optional[str] = Query(None, description="Quellenfilter"),
    limit: int = Query(50, ge=1, le=200),
    lang: Optional[str] = Query(None, description="Zielsprache (ISO, z.B. de, fr). Standard: DEFAULT_LANGUAGE")
):
    target_lang = lang or os.getenv("DEFAULT_LANGUAGE", getattr(settings, "DEFAULT_LANGUAGE", "en"))
    res = await news_service.query_news(
        lang=target_lang,
        q=q,
        tag=tag,
        source=source,
        limit=limit,
    )
    return JSONResponse(res)


@router.post("/refresh")
async def refresh_news():
    try:
        res = await news_service.run_once()
        return {"status": "ok", **res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sitemap")
async def news_sitemap():
    base_url = os.getenv("FRONTEND_URL", getattr(settings, "FRONTEND_URL", "http://localhost:5173"))
    xml = news_service.generate_news_sitemap(base_url=base_url, max_items=50)
    return Response(content=xml, media_type="application/xml")


@router.get("/sitemap-news")
async def news_sitemap_news(lang: Optional[str] = None):
    base_url = os.getenv("FRONTEND_URL", getattr(settings, "FRONTEND_URL", "http://localhost:5173"))
    target_lang = lang or os.getenv("DEFAULT_LANGUAGE", getattr(settings, "DEFAULT_LANGUAGE", "en"))
    xml = news_service.generate_google_news_sitemap(base_url=base_url, lang=target_lang, max_items=50)
    return Response(content=xml, media_type="application/xml")


@router.get("/{item_id}")
async def get_news_item(item_id: str, lang: Optional[str] = Query(None, description="Zielsprache")):
    """Einzelnes News-Item (optional übersetzt) liefern."""
    item = news_service.get_news_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    target = lang or os.getenv("DEFAULT_LANGUAGE", getattr(settings, "DEFAULT_LANGUAGE", "en"))
    if target and target != os.getenv("DEFAULT_LANGUAGE", getattr(settings, "DEFAULT_LANGUAGE", "en")):
        # On-demand übersetzen (Titel/Teaser)
        from app.services.translation_service import translation_service
        title = item.get("title", "")
        summary = item.get("summary", "")
        item = dict(item)
        item["title_translated"] = await translation_service.translate(title, target, source_lang=os.getenv("DEFAULT_LANGUAGE", getattr(settings, "DEFAULT_LANGUAGE", "en")))
        item["summary_translated"] = await translation_service.translate(summary, target, source_lang=os.getenv("DEFAULT_LANGUAGE", getattr(settings, "DEFAULT_LANGUAGE", "en")))
        item["lang"] = target
    return JSONResponse(item)
