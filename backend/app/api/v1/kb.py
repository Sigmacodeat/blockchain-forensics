from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import os
from app.kb.indexer import reindex_kb, reindex_kb_multiple, search_kb, semantic_search_kb

router = APIRouter()

class KbSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=256)
    limit: int = Field(5, ge=1, le=20)

class KbReindexMultiRequest(BaseModel):
    roots: List[str] = Field(..., min_length=1, description="Liste von Root-Verzeichnissen für die KB-Reindizierung")

@router.post("/kb/reindex")
async def kb_reindex(root: Optional[str] = None):
    root_path = root or os.path.abspath(os.path.join(os.getcwd(), "docs"))
    res = await reindex_kb(root_path)
    return {"status": "ok", **res}

@router.post("/kb/reindex-multi")
async def kb_reindex_multi(payload: KbReindexMultiRequest):
    # Normalisiere Pfade und filtere nicht existierende heraus
    roots = [os.path.abspath(p) for p in payload.roots]
    res = await reindex_kb_multiple(roots)
    return {"status": "ok", **res}

@router.post("/kb/search")
async def kb_search(payload: KbSearchRequest):
    rows = await search_kb(payload.query, limit=payload.limit)
    return {"results": rows}

@router.post("/kb/semantic_search")
async def kb_semantic_search(payload: KbSearchRequest):
    rows = await semantic_search_kb(payload.query, limit=payload.limit)
    return {"results": rows}
