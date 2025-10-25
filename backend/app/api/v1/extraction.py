from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.extraction_service import ExtractionService

router = APIRouter()


class CodeExtractRequest(BaseModel):
    code: str = Field(..., description="Source code to extract information from")
    language: Optional[str] = Field(None, description="Programming language, e.g., python, solidity")
    task: Optional[str] = Field(None, description="Optional extraction task hint")


class TextExtractRequest(BaseModel):
    text: str = Field(..., description="Free-form text to extract structured data from")
    task: Optional[str] = Field(None, description="Optional extraction task hint")
    schema_: Optional[Dict[str, Any]] = Field(
        None,
        alias="schema",
        description="Optional JSON schema guiding extraction",
    )


@router.post("/extraction/code")
async def post_extraction_code(req: CodeExtractRequest) -> Dict[str, Any]:
    try:
        service = ExtractionService()
        resp = service.extract_from_code(req.code, language=req.language, task=req.task)
        if isinstance(resp, dict):
            resp.setdefault("ok", True)
            resp.setdefault("mode", "code")
            if req.language is not None:
                resp["language"] = req.language
        return resp
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/extraction/text")
async def post_extraction_text(req: TextExtractRequest) -> Dict[str, Any]:
    try:
        service = ExtractionService()
        return service.extract_from_text(req.text, schema=req.schema_, task=req.task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
