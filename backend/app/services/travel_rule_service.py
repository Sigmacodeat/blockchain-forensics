from typing import Any
from datetime import datetime


def _is_iso_date(val: Any) -> bool:
    try:
        if not isinstance(val, str):
            return False
        datetime.strptime(val, "%Y-%m-%d")
        return True
    except Exception:
        return False


def _is_country_code(val: Any) -> bool:
    try:
        s = str(val)
        return len(s) == 2 and s.isalpha()
    except Exception:
        return False


def _is_currency_code(val: Any) -> bool:
    try:
        s = str(val)
        return len(s) == 3 and s.isalpha()
    except Exception:
        return False

"""
Travel Rule Service
==================

Business logic for Travel Rule Protocol (TRP) compliance.
Handles IVMS101 validation, message preparation, and sending.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.travel_rule import (
    TravelRuleMessage,
    TravelRuleStatusHistory,
    TravelRuleParty,
    TravelRuleStatus
)
try:
    from app.db.session import SessionLocal
except Exception:  # In Test-/Dev-Umgebungen kann dieses Modul fehlen; Tests patchen es per MagicMock
    SessionLocal = None  # type: ignore
from app.messaging.kafka_client import KafkaTopics
from app.services.signing import manifest_service

logger = logging.getLogger(__name__)


class TravelRuleService:
    """Service for Travel Rule operations"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def prepare_message(
        self,
        ivms101_payload: Dict[str, Any],
        originator_vasp_id: str,
        beneficiary_vasp_id: str
    ) -> Dict[str, Any]:
        """
        Prepare a Travel Rule message for sending.

        Validates IVMS101 payload and returns preparation DTO.

        Args:
            ivms101_payload: IVMS101 message payload
            originator_vasp_id: VASP ID of originator
            beneficiary_vasp_id: VASP ID of beneficiary

        Returns:
            Dict with message_id, prepared_payload, and validation_errors
        """
        try:
            # Validate IVMS101 structure
            validation_errors = self._validate_ivms101(ivms101_payload)

            if validation_errors:
                logger.warning(f"IVMS101 validation errors: {validation_errors}")
                return {
                    "success": False,
                    "errors": validation_errors,
                    "prepared_payload": None
                }

            # Screen sanctions/labels for originator/beneficiary addresses (best-effort)
            sanctions_hits: list[Dict[str, Any]] = []
            try:
                from app.enrichment.labels_service import labels_service  # lazy import
                originator_addr = (ivms101_payload.get("originator", {}) or {}).get("address")
                beneficiary_addr = (ivms101_payload.get("beneficiary", {}) or {}).get("address")
                if originator_addr:
                    is_s = awaitable_false(labels_service.is_sanctioned, originator_addr)
                    if is_s:
                        sanctions_hits.append({"party": "originator", "address": originator_addr})
                if beneficiary_addr:
                    is_s = awaitable_false(labels_service.is_sanctioned, beneficiary_addr)
                    if is_s:
                        sanctions_hits.append({"party": "beneficiary", "address": beneficiary_addr})
            except Exception:
                pass

            # Generate unique message ID
            message_id = str(uuid.uuid4())

            # Prepare response DTO
            prepared_dto = {
                "message_id": message_id,
                "ivms101_payload": ivms101_payload,
                "originator_vasp_id": originator_vasp_id,
                "beneficiary_vasp_id": beneficiary_vasp_id,
                "status": "prepared",
                "prepared_at": datetime.utcnow().isoformat(),
                "sanctions_hits": sanctions_hits,
            }

            # Audit compliance event (best-effort)
            try:
                from app.audit.logger import audit_logger, AuditEventType, AuditSeverity
                import asyncio as _asyncio
                # Only create task if event loop is running; otherwise skip in tests
                loop = None
                try:
                    loop = _asyncio.get_event_loop()
                except Exception:
                    loop = None
                if loop and loop.is_running():
                    _asyncio.create_task(
                        audit_logger.log_event(
                            event_type=AuditEventType.COMPLIANCE,
                            severity=AuditSeverity.MEDIUM if sanctions_hits else AuditSeverity.LOW,
                            user_id="system",
                            resource="travel_rule:prepare",
                            action="prepare",
                            details={"message_id": message_id, "sanctions_hits": sanctions_hits},
                            success=True,
                        )
                    )
            except Exception:
                pass

            return {
                "success": True,
                "prepared_payload": prepared_dto,
                "errors": []
            }

        except Exception as e:
            logger.error(f"Error preparing Travel Rule message: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "prepared_payload": None
            }

    def send_message(
        self,
        message_id: str,
        ivms101_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a prepared Travel Rule message.

        Persists message, updates status, and triggers audit events.

        Args:
            message_id: Unique message ID
            ivms101_payload: IVMS101 payload

        Returns:
            Dict with success status and message details
        """
        db = self.db_session or SessionLocal()

        try:
            # Extract key info for quick access
            originator = ivms101_payload.get("originator", {})
            beneficiary = ivms101_payload.get("beneficiary", {})
            transaction = ivms101_payload.get("transaction", {})

            # Create message record
            message = TravelRuleMessage(
                message_id=message_id,
                status=TravelRuleStatus.SENT,
                ivms101_payload=ivms101_payload,
                originator_vasp_id=originator.get("vasp", {}).get("vasp_id"),
                beneficiary_vasp_id=beneficiary.get("vasp", {}).get("vasp_id"),
                originator_address=originator.get("address"),
                beneficiary_address=beneficiary.get("address"),
                transaction_amount=str(transaction.get("amount")),
                transaction_currency=transaction.get("currency"),
                sent_at=datetime.utcnow()
            )

            db.add(message)
            db.flush()  # Get message.id

            # Add status history
            status_history = TravelRuleStatusHistory(
                message_id=message.id,
                old_status=None,
                new_status=TravelRuleStatus.SENT,
                changed_by="system",
                notes="Message prepared and sent"
            )
            db.add(status_history)

            # Extract and store party details
            self._store_party_details(db, message.id, ivms101_payload)

            db.commit()

            # Trigger audit event (masked for security)
            self._trigger_audit_event(message_id, "travel_rule_sent", {
                "originator_vasp": self._mask_vasp_id(originator.get("vasp", {}).get("vasp_id")),
                "beneficiary_vasp": self._mask_vasp_id(beneficiary.get("vasp", {}).get("vasp_id")),
                "amount": transaction.get("amount"),
                "currency": transaction.get("currency")
            })

            logger.info(f"Travel Rule message {message_id} sent successfully")

            # Audit compliance event (best-effort)
            try:
                from app.audit.logger import audit_logger, AuditEventType, AuditSeverity
                import asyncio as _asyncio
                loop = None
                try:
                    loop = _asyncio.get_event_loop()
                except Exception:
                    loop = None
                if loop and loop.is_running():
                    _asyncio.create_task(
                        audit_logger.log_event(
                            event_type=AuditEventType.COMPLIANCE,
                            severity=AuditSeverity.MEDIUM,
                            user_id="system",
                            resource="travel_rule:send",
                            action="send",
                            details={"message_id": message_id},
                            success=True,
                        )
                    )
            except Exception:
                pass

            return {
                "success": True,
                "message_id": message_id,
                "status": "sent"
            }

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error sending Travel Rule message {message_id}: {e}")
            return {
                "success": False,
                "error": "Message ID already exists"
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error sending Travel Rule message {message_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if not self.db_session:
                db.close()

    def _store_party_details(self, db: Session, message_id: int, payload: Dict[str, Any]):
        """Store detailed party information"""
        try:
            # Originator
            originator = payload.get("originator", {})
            if originator:
                party = TravelRuleParty(
                    message_id=message_id,
                    party_type="originator",
                    name=originator.get("name"),
                    address=originator.get("address"),
                    customer_id=originator.get("customer_id"),
                    national_id=originator.get("national_id"),
                    country_of_residence=originator.get("country_of_residence")
                )
                db.add(party)

            # Beneficiary
            beneficiary = payload.get("beneficiary", {})
            if beneficiary:
                party = TravelRuleParty(
                    message_id=message_id,
                    party_type="beneficiary",
                    name=beneficiary.get("name"),
                    address=beneficiary.get("address"),
                    customer_id=beneficiary.get("customer_id"),
                    national_id=beneficiary.get("national_id"),
                    country_of_residence=beneficiary.get("country_of_residence")
                )
                db.add(party)

            db.commit()

        except Exception as e:
            logger.error(f"Error storing party details for message {message_id}: {e}")
            db.rollback()

    def _redact_ivms101(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive information for display"""
        redacted = payload.copy()

        # Redact PII in originator and beneficiary
        for party_type in ["originator", "beneficiary"]:
            if party_type in redacted:
                party = redacted[party_type]
                if "name" in party:
                    party["name"] = "REDACTED"
                if "address" in party and isinstance(party["address"], dict):
                    party["address"] = {"country": party["address"].get("country", "UNKNOWN")}
                if "national_id" in party:
                    party["national_id"] = {"country": party["national_id"].get("country", "UNKNOWN")}

        return redacted

    def _trigger_audit_event(self, message_id: str, event_type: str, data: Dict[str, Any]):
        """Trigger audit event for Kafka"""
        try:
            from app.messaging.kafka_client import KafkaProducerClient

            producer = KafkaProducerClient()
            audit_event = {
                "event_id": str(uuid.uuid4()),
                "event_type": event_type,
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }

            producer.produce_event(
                topic=KafkaTopics.AUDIT_LOG,
                event=audit_event
            )

        except Exception as e:
            logger.error(f"Failed to trigger audit event: {e}")

    def _mask_vasp_id(self, vasp_id: str) -> str:
        """Mask VASP ID for logging"""
        if not vasp_id:
            return "UNKNOWN"
        return vasp_id[:8] + "..." + vasp_id[-4:] if len(vasp_id) > 12 else "MASKED"
    def get_message_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status and details of a Travel Rule message.

        Args:
            message_id: Message ID to query

        Returns:
            Dict with message details or None if not found
        """
        db = self.db_session or SessionLocal()

        try:
            message = db.query(TravelRuleMessage).filter(
                TravelRuleMessage.message_id == message_id
            ).first()

            if not message:
                return None

            # Redact sensitive information
            redacted_payload = self._redact_ivms101(message.ivms101_payload)

            created_at = getattr(message, "created_at", None)
            sent_at = getattr(message, "sent_at", None)

            return {
                "message_id": message.message_id,
                "status": message.status.value,
                "created_at": created_at.isoformat() if created_at else None,
                "sent_at": sent_at.isoformat() if sent_at else None,
                "ivms101_payload": redacted_payload
            }

        except Exception as e:
            logger.error(f"Error getting Travel Rule message {message_id}: {e}")
            return None
        finally:
            if not self.db_session:
                db.close()

    def _validate_ivms101(self, payload: Dict[str, Any]) -> list[str]:
        """Validate IVMS101 payload structure"""
        errors: list[str] = []

        # Required fields
        if not payload.get("originator"):
            errors.append("Missing originator information")
        if not payload.get("beneficiary"):
            errors.append("Missing beneficiary information")
        if not payload.get("transaction"):
            errors.append("Missing transaction information")

        # Originator validation
        originator = payload.get("originator", {})
        if not originator.get("name"):
            errors.append("Missing originator name")
        # Address optional: validate only if provided
        if originator.get("address") is not None:
            addr = originator.get("address")
            if isinstance(addr, dict):
                # simple presence checks for structured address
                if addr.get("country") and not _is_country_code(addr.get("country")):
                    errors.append("Originator address country must be ISO alpha-2")
        # Optional identity fields
        dob = originator.get("date_of_birth")
        if dob and not _is_iso_date(dob):
            errors.append("Originator date_of_birth must be YYYY-MM-DD")
        nat_id = originator.get("national_id")
        if isinstance(nat_id, dict):
            if nat_id.get("country") and not _is_country_code(nat_id.get("country")):
                errors.append("Originator national_id.country must be ISO alpha-2")

        # Beneficiary validation
        beneficiary = payload.get("beneficiary", {})
        if not beneficiary.get("name"):
            errors.append("Missing beneficiary name")
        # Address optional: validate only if provided
        if beneficiary.get("address") is not None:
            addr = beneficiary.get("address")
            if isinstance(addr, dict):
                if addr.get("country") and not _is_country_code(addr.get("country")):
                    errors.append("Beneficiary address country must be ISO alpha-2")
        # Optional identity fields
        dob_b = beneficiary.get("date_of_birth")
        if dob_b and not _is_iso_date(dob_b):
            errors.append("Beneficiary date_of_birth must be YYYY-MM-DD")
        nat_id_b = beneficiary.get("national_id")
        if isinstance(nat_id_b, dict):
            if nat_id_b.get("country") and not _is_country_code(nat_id_b.get("country")):
                errors.append("Beneficiary national_id.country must be ISO alpha-2")

        # Transaction validation
        transaction = payload.get("transaction", {})
        if not transaction.get("amount"):
            errors.append("Missing transaction amount")
        else:
            try:
                amt = float(transaction.get("amount"))
                if amt <= 0:
                    errors.append("Transaction amount must be positive")
            except Exception:
                errors.append("Transaction amount must be numeric")
        if not transaction.get("currency"):
            errors.append("Missing transaction currency")
        else:
            cur = str(transaction.get("currency")).upper()
            if not _is_currency_code(cur):
                errors.append("Transaction currency must be 3-letter ISO code")

        return errors


# Helper to safely await sync/async is_sanctioned
def awaitable_false(func, *args, **kwargs) -> bool:
    try:
        import asyncio
        res = func(*args, **kwargs)
        if asyncio.iscoroutine(res):
            loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else asyncio.new_event_loop()
            if not loop.is_running():
                try:
                    asyncio.set_event_loop(loop)
                except Exception:
                    pass
            try:
                return loop.run_until_complete(res)
            except Exception:
                return False
        return bool(res)
    except Exception:
        return False



# Global service instance
travel_rule_service = TravelRuleService()
