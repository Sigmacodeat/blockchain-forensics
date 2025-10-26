from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os

from app.auth.dependencies import require_admin
from app.services.social_publisher import social_publisher
from app.services.news_service import get_news_item
from app.services.social_content import generate_news_post, build_shortlink
from app.workers.social_scheduler import social_scheduler_worker

try:
    from app.ai_agents.agent import get_agent  # optional for auto-replies
except Exception:  # pragma: no cover
    get_agent = None  # type: ignore

router = APIRouter(prefix="/social")


class PostRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    channels: Optional[List[str]] = None
    telegram_chat_id: Optional[str] = None


@router.get("/health")
async def social_health() -> Dict[str, Any]:
    return {"ok": True, "channels": social_publisher.enabled_channels()}


@router.post("/post")
async def social_post(payload: PostRequest, user: dict = Depends(require_admin)) -> Dict[str, Any]:
    res = await social_publisher.post(
        payload.message,
        channels=payload.channels,
        extra={"telegram_chat_id": payload.telegram_chat_id} if payload.telegram_chat_id else None,
    )
    return res


class NewsPublishRequest(BaseModel):
    channels: Optional[List[str]] = None
    language: Optional[str] = None
    telegram_chat_id: Optional[str] = None


@router.get("/news/{item_id}/preview")
async def social_news_preview(item_id: str, lang: Optional[str] = Query(None), user: dict = Depends(require_admin)) -> Dict[str, Any]:
    item = get_news_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    post = generate_news_post(item, lang)
    # Provide a tracked shortlink for convenience
    short = build_shortlink(item.get("url") or item.get("url_norm") or "", platform="social", campaign="news")
    return {"ok": True, "message": post["message"], "hashtags": post["hashtags"], "shortlink": short}


@router.post("/news/{item_id}/publish")
async def social_news_publish(item_id: str, payload: NewsPublishRequest, user: dict = Depends(require_admin)) -> Dict[str, Any]:
    item = get_news_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    post = generate_news_post(item, payload.language)
    link = build_shortlink(item.get("url") or item.get("url_norm") or "", platform="social", campaign="news")
    # Append link into message for chat-type channels
    msg_with_link = f"{post['message']}\n\n{link['public_url']}"
    res = await social_publisher.post(
        msg_with_link,
        channels=payload.channels,
        extra={
            "telegram_chat_id": payload.telegram_chat_id,
            "link": link["public_url"],  # used by aggregator like Ayrshare
        },
    )
    return {"ok": True, "results": res.get("results"), "shortlink": link}


@router.post("/scheduler/run-once")
async def social_scheduler_run_once(user: dict = Depends(require_admin)) -> Dict[str, Any]:
    try:
        n = await social_scheduler_worker.run_once()
        return {"ok": True, "posted": n}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request) -> Dict[str, Any]:
    expected = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    if expected:
        provided = (
            request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            or request.headers.get("X-Telegram-Secret")
            or request.query_params.get("secret")
            or ""
        )
        if provided != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    message = (update or {}).get("message") or {}
    text = message.get("text") or ""
    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    if not chat_id:
        return {"ok": True}  # nothing to do

    reply_text = ""
    if text:
        agent = None
        try:
            agent = get_agent() if get_agent else None  # type: ignore
        except Exception:
            agent = None
        if agent is not None:
            try:
                res = await agent.investigate(text, chat_history=None, language=None, context="forensics")
                reply_text = res.get("response") or ""
            except Exception:
                reply_text = ""

    if not reply_text:
        reply_text = "Danke für deine Nachricht. Unser Forensics-Agent antwortet dir hier."

    await social_publisher.send_telegram(reply_text, chat_id=str(chat_id))
    return {"ok": True}
