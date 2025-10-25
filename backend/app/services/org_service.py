from __future__ import annotations
import json
import uuid
import logging
from typing import Dict, List, Optional

from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)


class OrgService:
    """
    Lightweight, Redis-backed organization/membership service.
    - Org metadata: org:{org_id}:meta -> { id, name, owner_id, created_at }
    - Members: org:{org_id}:members -> Redis Set of user_ids
    - User orgs: user:{user_id}:orgs -> Redis Set of org_ids
    """

    ORG_META = "org:{org_id}:meta"
    ORG_MEMBERS = "org:{org_id}:members"
    USER_ORGS = "user:{user_id}:orgs"

    def __init__(self) -> None:
        # In-memory fallback stores used when Redis is unavailable (e.g., TEST_MODE)
        self._mem_meta: dict[str, dict[str, str]] = {}
        self._mem_members: dict[str, set[str]] = {}
        self._mem_user_orgs: dict[str, set[str]] = {}

    async def create_org(self, name: str, owner_id: str, created_at_iso: str) -> Dict[str, str]:
        await redis_client._ensure_connected()  # type: ignore[attr-defined]
        client = getattr(redis_client, "client", None)
        org_id = str(uuid.uuid4())
        meta = {
            "id": org_id,
            "name": name,
            "owner_id": owner_id,
            "created_at": created_at_iso,
        }
        if client is None:
            # In-memory fallback
            self._mem_meta[org_id] = meta
            self._mem_members.setdefault(org_id, set()).add(owner_id)
            self._mem_user_orgs.setdefault(owner_id, set()).add(org_id)
            return meta
        meta_key = self.ORG_META.format(org_id=org_id)
        members_key = self.ORG_MEMBERS.format(org_id=org_id)
        user_orgs_key = self.USER_ORGS.format(user_id=owner_id)
        pipe = client.pipeline()
        pipe.set(meta_key, json.dumps(meta))
        pipe.sadd(members_key, owner_id)
        pipe.sadd(user_orgs_key, org_id)
        await pipe.execute()
        return meta

    async def get_org(self, org_id: str) -> Optional[Dict[str, str]]:
        await redis_client._ensure_connected()  # type: ignore[attr-defined]
        client = getattr(redis_client, "client", None)
        if client is None:
            return self._mem_meta.get(org_id)
        raw = await client.get(self.ORG_META.format(org_id=org_id))
        return json.loads(raw) if raw else None

    async def list_orgs_for_user(self, user_id: str) -> List[Dict[str, str]]:
        await redis_client._ensure_connected()  # type: ignore[attr-defined]
        client = getattr(redis_client, "client", None)
        if client is None:
            ids = list(self._mem_user_orgs.get(user_id, set()))
            return [self._mem_meta[oid] for oid in ids if oid in self._mem_meta]
        org_ids = await client.smembers(self.USER_ORGS.format(user_id=user_id))
        if not org_ids:
            return []
        out: List[Dict[str, str]] = []
        # Fetch sequentially to support simple test doubles without pipeline.get
        for oid in org_ids:
            try:
                raw = await client.get(self.ORG_META.format(org_id=oid))
                if raw:
                    out.append(json.loads(raw))
            except Exception:
                continue
        return out

    async def add_member(self, org_id: str, requester_id: str, user_id: str) -> bool:
        """Add member; only owner can add."""
        await redis_client._ensure_connected()  # type: ignore[attr-defined]
        client = getattr(redis_client, "client", None)
        meta = await self.get_org(org_id)
        if not meta or meta.get("owner_id") != requester_id:
            return False
        if client is None:
            self._mem_members.setdefault(org_id, set()).add(user_id)
            self._mem_user_orgs.setdefault(user_id, set()).add(org_id)
            return True
        pipe = client.pipeline()
        pipe.sadd(self.ORG_MEMBERS.format(org_id=org_id), user_id)
        pipe.sadd(self.USER_ORGS.format(user_id=user_id), org_id)
        res = await pipe.execute()
        return bool(res)

    async def remove_member(self, org_id: str, requester_id: str, user_id: str) -> bool:
        """Remove member; only owner can remove. Owner cannot remove self if sole member."""
        await redis_client._ensure_connected()  # type: ignore[attr-defined]
        client = getattr(redis_client, "client", None)
        meta = await self.get_org(org_id)
        if not meta or meta.get("owner_id") != requester_id:
            return False
        if client is None:
            members = self._mem_members.get(org_id, set())
            if user_id == meta.get("owner_id") and (not members or len(members) <= 1):
                return False
            members.discard(user_id)
            self._mem_members[org_id] = members
            uorgs = self._mem_user_orgs.get(user_id, set())
            uorgs.discard(org_id)
            self._mem_user_orgs[user_id] = uorgs
            return True
        # Prevent removing owner if they are the only member
        members = await client.smembers(self.ORG_MEMBERS.format(org_id=org_id))
        if user_id == meta.get("owner_id") and (not members or (len(members) <= 1)):
            return False
        pipe = client.pipeline()
        pipe.srem(self.ORG_MEMBERS.format(org_id=org_id), user_id)
        pipe.srem(self.USER_ORGS.format(user_id=user_id), org_id)
        try:
            res = await pipe.execute()
        except Exception:
            return False
        # res is list of bools; consider success if any op succeeded
        return any(bool(r) for r in res)

    async def list_members(self, org_id: str) -> List[str]:
        await redis_client._ensure_connected()  # type: ignore[attr-defined]
        client = getattr(redis_client, "client", None)
        if client is None:
            return list(self._mem_members.get(org_id, set()))
        members = await client.smembers(self.ORG_MEMBERS.format(org_id=org_id))
        return list(members or [])


org_service = OrgService()
