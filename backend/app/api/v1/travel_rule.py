"""
Travel Rule API Routes
======================

API endpoints for Travel Rule Protocol (TRP) compliance.
Implements IVMS101 message handling for VASP communications.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.travel_rule_service import travel_rule_service
try:
    from app.compliance.travel_rule.adapters import travel_rule_manager
except ImportError:
    # Fallback if adapters not available
    travel_rule_manager = None
from app.auth.dependencies import get_current_user_strict, get_current_user
import os

logger = logging.getLogger(__name__)
router = APIRouter()
_TEST_MODE = bool(os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TEST_MODE") == "1")
_user_dep = get_current_user if _TEST_MODE else get_current_user_strict


# ===== Request/Response Models =====

class PrepareTravelRuleRequest(BaseModel):
    """Request to prepare a Travel Rule message"""
    ivms101_payload: Dict[str, Any] = Field(..., description="IVMS101 message payload")
    originator_vasp_id: str = Field(..., description="VASP ID of originator")
    beneficiary_vasp_id: str = Field(..., description="VASP ID of beneficiary")


class PrepareTravelRuleResponse(BaseModel):
    success: bool
    prepared_payload: Dict[str, Any] | None = None
    errors: list[str] = []


class SendTravelRuleRequest(BaseModel):
    message_id: str
    ivms101_payload: Dict[str, Any]


class TravelRuleStatusResponse(BaseModel):
    message_id: str
    status: str
    created_at: str | None = None
    sent_at: str | None = None
    ivms101_payload: Dict[str, Any]


# ===== Routes =====

@router.post("/prepare-legacy", response_model=PrepareTravelRuleResponse, status_code=status.HTTP_200_OK)
def prepare_travel_rule(req: PrepareTravelRuleRequest, user=Depends(_user_dep)):
    """Validate IVMS101 payload and prepare Travel Rule message."""
    try:
        result = travel_rule_service.prepare_message(
            ivms101_payload=req.ivms101_payload,
            originator_vasp_id=req.originator_vasp_id,
            beneficiary_vasp_id=req.beneficiary_vasp_id,
        )
        return result
    except Exception as e:
        logger.error(f"prepare_travel_rule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send", status_code=status.HTTP_200_OK)
def send_travel_rule(req: SendTravelRuleRequest, user=Depends(_user_dep)):
    """Send a prepared Travel Rule message."""
    try:
        result = travel_rule_service.send_message(
            message_id=req.message_id,
            ivms101_payload=req.ivms101_payload,
        )
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "send_failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"send_travel_rule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}", response_model=TravelRuleStatusResponse)
def get_travel_rule_status(message_id: str, user=Depends(_user_dep)):
    """Get status/details for a Travel Rule message."""
    try:
        result = travel_rule_service.get_message_status(message_id)
        if not result:
            raise HTTPException(status_code=404, detail="message_not_found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_travel_rule_status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SendTravelRuleRequest(BaseModel):
    """Request to send a prepared Travel Rule message"""
    message_id: str = Field(..., description="Unique message ID from preparation")
    ivms101_payload: Dict[str, Any] = Field(..., description="IVMS101 message payload")


class TravelRuleResponse(BaseModel):
    """Standard Travel Rule response"""
    success: bool
    message_id: str | None = None
    status: str | None = None
    errors: list[str] = []
    data: Dict[str, Any] | None = None
    prepared_payload: Dict[str, Any] | None = None


# ===== API Endpoints =====

@router.post("/prepare", response_model=TravelRuleResponse)
async def prepare_travel_rule_message(
    request: PrepareTravelRuleRequest,
    current_user: dict = Depends(_user_dep)
) -> TravelRuleResponse:
    """
    Prepare a Travel Rule message for sending.

    Validates IVMS101 payload and returns a preparation DTO that can be signed
    and sent to the beneficiary VASP.

    **Request Body:**
    - ivms101_payload: Complete IVMS101 message structure
    - originator_vasp_id: Your VASP's identifier
    - beneficiary_vasp_id: Beneficiary VASP's identifier

    **Returns:**
    - prepared_payload: DTO ready for signing and transmission
    - validation errors if payload is invalid
    """
    try:
        # Delegate to service to validate and prepare
        res = travel_rule_service.prepare_message(
            ivms101_payload=request.ivms101_payload,
            originator_vasp_id=request.originator_vasp_id,
            beneficiary_vasp_id=request.beneficiary_vasp_id,
        )
        if res.get("success"):
            dto = res.get("prepared_payload") or {}
            return TravelRuleResponse(
                success=True,
                message_id=dto.get("message_id"),
                data=dto,
                prepared_payload=dto,
            )
        return TravelRuleResponse(success=False, errors=res.get("errors", ["validation_failed"]), prepared_payload=None)
    except Exception as e:
        logger.error(f"Error preparing Travel Rule message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error preparing Travel Rule message"
        )

# ==== Body-based validation endpoint ====
class ValidateTravelRuleRequest(BaseModel):
    ivms101_payload: Dict[str, Any] = Field(..., description="IVMS101 message payload")


@router.post("/validate", response_model=TravelRuleResponse)
async def validate_travel_rule_body(
    request: ValidateTravelRuleRequest,
    current_user: dict = Depends(_user_dep)
) -> TravelRuleResponse:
    """
    Validate IVMS101 payload from request body.

    Returns a standardized response with validation errors.
    """
    try:
        errors = travel_rule_service._validate_ivms101(request.ivms101_payload)
        if errors:
            return TravelRuleResponse(success=False, errors=errors)
        return TravelRuleResponse(success=True, data={"valid": True})
    except Exception as e:
        logger.error(f"Error validating Travel Rule payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error validating payload"
        )
        if res.get("success"):
            dto = res.get("prepared_payload") or {}
            return TravelRuleResponse(
                success=True,
                message_id=dto.get("message_id"),
                data=dto,
            )
        return TravelRuleResponse(success=False, errors=res.get("errors", ["validation_failed"]))

    except Exception as e:
        logger.error(f"Error preparing Travel Rule message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error preparing Travel Rule message"
        )


@router.post("/send", response_model=TravelRuleResponse)
async def send_travel_rule_message(
    request: SendTravelRuleRequest,
    current_user: dict = Depends(_user_dep)
) -> TravelRuleResponse:
    """
    Send a prepared Travel Rule message.

    Persists the message, updates status to 'sent', and triggers audit events.
    The message should be cryptographically signed before sending.

    **Request Body:**
    - message_id: Unique ID from preparation step
    - ivms101_payload: Signed IVMS101 payload

    **Returns:**
    - Confirmation of successful sending
    """
    try:
        res = travel_rule_service.send_message(
            message_id=request.message_id,
            ivms101_payload=request.ivms101_payload,
        )
        if res.get("success"):
            return TravelRuleResponse(
                success=True,
                message_id=res.get("message_id", request.message_id),
                status=res.get("status", "sent"),
            )
        return TravelRuleResponse(success=False, errors=[res.get("error", "send_failed")])

    except Exception as e:
        logger.error(f"Error sending Travel Rule message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error sending Travel Rule message"
        )


@router.get("/messages/{message_id}", response_model=TravelRuleResponse)
async def get_travel_rule_message(
    message_id: str,
    current_user: dict = Depends(_user_dep)
) -> TravelRuleResponse:
    """
    Get status and details of a Travel Rule message.

    Returns redacted message information for compliance monitoring.

    **Path Parameters:**
    - message_id: Unique message identifier

    **Returns:**
    - Message status, timestamps, and redacted payload
    """
    try:
        res = travel_rule_service.get_message_status(message_id)
        if not res:
            return TravelRuleResponse(success=False, errors=["not_found"], message_id=message_id)
        return TravelRuleResponse(
            success=True,
            message_id=message_id,
            status=res.get("status"),
            data=res,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Travel Rule message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error retrieving Travel Rule message"
        )


@router.get("/adapters", response_model=TravelRuleResponse)
async def list_travel_rule_adapters(
    current_user: dict = Depends(_user_dep)
) -> TravelRuleResponse:
    """List configured Travel Rule adapters"""
    try:
        adapters = {}
        try:
            for name, adapter in (travel_rule_manager.adapters or {}).items():  # type: ignore[attr-defined]
                cfg = getattr(adapter, "config", {}) or {}
                adapters[name] = {
                    "endpoint": cfg.get("endpoint"),
                    "vasp_code": cfg.get("vasp_code"),
                    "status": "configured" if cfg.get("endpoint") else "prepared"
                }
        except Exception:
            adapters = {}
        return TravelRuleResponse(success=True, data={"adapters": adapters, "total": len(adapters)})

    except Exception as e:
        logger.error(f"Error listing Travel Rule adapters: {e}")
        return TravelRuleResponse(
            success=False,
            errors=[str(e)]
        )


@router.get("/validate-ivms101")
async def validate_ivms101_payload(
    payload: str,
    current_user: dict = Depends(_user_dep)
):
    """
    Validate an IVMS101 payload structure.

    **Query Parameters:**
    - payload: IVMS101 payload as JSON

    **Returns:**
    - Validation results and errors
    """
    try:
        # Accept stringified JSON/dict from query param and parse
        import json, ast
        parsed: Dict[str, Any]
        try:
            parsed = json.loads(payload)
        except Exception:
            try:
                parsed = ast.literal_eval(payload)
            except Exception:
                parsed = {}

        from app.services.travel_rule_service import travel_rule_service as _svc
        errors = _svc._validate_ivms101(parsed)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "payload_structure": {
                "has_originator": "originator" in parsed,
                "has_beneficiary": "beneficiary" in parsed,
                "has_transaction": "transaction" in parsed
            }
        }

    except Exception as e:
        logger.error(f"Error validating IVMS101 payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error validating payload"
        )
