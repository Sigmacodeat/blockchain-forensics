"""
Chat Upload API for multimodal files (images, PDFs, etc.)
"""

import logging
import os
import time
import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.db.postgres import postgres_client

logger = logging.getLogger(__name__)
router = APIRouter()

# Configure upload settings
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "chat")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt'}

try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except Exception:
    # In some test or restricted environments, creation may fail; defer to runtime
    pass

class UploadResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    content_text: Optional[str] = None
    ocr_status: Optional[str] = None
    ocr_confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

async def _save_chat_attachment(session_id: str, message_id: int, filename: str, file_path: str, file_size: int, mime_type: str, content_text: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> int:
    """Save attachment metadata to database."""
    if not getattr(postgres_client, "pool", None):
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        result = await postgres_client.pool.fetchval("""
            INSERT INTO chat_attachments (session_id, message_id, filename, file_path, file_size, mime_type, content_text, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, session_id, message_id, filename, file_path, file_size, mime_type, content_text, metadata)
        return result
    except Exception as e:
        logger.error(f"Failed to save attachment: {e}")
        raise HTTPException(status_code=500, detail="Failed to save attachment")

from app.services.ocr_service import ocr_service

from app.services.cache_service import cache_ocr_result, get_cached_ocr_result
import hashlib

async def _extract_text_from_file(file_path: str, mime_type: str) -> Optional[str]:
    """Extract text from uploaded file using OCR service with caching."""
    try:
        # Generate file hash for caching
        file_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        file_hash_str = file_hash.hexdigest()

        # Check cache first
        cached_result = await get_cached_ocr_result(file_hash_str)
        if cached_result:
            logger.info(f"Using cached OCR result for {file_hash_str}")
            return cached_result.get("text")

        # Perform OCR
        result = await ocr_service.extract_text(file_path, mime_type)
        if result.get("status") == "success":
            # Cache the result
            await cache_ocr_result(file_hash_str, result)
            return result.get("text")
        else:
            logger.warning(f"OCR extraction failed: {result.get('status')}")
            return None
    except Exception as e:
        logger.error(f"OCR extraction error: {e}")
        return None

from app.services.queue_service import queue_service

# ... existing code ...

@router.post("/ai/chat/upload", response_model=UploadResponse)
async def upload_chat_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    message_id: int = Form(...),
    user: Dict = Depends(get_current_user)
) -> UploadResponse:
    """Upload a file for chat multimodal processing with async OCR."""

    start_time = time.time()

    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Generate unique filename
    unique_id = str(uuid.uuid4())
    safe_filename = f"{unique_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    # For immediate response, return basic info
    # OCR will be processed asynchronously
    metadata = {
        "ocr_status": "queued",
        "processing_time": time.time() - start_time
    }

    # Save metadata to database
    attachment_id = await _save_chat_attachment(
        session_id, message_id, file.filename, file_path, len(content), file.content_type or "", None, metadata
    )

    # Queue OCR processing for better performance
    await queue_service.enqueue("ocr_processing", {
        "file_path": file_path,
        "mime_type": file.content_type or "",
        "attachment_id": attachment_id
    })

    return UploadResponse(
        id=attachment_id,
        filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type or "",
        content_text="OCR processing queued - will be available shortly",
        ocr_status="queued",
        metadata=metadata
    )
