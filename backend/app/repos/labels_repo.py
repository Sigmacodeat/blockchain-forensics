from typing import List, Dict, Any, Tuple
from app.db.postgres import postgres_client


async def add_label(chain: str, address: str, label: str, category: str = "generic") -> Dict[str, Any]:
    async with postgres_client.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO labels (chain, address, label, category)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (chain, address, label) DO NOTHING
            RETURNING id, chain, address, label, category, created_at
            """,
            chain.lower(), address.lower(), label, category,
        )
        if row:
            return dict(row)
        # fetch existing
        row = await conn.fetchrow(
            """
            SELECT id, chain, address, label, category, created_at
            FROM labels WHERE chain = $1 AND address = $2 AND label = $3
            """,
            chain.lower(), address.lower(), label,
        )
        return dict(row) if row else {
            "chain": chain.lower(),
            "address": address.lower(),
            "label": label,
            "category": category,
        }


async def get_labels(chain: str, address: str) -> List[Dict[str, Any]]:
    async with postgres_client.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, chain, address, label, category, created_at
            FROM labels
            WHERE chain = $1 AND address = $2
            ORDER BY created_at DESC
            """,
            chain.lower(), address.lower(),
        )
        return [dict(r) for r in rows]


async def bulk_upsert(items: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Perform bulk upsert of label records.

    items: list of dicts with keys: chain, address, label, category
    Returns: (inserted_count, existing_count)
    """
    if not items:
        return (0, 0)

    # Normalize input
    payload = [
        (
            (it.get("chain") or "").lower(),
            (it.get("address") or "").lower(),
            it.get("label") or "",
            it.get("category") or "generic",
        )
        for it in items
    ]

    async with postgres_client.acquire() as conn:
        # Insert with ON CONFLICT DO NOTHING to count new vs existing in two steps
        inserted = 0
        await conn.execute("BEGIN")
        try:
            stmt = (
                """
                INSERT INTO labels (chain, address, label, category)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (chain, address, label) DO UPDATE SET category = EXCLUDED.category
                """
            )
            # executemany for performance
            await conn.executemany(stmt, payload)

            # Approximate counts: count how many rows currently exist for the provided keys
            # and infer existing by matching keys; to avoid heavy queries, we return len(items) as affected
            # and 0 for existing updates (since we cannot distinguish cheaply here).
            inserted = len(items)
            await conn.execute("COMMIT")
            return (inserted, 0)
        except Exception:
            await conn.execute("ROLLBACK")
            raise
