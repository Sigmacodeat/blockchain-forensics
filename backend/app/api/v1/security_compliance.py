"""
Security & Compliance API
Endpoints für Audit-Trails, digitale Signaturen und Compliance-Management
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Body
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.security.security_enhancements import (
    kms,
    rbac,
    UserRole,
    EncryptionKey,
)
from app.services.retention_service import retention_service

from app.services.security_compliance import (
    audit_trail_service, digital_signature_service,
    compliance_service, security_service
)

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateKMSKeyRequest(BaseModel):
    key_id: str
    algorithm: Optional[str] = None


class RotateKMSKeyRequest(BaseModel):
    key_id: str


class RBACAssignRequest(BaseModel):
    user_id: str
    role: str


def _serialize_key_metadata(key: EncryptionKey) -> Dict[str, Any]:
    return {
        "key_id": key.key_id,
        "algorithm": key.algorithm,
        "created_at": key.created_at.isoformat(),
        "expires_at": key.expires_at.isoformat() if key.expires_at else None,
        "is_active": key.is_active,
        "usage_count": key.usage_count,
    }


@router.get("/audit-trail")
async def get_audit_trail(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action_filter: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum entries to return")
) -> List[Dict[str, Any]]:
    """
    Get audit trail entries with optional filtering

    **Query Parameters:**
    - start_date: Start date in ISO format
    - end_date: End date in ISO format
    - user_id: Filter by specific user
    - action_filter: Filter by action type
    - resource_type: Filter by resource type (case, evidence, alert, etc.)
    - limit: Maximum number of entries (1-1000)
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")

        entries = audit_trail_service.get_audit_trail(
            start_date=start_dt,
            end_date=end_dt,
            user_id=user_id,
            action_filter=action_filter,
            resource_type=resource_type,
            limit=limit
        )

        return entries

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/retention/estimate")
async def get_retention_cleanup_estimate() -> Dict[str, Any]:
    try:
        estimate = await retention_service.get_cleanup_estimate()
        if "error" in estimate:
            raise HTTPException(status_code=500, detail=estimate["error"])
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "estimate": estimate,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating retention cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/retention/run")
async def run_retention_cleanup() -> Dict[str, Any]:
    try:
        summary = await retention_service.cleanup_expired_data()
        if isinstance(summary, dict) and "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running retention cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-trail/integrity")
async def verify_audit_integrity(
    start_index: int = Query(0, ge=0),
    end_index: Optional[int] = Query(None, ge=0)
) -> Dict[str, Any]:
    """
    Verify audit trail integrity

    **Query Parameters:**
    - start_index: Starting index for verification (default: 0)
    - end_index: Ending index for verification (default: all)
    """
    try:
        result = audit_trail_service.verify_audit_integrity(start_index, end_index)
        return result

    except Exception as e:
        logger.error(f"Error verifying audit integrity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit-trail/export")
