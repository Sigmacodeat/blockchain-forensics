"""
WebSocket for NewsCase streams (slug-based)
Events delivered:
- news_case.snapshot: initial snapshot when connected
- news_case.status: periodic snapshot/status
- news_case.tx: newly detected transaction for any watched address
- news_case.kyt: KYT analysis result for a detected tx (best-effort)
"""
import asyncio
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.news_case_service import news_case_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websockets"])  # mounted under /api/v1


@router.websocket("/news-cases/{slug}")
async def news_case_websocket(websocket: WebSocket, slug: str):
    """
    WebSocket endpoint für NewsCase-Streams

    Client verbindet auf /api/v1/ws/news-cases/{slug}
    - erhält initial "news_case.snapshot"
    - danach kontinuierliche Events (status/tx/kyt)
    """
    await websocket.accept()
    logger.info("NewsCase WS connected: slug=%s", slug)
    q = None
    try:
        # Subscribe
        # optional backlog count from query (?backlog=50)
        try:
            params = websocket.query_params or {}
            backlog_param = params.get("backlog") if hasattr(params, "get") else None
            backlog_count = int(backlog_param) if backlog_param is not None else None
        except Exception:
            backlog_count = None
        q = await news_case_service.connect(slug, backlog_count=backlog_count)
        await websocket.send_json({"type": "news_case.subscribed", "slug": slug})

        async def _sender():
            while True:
                evt = await q.get()
                try:
                    await websocket.send_json(evt)
                except Exception as e:
                    logger.warning("send_json failed for %s: %s", slug, e)
                    raise

        async def _receiver():
            # optional ping handler; ignore other messages
            while True:
                try:
                    msg = await websocket.receive_text()
                    if msg == "ping":
                        await websocket.send_json({"type": "pong"})
                except Exception:
                    # Any receive error closes receiver loop
                    raise

        await asyncio.gather(_sender(), _receiver())

    except WebSocketDisconnect:
        logger.info("NewsCase WS disconnected: slug=%s", slug)
    except Exception as e:
        logger.error("NewsCase WS error (%s): %s", slug, e)
        try:
            await websocket.send_json({"type": "error", "detail": str(e)})
        except Exception:
            pass
    finally:
        if q is not None:
            try:
                news_case_service.unsubscribe(slug, q)
            except Exception:
                pass
