import os
import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.db.postgres import postgres_client
from app.auth.dependencies import require_admin

router = APIRouter()

# Table bootstrap (idempotent)
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    prefix VARCHAR(32) NOT NULL,
    hash_sha256 CHAR(64) NOT NULL,
    scope TEXT NULL,
    tier VARCHAR(32) NOT NULL DEFAULT 'pro',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_api_keys_revoked ON api_keys (revoked);
CREATE UNIQUE INDEX IF NOT EXISTS ux_api_keys_prefix ON api_keys (prefix);
"""

async def _ensure_table():
    if os.getenv("TEST_MODE") == "1" or not getattr(postgres_client, "pool", None):
        return
    async with postgres_client.acquire() as conn:
        await conn.execute(CREATE_TABLE_SQL)


def _gen_key() -> Dict[str, str]:
    prefix = "sk_live_" + uuid4().hex[:8]
    secret = secrets.token_hex(24)
    value = f"{prefix}{secret}"
    h = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return {"prefix": prefix, "value": value, "hash": h}


class CreateKeyIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    scope: Optional[str] = Field(None, description="Optional scope label for limiting access")
    tier: str = Field("pro", pattern=r"^(free|pro|enterprise)$")


class KeyOut(BaseModel):
    id: str
    name: str
    prefix: str
    scope: Optional[str]
    tier: str
    created_at: datetime
    revoked: bool


class CreateKeyOut(KeyOut):
    api_key: str


@router.get("/keys", response_model=List[KeyOut])
async def list_keys(_user: dict = Depends(require_admin)) -> List[Dict[str, Any]]:
    await _ensure_table()
    if not getattr(postgres_client, "pool", None):
        return []
    async with postgres_client.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id::text, name, prefix, scope, tier, created_at, revoked
            FROM api_keys
            ORDER BY created_at DESC
        """)
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "prefix": r["prefix"],
            "scope": r["scope"],
            "tier": r["tier"],
            "created_at": r["created_at"],
            "revoked": r["revoked"],
        }
        for r in rows
    ]


@router.post("/keys", response_model=CreateKeyOut)
async def create_key(payload: CreateKeyIn, _user: dict = Depends(require_admin)) -> Dict[str, Any]:
    await _ensure_table()
    if not getattr(postgres_client, "pool", None):
        raise HTTPException(status_code=503, detail="DB unavailable")
    kid = uuid4()
    gen = _gen_key()
    async with postgres_client.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO api_keys (id, name, prefix, hash_sha256, scope, tier)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            str(kid), payload.name, gen["prefix"], gen["hash"], payload.scope, payload.tier,
        )
        row = await conn.fetchrow(
            """
            SELECT id::text, name, prefix, scope, tier, created_at, revoked
            FROM api_keys WHERE id = $1
            """,
            str(kid),
        )
    return {
        "id": row["id"],
        "name": row["name"],
        "prefix": row["prefix"],
        "scope": row["scope"],
        "tier": row["tier"],
        "created_at": row["created_at"],
        "revoked": row["revoked"],
        "api_key": gen["value"],  # only shown once
    }


@router.post("/keys/{key_id}/rotate", response_model=CreateKeyOut)
async def rotate_key(key_id: str, _user: dict = Depends(require_admin)) -> Dict[str, Any]:
    await _ensure_table()
    if not getattr(postgres_client, "pool", None):
        raise HTTPException(status_code=503, detail="DB unavailable")
    async with postgres_client.acquire() as conn:
        # Revoke old
        await conn.execute("UPDATE api_keys SET revoked = TRUE WHERE id::text = $1", key_id)
        # Create new
        kid = uuid4()
        gen = _gen_key()
        # Copy name/scope/tier from previous
        src = await conn.fetchrow("SELECT name, scope, tier FROM api_keys WHERE id::text = $1 LIMIT 1", key_id)
        if not src:
            raise HTTPException(status_code=404, detail="Key not found")
        await conn.execute(
            """
            INSERT INTO api_keys (id, name, prefix, hash_sha256, scope, tier)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            str(kid), src["name"], gen["prefix"], gen["hash"], src["scope"], src["tier"],
        )
        row = await conn.fetchrow(
            """
            SELECT id::text, name, prefix, scope, tier, created_at, revoked
            FROM api_keys WHERE id = $1
            """,
            str(kid),
        )
    return {
        "id": row["id"],
        "name": row["name"],
        "prefix": row["prefix"],
        "scope": row["scope"],
        "tier": row["tier"],
        "created_at": row["created_at"],
        "revoked": row["revoked"],
        "api_key": gen["value"],
    }


@router.delete("/keys/{key_id}")
async def revoke_key(key_id: str, _user: dict = Depends(require_admin)) -> Dict[str, Any]:
    await _ensure_table()
    if not getattr(postgres_client, "pool", None):
        raise HTTPException(status_code=503, detail="DB unavailable")
    async with postgres_client.acquire() as conn:
        res = await conn.execute("UPDATE api_keys SET revoked = TRUE WHERE id::text = $1", key_id)
    return {"status": "revoked", "id": key_id}
