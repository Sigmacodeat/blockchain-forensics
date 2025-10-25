"""
Institutional Verification API
===============================

REST API endpoints for institutional verification workflow.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile, File
from fastapi import status

from app.auth.dependencies import get_current_user_strict, require_roles
from app.auth.models import UserRole
from app.services.institutional_verification_service import institutional_verification_service

logger = logging.getLogger(__name__)

router = APIRouter()

ERROR_STATUS_MAP = {
    "invalid_organization_type": status.HTTP_400_BAD_REQUEST,
    "duplicate_request": status.HTTP_409_CONFLICT,
    "integrity_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "creation_failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "missing_document_type": status.HTTP_400_BAD_REQUEST,
    "empty_file": status.HTTP_400_BAD_REQUEST,
    "invalid_document_type": status.HTTP_400_BAD_REQUEST,
    "file_too_large": status.HTTP_400_BAD_REQUEST,
    "not_found": status.HTTP_404_NOT_FOUND,
    "invalid_status": status.HTTP_400_BAD_REQUEST,
    "upload_failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "status_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "retrieval_failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "invalid_status_filter": status.HTTP_400_BAD_REQUEST,
    "list_failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "invalid_action": status.HTTP_400_BAD_REQUEST,
    "review_failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def _ensure_success(result: dict) -> dict:
    """Raise HTTPException for unsuccessful service responses."""
    if result.get("success"):
        return result

    message = result.get("error", "Unknown error")
    code = result.get("code")
    status_code = ERROR_STATUS_MAP.get(code, status.HTTP_400_BAD_REQUEST)
    raise HTTPException(status_code=status_code, detail=message)


@router.post("/request", response_model=dict)
async def request_institutional_verification(
    organization_type: str = Form(..., description="Type of organization"),
    organization_name: Optional[str] = Form(None, description="Name of organization"),
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Request institutional verification for current user.

    Organization types: police, detective, lawyer, government, exchange, other
    """
    try:
        result = await institutional_verification_service.create_verification_request(
            user_id=current_user["user_id"],
            organization_type=organization_type,
            organization_name=organization_name,
        )
        return _ensure_success(result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error requesting institutional verification: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to submit verification request")


@router.post("/{verification_id}/upload", response_model=dict)
async def upload_verification_document(
    verification_id: int,
    document_type: str = Form(..., description="Type of document"),
    file: UploadFile = File(..., description="Document file"),
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Upload document for verification request.
    """
    try:
        file_content = await file.read()
        result = await institutional_verification_service.upload_verification_document(
            verification_id=verification_id,
            file_data=file_content,
            filename=file.filename,
            document_type=document_type,
            user_id=current_user["user_id"],
        )
        return _ensure_success(result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error uploading verification document: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to upload verification document")


@router.get("/status", response_model=dict)
async def get_verification_status(
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Get current user's verification status.
    """
    try:
        result = await institutional_verification_service.get_verification_status(
            user_id=current_user["user_id"]
        )
        return _ensure_success(result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error getting verification status: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch verification status")


@router.get("/{verification_id}", response_model=dict)
async def get_verification_request(
    verification_id: int,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Get specific verification request details.
    Users can only access their own requests.
    """
    try:
        result = await institutional_verification_service.get_verification_request(
            verification_id=verification_id,
            user_id=current_user["user_id"]
        )
        return _ensure_success(result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error getting verification request: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to load verification request")


@router.get("/", response_model=dict)
async def list_verification_requests(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_roles([UserRole.ADMIN, UserRole.AUDITOR]))
):
    """
    List all verification requests (admin only).
    """
    try:
        result = await institutional_verification_service.list_verification_requests(
            status=status,
            limit=limit,
            offset=offset
        )
        return _ensure_success(result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error listing verification requests: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list verification requests")


@router.post("/{verification_id}/review", response_model=dict)
async def review_verification_request(
    verification_id: int,
    action: str = Form(..., description="'approve' or 'reject'"),
    admin_notes: Optional[str] = Form(None, description="Admin notes"),
    rejection_reason: Optional[str] = Form(None, description="Rejection reason (required for reject)"),
    current_user: dict = Depends(require_roles([UserRole.ADMIN, UserRole.AUDITOR]))
):
    """
    Admin review of verification request.
    """
    try:
        if action == "reject" and not rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason required for reject action")

        result = await institutional_verification_service.review_verification_request(
            verification_id=verification_id,
            admin_user_id=current_user["user_id"],
            action=action,
            admin_notes=admin_notes,
            rejection_reason=rejection_reason,
        )
        return _ensure_success(result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error reviewing verification request: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to review verification request")


@router.get("/{verification_id}/download", response_model=dict)
async def download_verification_document(
    verification_id: int,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Get download URL for verification document.
    """
    try:
        result = await institutional_verification_service.get_verification_request(
            verification_id=verification_id,
            user_id=current_user["user_id"]
        )
        verification = _ensure_success(result)["verification"]

        document = verification.get("document") or {}
        download_url = document.get("url")
        filename = document.get("filename")

        if not download_url or not filename:
            raise HTTPException(status_code=404, detail="No document available")

        return {
            "success": True,
            "download_url": download_url,
            "filename": filename,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error getting verification document download: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve document download link")