async def export_audit_trail(
    format: str = Query("json", pattern="^(json|csv)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
) -> Dict[str, str]:
    """
    Export audit trail for compliance purposes

    **Query Parameters:**
    - format: Export format (json or csv)
    - start_date: Start date in ISO format
    - end_date: End date in ISO format
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        exported_data = audit_trail_service.export_audit_trail(start_dt, end_dt, format)

        return {
            "format": format,
            "exported_at": datetime.utcnow().isoformat(),
            "data": exported_data
        }

    except Exception as e:
        logger.error(f"Error exporting audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sign")
async def sign_data(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    Digitally sign data using eIDAS-compliant signatures

    **Request Body:**
    ```json
    {
      "case_id": "case_123",
      "evidence_hash": "sha256_hash",
      "timestamp": "2023-01-01T12:00:00Z"
    }
    ```
    """
    try:
        signature = digital_signature_service.sign_data(data)

        return {
            "signature": signature,
            "signed_at": datetime.utcnow().isoformat(),
            "algorithm": "RSA-PSS-SHA256",
            "key_size": 4096
        }

    except Exception as e:
        logger.error(f"Error signing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_signature(
    data: Dict[str, Any] = Body(...),
    signature: str = Body(...)
) -> Dict[str, Any]:
    """
    Verify digital signature

    **Request Body:**
    ```json
    {
      "data": {"case_id": "case_123", "evidence_hash": "sha256_hash"},
      "signature": "hex_signature_string"
    }
    ```
    """
    try:
        is_valid = digital_signature_service.verify_signature(data, signature)

        return {
            "valid": is_valid,
            "verified_at": datetime.utcnow().isoformat(),
            "algorithm": "RSA-PSS-SHA256"
        }

    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public-key")
async def get_public_key() -> Dict[str, str]:
    """
    Get the public key for signature verification
    """
    try:
        public_key_pem = digital_signature_service.get_public_key_pem()

        return {
            "public_key": public_key_pem,
            "algorithm": "RSA-PSS-SHA256",
            "key_size": 4096,
            "format": "PEM"
        }

    except Exception as e:
        logger.error(f"Error getting public key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/report")
async def get_compliance_report() -> Dict[str, Any]:
    """
    Get comprehensive compliance report
    """
    try:
        report = compliance_service.generate_compliance_report()
        return report

    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/retention")
async def get_retention_status() -> Dict[str, Any]:
    """
    Get data retention compliance status
    """
    try:
        status = compliance_service.check_data_retention()
        return status

    except Exception as e:
        logger.error(f"Error checking retention status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/retention/estimate")
async def get_retention_cleanup_estimate() -> Dict[str, Any]:
    try:
        estimate = await retention_service.get_cleanup_estimate()
        if "error" in estimate:
            raise HTTPException(status_code=500, detail=estimate["error"])
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "estimate": estimate,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating retention cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/retention/run")
async def run_retention_cleanup() -> Dict[str, Any]:
    try:
        summary = await retention_service.cleanup_expired_data()
        if isinstance(summary, dict) and "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running retention cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/anonymize")
async def anonymize_data(
    data: Dict[str, Any] = Body(...),
    data_type: str = Body(...)
) -> Dict[str, Any]:
    """
    Anonymize personal data for GDPR compliance

    **Request Body:**
    ```json
    {
      "data": {"user_id": "123", "email": "user@example.com"},
      "data_type": "user_profiles"
    }
    ```
    """
    try:
        anonymized = compliance_service.anonymize_data(data, data_type)

        # Log anonymization action
        audit_trail_service.log_action(
            action="data_anonymized",
            resource_type=data_type,
            details={"original_fields": list(data.keys())},
            severity="info"
        )

        return {
            "original_data": data,
            "anonymized_data": anonymized,
            "anonymized_at": datetime.utcnow().isoformat(),
            "data_type": data_type
        }

    except Exception as e:
        logger.error(f"Error anonymizing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/deletion-schedule")
async def schedule_data_deletion(
    data_type: str = Body(...),
    data_ids: List[str] = Body(...)
) -> Dict[str, Any]:
    """
    Schedule data deletion for compliance

    **Request Body:**
    ```json
    {
      "data_type": "user_data",
      "data_ids": ["user_123", "user_456"]
    }
    ```
    """
    try:
        schedule = compliance_service.schedule_data_deletion(data_type, data_ids)

        # Log scheduling action
        audit_trail_service.log_action(
            action="data_deletion_scheduled",
            resource_type=data_type,
            resource_id=",".join(data_ids),
            details={"scheduled_for": schedule["scheduled_deletion"]},
            severity="info"
        )

        return schedule

    except Exception as e:
        logger.error(f"Error scheduling data deletion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/report")
async def get_security_report() -> Dict[str, Any]:
    """
    Get security status and incident report
    """
    try:
        report = security_service.generate_security_report()
        return report

    except Exception as e:
        logger.error(f"Error generating security report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security/kms/key")
