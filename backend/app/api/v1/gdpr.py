"""
GDPR Compliance API Endpoints
==============================

User data export, deletion, and privacy controls
"""

from fastapi import APIRouter, Depends, Response, HTTPException
from typing import Dict, Any
import logging

from app.services.gdpr_service import gdpr_service
from app.services.audit_service import audit_service
from app.api.dependencies import get_current_user_strict

router = APIRouter(prefix="/gdpr", tags=["GDPR"])
logger = logging.getLogger(__name__)


@router.post("/export", summary="Export My Data (GDPR Art. 20)")
async def export_my_data(
    current_user: dict = Depends(get_current_user_strict)
) -> Response:
    """
    Export all personal data (GDPR Right to Data Portability)
    
    Returns JSON file with:
    - Profile data
    - Cases
    - Traces
    - Chat history
    - Audit logs
    - Payments
    """
    try:
        user_id = current_user["user_id"]
        
        # Generate export
        data = await gdpr_service.export_user_data(user_id)
        
        # Audit log
        await audit_service.log_action(
            user_id=user_id,
            action="gdpr_export",
            resource_type="user_data",
            resource_id=user_id,
            details={"size_bytes": len(data)}
        )
        
        # Return as downloadable JSON
        return Response(
            content=data,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=gdpr_export_{user_id}.json"
            }
        )
    
    except Exception as e:
        logger.error(f"GDPR export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Export failed")


@router.post("/delete", summary="Delete My Data (GDPR Art. 17)")
async def delete_my_data(
    mode: str = "anonymize",  # 'delete' or 'anonymize'
    current_user: dict = Depends(get_current_user_strict)
) -> Dict[str, Any]:
    """
    Delete or anonymize personal data (GDPR Right to Erasure)
    
    Modes:
    - anonymize: Soft delete, preserves analytics (default)
    - delete: Hard delete, irreversible
    
    Note: Some data (audit logs) may be retained for legal compliance
    """
    try:
        user_id = current_user["user_id"]
        
        if mode not in ["delete", "anonymize"]:
            raise HTTPException(status_code=400, detail="Invalid mode")
        
        # Perform deletion/anonymization
        summary = await gdpr_service.delete_user_data(user_id, mode=mode)
        
        # Audit log (before account is disabled)
        await audit_service.log_action(
            user_id=user_id,
            action=f"gdpr_{mode}",
            resource_type="user_data",
            resource_id=user_id,
            details=summary
        )
        
        return {
            "success": True,
            "mode": mode,
            "summary": summary,
            "message": f"Data {mode}d successfully. Account will be disabled."
        }
    
    except Exception as e:
        logger.error(f"GDPR deletion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Deletion failed")


@router.get("/retention-status", summary="Data Retention Status")
async def get_retention_status(
    current_user: dict = Depends(get_current_user_strict)
) -> Dict[str, Any]:
    """
    Get data retention status
    
    Shows:
    - What data is stored
    - Retention periods
    - Expiration dates
    """
    try:
        user_id = current_user["user_id"]
        
        status = await gdpr_service.get_data_retention_status(user_id)
        
        return status
    
    except Exception as e:
        logger.error(f"Failed to get retention status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch status")


@router.get("/privacy-info", summary="Privacy Information")
async def get_privacy_info() -> Dict[str, Any]:
    """
    Get privacy policy information
    
    Returns:
    - Data categories we collect
    - Retention periods
    - User rights
    - Contact information
    """
    return {
        "data_categories": {
            "profile": {
                "description": "Email, name, plan, preferences",
                "retention": "Until account deletion",
                "legal_basis": "Contract performance"
            },
            "cases": {
                "description": "Investigation cases and evidence",
                "retention": "3 years after creation",
                "legal_basis": "Legitimate interest (fraud prevention)"
            },
            "traces": {
                "description": "Transaction traces and analysis",
                "retention": "1 year after creation",
                "legal_basis": "Contract performance"
            },
            "audit_logs": {
                "description": "Security and access logs",
                "retention": "2 years (compliance requirement)",
                "legal_basis": "Legal obligation"
            },
            "chat_history": {
                "description": "AI chat conversations",
                "retention": "90 days",
                "legal_basis": "Contract performance"
            }
        },
        "your_rights": {
            "access": "Request copy of your data (Art. 20)",
            "rectification": "Correct inaccurate data (Art. 16)",
            "erasure": "Delete or anonymize data (Art. 17)",
            "portability": "Receive data in machine-readable format (Art. 20)",
            "object": "Object to processing (Art. 21)",
            "restrict": "Restrict processing (Art. 18)"
        },
        "contact": {
            "email": "privacy@blockchain-forensics.ai",
            "dpo": "data-protection-officer@blockchain-forensics.ai"
        },
        "jurisdiction": "EU (GDPR), US (CCPA), UK (UK GDPR)"
    }
