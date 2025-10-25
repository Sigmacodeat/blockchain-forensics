from __future__ import annotations
from typing import List

from app.db.postgres import postgres_client


class SanctionsRepository:
    async def count_distinct_hits(self, addresses: List[str]) -> int:
        if not addresses:
            return 0
        # Normalize/dedupe lowercased addresses
        unique_addrs = list({addr.lower() for addr in addresses if isinstance(addr, str) and addr})
        if not unique_addrs:
            return 0
        if not postgres_client or not getattr(postgres_client, "pool", None):
            return 0
        async with postgres_client.acquire() as conn:
            res = await conn.fetchval(
                "SELECT COUNT(DISTINCT address) FROM sanctioned_addresses WHERE address = ANY($1::text[])",
                unique_addrs,
            )
            return int(res or 0)


sanctions_repository = SanctionsRepository()
