from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from app.auth.dependencies import get_current_user_strict
from app.db.redis_client import redis_client
from datetime import datetime
import uuid
import json

router = APIRouter()

@router.get("/me/export")
async def export_my_data(
    request: Request,
    user: dict = Depends(get_current_user_strict),
    ttl_done: int = Query(7 * 24 * 3600, ge=3600, le=30 * 24 * 3600),
    max_attempts: int = Query(5, ge=1, le=20),
) -> Dict[str, Any]:
    """
    Initiates a data export for the authenticated user (DSR Export).
    Returns a ticket id which can be used to track completion.
    Implementation note: This is a minimal placeholder that stores a ticket in Redis.
    """
    await redis_client._ensure_connected()  # type: ignore[attr-defined]
    client = getattr(redis_client, "client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Export service unavailable")
    ticket = str(uuid.uuid4())
    key = f"dsr:export:{ticket}"
    payload = {
        "user_id": str(user["user_id"]),
        "request_id": ticket,
        "requested_at": datetime.utcnow().isoformat(),
        "status": "queued",
        "type": "export",
        "ttl_done": int(ttl_done),
        "max_attempts": int(max_attempts),
    }
    await client.setex(key, 7 * 24 * 3600, json.dumps(payload))
    return {"ticket": ticket, "status": "queued", "type": "export"}

@router.delete("/me")
async def delete_my_data(
    request: Request,
    user: dict = Depends(get_current_user_strict),
    ttl_done: int = Query(7 * 24 * 3600, ge=3600, le=30 * 24 * 3600),
    max_attempts: int = Query(5, ge=1, le=20),
) -> Dict[str, Any]:
    """
    Initiates deletion for the authenticated user's personal data (DSR Delete).
    Minimal placeholder: emits a deletion ticket into Redis to be processed by a retention job.
    """
    await redis_client._ensure_connected()  # type: ignore[attr-defined]
    client = getattr(redis_client, "client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Deletion service unavailable")
    ticket = str(uuid.uuid4())
    key = f"dsr:delete:{ticket}"
    payload = {
        "user_id": str(user["user_id"]),
        "request_id": ticket,
        "requested_at": datetime.utcnow().isoformat(),
        "status": "queued",
        "type": "delete",
        "ttl_done": int(ttl_done),
        "max_attempts": int(max_attempts),
    }
    await client.setex(key, 7 * 24 * 3600, json.dumps(payload))
    return {"ticket": ticket, "status": "queued", "type": "delete"}


@router.get("/tickets/{ticket_type}/{ticket_id}")
async def get_dsr_ticket_status(
    ticket_type: str,
    ticket_id: str,
    user: dict = Depends(get_current_user_strict),
) -> Dict[str, Any]:
    """
    Liefert den aktuellen Status eines DSR-Tickets (export/delete) zurück.
    Nur Eigentümer (user_id) erhalten Einblick in das eigene Ticket.
    """
    if ticket_type not in {"export", "delete"}:
        raise HTTPException(status_code=400, detail="invalid ticket type")
    await redis_client._ensure_connected()  # type: ignore[attr-defined]
    client = getattr(redis_client, "client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Ticket service unavailable")
    key = f"dsr:{ticket_type}:{ticket_id}"
    val = await client.get(key)
    if not val:
        raise HTTPException(status_code=404, detail="ticket not found")
    try:
        if isinstance(val, bytes):
            val = val.decode("utf-8", errors="ignore")
        data = json.loads(val)
    except Exception:
        raise HTTPException(status_code=500, detail="invalid ticket payload")
    # Zugriffsprüfung: nur eigener user_id
    if str(data.get("user_id")) != str(user["user_id"]):
        raise HTTPException(status_code=403, detail="forbidden")
    return data


@router.get("/tickets")
async def list_my_dsr_tickets(
    user: dict = Depends(get_current_user_strict),
    cursor: int = Query(0, ge=0),
    count: int = Query(100, ge=10, le=500),
) -> Dict[str, Any]:
    """
    Listet DSR-Tickets (export/delete) des eingeloggten Nutzers auf.
    Cursor-basiertes Paging über Redis SCAN. Es werden nur eigene Tickets gezeigt.
    """
    await redis_client._ensure_connected()  # type: ignore[attr-defined]
    client = getattr(redis_client, "client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Ticket service unavailable")
    items: list[dict] = []
    next_cursor = cursor
    # zwei Patterns nacheinander scannen
    for pattern in ("dsr:export:*", "dsr:delete:*"):
        scan_cursor = cursor
        scan_done = False
        while not scan_done and len(items) < count:
            scan_cursor, keys = await client.scan(cursor=scan_cursor, match=pattern, count=count)
            for k in keys or []:
                val = await client.get(k)
                if not val:
                    continue
                try:
                    if isinstance(val, bytes):
                        val = val.decode("utf-8", errors="ignore")
                    data = json.loads(val)
                    if str(data.get("user_id")) == str(user["user_id"]):
                        data.setdefault("ticket", k.split(":")[-1])
                        data.setdefault("type", k.split(":")[1])
                        items.append(data)
                except Exception:
                    # ignoriere kaputte Einträge
                    continue
            if scan_cursor == 0:
                scan_done = True
        # track den höchsten cursor für Antwort
        next_cursor = max(next_cursor, scan_cursor)
        if len(items) >= count:
            break
    return {"cursor": next_cursor, "items": items}


@router.post("/tickets/{ticket_type}/{ticket_id}/requeue")
async def requeue_dsr_ticket(
    ticket_type: str,
    ticket_id: str,
    user: dict = Depends(get_current_user_strict),
) -> Dict[str, Any]:
    """
    Setzt ein fehlgeschlagenes Ticket zurück (status->queued, attempts=0, entfernt last_error/failed_at).
    Nur der Eigentümer darf requeue ausführen.
    """
    if ticket_type not in {"export", "delete"}:
        raise HTTPException(status_code=400, detail="invalid ticket type")
    await redis_client._ensure_connected()  # type: ignore[attr-defined]
    client = getattr(redis_client, "client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Ticket service unavailable")
    key = f"dsr:{ticket_type}:{ticket_id}"
    val = await client.get(key)
    if not val:
        raise HTTPException(status_code=404, detail="ticket not found")
    if isinstance(val, bytes):
        val = val.decode("utf-8", errors="ignore")
    try:
        data = json.loads(val)
    except Exception:
        raise HTTPException(status_code=500, detail="invalid ticket payload")
    if str(data.get("user_id")) != str(user["user_id"]):
        raise HTTPException(status_code=403, detail="forbidden")
    # nur failed Tickets zurücksetzen; queued/running ignorieren
    if data.get("status") == "failed":
        data["status"] = "queued"
        data["attempts"] = 0
        data.pop("last_error", None)
        data.pop("failed_at", None)
        await client.set(key, json.dumps(data))
    return {"ticket": ticket_id, "type": ticket_type, "status": data.get("status", "queued")}