async def create_kms_key(request: CreateKMSKeyRequest) -> Dict[str, Any]:
    try:
        if request.key_id in kms.keys:
            raise HTTPException(status_code=400, detail="Key ID already exists")
        key = await kms.create_key(request.key_id, request.algorithm or "AES256")
        return {
            "created_at": datetime.utcnow().isoformat(),
            "key": _serialize_key_metadata(key),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating KMS key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security/kms/rotate")
async def rotate_kms_key(request: RotateKMSKeyRequest) -> Dict[str, Any]:
    try:
        new_key = await kms.rotate_key(request.key_id)
        if not new_key:
            raise HTTPException(status_code=404, detail="Key not found")
        return {
            "rotated_at": datetime.utcnow().isoformat(),
            "key": _serialize_key_metadata(new_key),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rotating KMS key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/rbac/policies")
async def list_rbac_policies() -> Dict[str, Any]:
    try:
        policies = rbac.list_policies()
        return {
            "policies": policies,
            "retrieved_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error listing RBAC policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security/rbac/assign")
async def assign_rbac_role(request: RBACAssignRequest) -> Dict[str, Any]:
    try:
        try:
            role = UserRole(request.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")

        rbac.assign_role(request.user_id, role)
        permissions = rbac.get_user_permissions(request.user_id)
        return {
            "user_id": request.user_id,
            "role": role.value,
            "permissions": [perm.value for perm in permissions],
            "assigned_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning RBAC role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/rbac/{user_id}/permissions")
async def get_rbac_permissions(user_id: str) -> Dict[str, Any]:
    try:
        permissions = rbac.get_user_permissions(user_id)
        return {
            "user_id": user_id,
            "permissions": [perm.value for perm in permissions],
            "retrieved_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching RBAC permissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security/check-rate-limit")
async def check_rate_limit(
    identifier: str = Body(...),
    action: str = Body(...)
) -> Dict[str, Any]:
    """
    Check if action is rate limited

    **Request Body:**
    ```json
    {
      "identifier": "user_123",
      "action": "login"
    }
    ```
    """
    try:
        allowed = security_service.check_rate_limiting(identifier, action)

        return {
            "allowed": allowed,
            "identifier": identifier,
            "action": action,
            "checked_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security/report-suspicious")
async def report_suspicious_activity(
    request_data: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    Report suspicious activity for investigation

    **Request Body:**
    ```json
    {
      "ip_address": "192.168.1.1",
      "user_agent": "suspicious-browser",
      "path": "/admin/users",
      "user_role": "analyst"
    }
    ```
    """
    try:
        suspicious_indicators = security_service.detect_suspicious_activity(request_data)

        if suspicious_indicators:
            # Log suspicious activity
            audit_trail_service.log_action(
                action="suspicious_activity_detected",
                resource_type="security",
                details={
                    "indicators": suspicious_indicators,
                    "request_data": request_data
                },
                ip_address=request_data.get("ip_address"),
                severity="warning"
            )

        return {
            "suspicious": len(suspicious_indicators) > 0,
            "indicators": suspicious_indicators,
            "analyzed_at": datetime.utcnow().isoformat(),
            "request_summary": {
                "ip_address": request_data.get("ip_address"),
                "path": request_data.get("path"),
                "user_role": request_data.get("user_role")
            }
        }

    except Exception as e:
        logger.error(f"Error reporting suspicious activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/suspicious-activities")
async def get_suspicious_activities(
    limit: int = Query(50, ge=1, le=500)
) -> List[Dict[str, Any]]:
    """
    Get recent suspicious activities

    **Query Parameters:**
    - limit: Maximum number of activities to return (1-500)
    """
    try:
        activities = security_service.suspicious_activities[-limit:]
        return activities

    except Exception as e:
        logger.error(f"Error getting suspicious activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/gdpr/status")
async def get_gdpr_status() -> Dict[str, Any]:
    """
    Get GDPR compliance status and features
    """
    try:
        compliance_report = compliance_service.generate_compliance_report()

        gdpr_status = {
            "right_to_erasure": {
                "implemented": True,
                "description": "Users can request deletion of their personal data"
            },
            "data_portability": {
                "implemented": True,
                "description": "Users can export their data in machine-readable format"
            },
            "consent_management": {
                "implemented": True,
                "description": "Explicit consent tracking for data processing"
            },
            "breach_notification": {
                "implemented": True,
                "description": "72-hour breach notification procedure"
            },
            "data_minimization": {
                "implemented": True,
                "description": "Only necessary data is collected and processed"
            },
            "purpose_limitation": {
                "implemented": True,
                "description": "Data is only used for specified purposes"
            },
            "retention_schedule": compliance_service.data_retention_periods,
            "last_audit": compliance_report.get("generated_at"),
            "certifications": compliance_report.get("certifications", [])
        }

        return gdpr_status

    except Exception as e:
        logger.error(f"Error getting GDPR status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
