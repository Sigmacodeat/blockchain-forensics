from fastapi import APIRouter, Query
from typing import List, Optional

router = APIRouter()

# Minimaler Comments-Endpoint, um 500er zu vermeiden und leere Liste zurückzugeben.
# Erwartete Query-Parameter: entityType, entityId, limit

@router.get("/comments")
async def list_comments(
    entityType: Optional[str] = Query(default=None),
    entityId: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100)
) -> List[dict]:
    # Placeholder-Implementierung: gibt immer eine leere Liste zurück.
    # Später kann hier DB-Zugriff / Geschäftslogik ergänzt werden.
    _ = (entityType, entityId, limit)
    return []
