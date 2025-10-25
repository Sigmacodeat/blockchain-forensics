from typing import List, Dict, Any, Optional
from app.db.postgres import postgres_client


async def add_watch(chain: str, address: str, reason: str = "manual") -> Dict[str, Any]:
    async with postgres_client.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO compliance_watchlist (chain, address, reason)
            VALUES ($1, $2, $3)
            ON CONFLICT (chain, address) DO NOTHING
            RETURNING id, chain, address, reason, created_at
            """,
            chain.lower(), address.lower(), reason,
        )
        if row:
            return dict(row)
        # fetch existing on conflict
        row = await conn.fetchrow(
            """
            SELECT id, chain, address, reason, created_at
            FROM compliance_watchlist
            WHERE chain = $1 AND address = $2
            """,
            chain.lower(), address.lower(),
        )
        return dict(row) if row else {"chain": chain.lower(), "address": address.lower(), "reason": reason}


async def list_watch() -> List[Dict[str, Any]]:
    async with postgres_client.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, chain, address, reason, created_at
            FROM compliance_watchlist
            ORDER BY created_at DESC
            """,
        )
        return [dict(r) for r in rows]


async def list_watch_page(chain: Optional[str], address: Optional[str], limit: int, offset: int) -> Dict[str, Any]:
    """Return paginated items and total count"""
    async with postgres_client.acquire() as conn:
        where = []
        args: list[Any] = []
        if chain:
            where.append(f"chain = ${len(args)+1}")
            args.append(chain.lower())
        if address:
            where.append(f"address = ${len(args)+1}")
            args.append(address.lower())
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        # total
        q_total = f"SELECT COUNT(*) FROM compliance_watchlist{where_sql}"
        total = await conn.fetchval(q_total, *args)
        # items
        q_items = (
            f"SELECT id, chain, address, reason, created_at FROM compliance_watchlist{where_sql} "
            f"ORDER BY created_at DESC LIMIT ${len(args)+1} OFFSET ${len(args)+2}"
        )
        rows = await conn.fetch(q_items, *args, limit, offset)
        return {"items": [dict(r) for r in rows], "total": int(total)}


async def list_watch_filtered(chain: Optional[str] = None, address: Optional[str] = None) -> List[Dict[str, Any]]:
    async with postgres_client.acquire() as conn:
        if chain and address:
            rows = await conn.fetch(
                """
                SELECT id, chain, address, reason, created_at
                FROM compliance_watchlist
                WHERE chain = $1 AND address = $2
                ORDER BY created_at DESC
                """,
                chain.lower(), address.lower(),
            )
        elif chain:
            rows = await conn.fetch(
                """
                SELECT id, chain, address, reason, created_at
                FROM compliance_watchlist
                WHERE chain = $1
                ORDER BY created_at DESC
                """,
                chain.lower(),
            )
        elif address:
            rows = await conn.fetch(
                """
                SELECT id, chain, address, reason, created_at
                FROM compliance_watchlist
                WHERE address = $1
                ORDER BY created_at DESC
                """,
                address.lower(),
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, chain, address, reason, created_at
                FROM compliance_watchlist
                ORDER BY created_at DESC
                """,
            )
        return [dict(r) for r in rows]
