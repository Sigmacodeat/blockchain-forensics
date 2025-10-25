"""
Travel Rule Protocol Adapters
Support for TRISA and TRP (Travel Rule Information Sharing Alliance)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json
import logging
import os
import base64
from datetime import datetime

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)


@dataclass
class TravelRulePayload:
    """Travel Rule data payload"""
    sender_vasp: str
    receiver_vasp: str
    tx_hash: Optional[str] = None
    amount: Optional[float] = None
    amount_currency: str = "USD"
    originator: Optional[Dict[str, Any]] = None
    beneficiary: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TravelRuleResponse:
    """Travel Rule response"""
    success: bool
    message: str
    reference_id: Optional[str] = None
    delivery_status: str = "pending"
    error_details: Optional[Dict[str, Any]] = None


class TravelRuleAdapter(ABC):
    """Base adapter for Travel Rule protocols"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def prepare_payload(self, payload: TravelRulePayload) -> str:
        """Prepare payload for sending"""
        pass

    @abstractmethod
    async def send_payload(self, prepared_payload: str) -> TravelRuleResponse:
        """Send prepared payload"""
        pass

    @abstractmethod
    async def check_status(self, reference_id: str) -> TravelRuleResponse:
        """Check delivery status"""
        pass


class TRISAAdapter(TravelRuleAdapter):
    """TRISA Protocol Adapter"""

    async def prepare_payload(self, payload: TravelRulePayload) -> str:
        """Prepare TRISA payload"""
        key_b64, nonce_b64, ciphertext_b64 = self._encrypt_data(payload)
        trisa_payload = {
            "version": "1.0",
            "identity": self.config.get("vasp_code"),
            "envelope": {
                "alg": "AES-GCM",
                "enc_key": key_b64,
                "nonce": nonce_b64,
                "ciphertext": ciphertext_b64,
            },
            "meta": {
                "prepared_at": datetime.utcnow().isoformat()
            }
        }
        return json.dumps(trisa_payload)

    async def send_payload(self, prepared_payload: str) -> TravelRuleResponse:
        """Send via TRISA protocol"""
        endpoint = (self.config or {}).get("endpoint")
        if not endpoint:
            return TravelRuleResponse(
                success=True,
                message="TRISA payload prepared",
                reference_id="trisa_" + str(hash(prepared_payload)),
                delivery_status="prepared",
            )
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(endpoint.rstrip("/") + "/trisa/send", content=prepared_payload, headers={"content-type":"application/json"})
                if resp.status_code >= 200 and resp.status_code < 300:
                    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    ref = data.get("reference_id") or data.get("id") or ("trisa_" + str(hash(prepared_payload)))
                    return TravelRuleResponse(success=True, message="TRISA sent", reference_id=ref, delivery_status=data.get("status", "submitted"))
                return TravelRuleResponse(success=False, message=f"TRISA send failed: {resp.status_code}", error_details={"status_code": resp.status_code})
        except Exception as e:
            logger.error(f"TRISA send error: {e}")
            return TravelRuleResponse(success=False, message=str(e), error_details={"error": str(e)})

    async def check_status(self, reference_id: str) -> TravelRuleResponse:
        """Check TRISA delivery status"""
        endpoint = (self.config or {}).get("endpoint")
        if not endpoint:
            return TravelRuleResponse(success=True, message="TRISA status", reference_id=reference_id, delivery_status="delivered")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(endpoint.rstrip("/") + f"/trisa/status/{reference_id}")
                if resp.status_code >= 200 and resp.status_code < 300:
                    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    return TravelRuleResponse(success=True, message="TRISA status", reference_id=reference_id, delivery_status=data.get("status", "unknown"))
                return TravelRuleResponse(success=False, message=f"TRISA status failed: {resp.status_code}", reference_id=reference_id, error_details={"status_code": resp.status_code})
        except Exception as e:
            logger.error(f"TRISA status error: {e}")
            return TravelRuleResponse(success=False, message=str(e), reference_id=reference_id, error_details={"error": str(e)})

    def _generate_encryption_key(self) -> bytes:
        return AESGCM.generate_key(bit_length=256)

    def _encrypt_data(self, payload: TravelRulePayload) -> tuple[str, str, str]:
        key = self._generate_encryption_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        plaintext = json.dumps(payload.__dict__).encode("utf-8")
        ct = aesgcm.encrypt(nonce, plaintext, None)
        return base64.b64encode(key).decode(), base64.b64encode(nonce).decode(), base64.b64encode(ct).decode()


class TRPAdapter(TravelRuleAdapter):
    """TRP Protocol Adapter"""

    async def prepare_payload(self, payload: TravelRulePayload) -> str:
        """Prepare TRP payload"""
        trp_payload = {
            "protocol_version": "2.0",
            "message_type": "travel_rule",
            "vasp_code": self.config.get("vasp_code"),
            "payload": payload.__dict__
        }
        return json.dumps(trp_payload)

    async def send_payload(self, prepared_payload: str) -> TravelRuleResponse:
        """Send via TRP protocol"""
        endpoint = (self.config or {}).get("endpoint")
        if not endpoint:
            return TravelRuleResponse(
                success=True,
                message="TRP payload prepared",
                reference_id="trp_" + str(hash(prepared_payload)),
                delivery_status="prepared",
            )
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(endpoint.rstrip("/") + "/trp/send", content=prepared_payload, headers={"content-type":"application/json"})
                if resp.status_code >= 200 and resp.status_code < 300:
                    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    ref = data.get("reference_id") or data.get("id") or ("trp_" + str(hash(prepared_payload)))
                    return TravelRuleResponse(success=True, message="TRP sent", reference_id=ref, delivery_status=data.get("status", "submitted"))
                return TravelRuleResponse(success=False, message=f"TRP send failed: {resp.status_code}", error_details={"status_code": resp.status_code})
        except Exception as e:
            logger.error(f"TRP send error: {e}")
            return TravelRuleResponse(success=False, message=str(e), error_details={"error": str(e)})

    async def check_status(self, reference_id: str) -> TravelRuleResponse:
        """Check TRP delivery status"""
        endpoint = (self.config or {}).get("endpoint")
        if not endpoint:
            return TravelRuleResponse(success=True, message="TRP status", reference_id=reference_id, delivery_status="delivered")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(endpoint.rstrip("/") + f"/trp/status/{reference_id}")
                if resp.status_code >= 200 and resp.status_code < 300:
                    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    return TravelRuleResponse(success=True, message="TRP status", reference_id=reference_id, delivery_status=data.get("status", "unknown"))
                return TravelRuleResponse(success=False, message=f"TRP status failed: {resp.status_code}", reference_id=reference_id, error_details={"status_code": resp.status_code})
        except Exception as e:
            logger.error(f"TRP status error: {e}")
            return TravelRuleResponse(success=False, message=str(e), reference_id=reference_id, error_details={"error": str(e)})


class TravelRuleManager:
    """Manages Travel Rule protocol adapters"""

    def __init__(self):
        self.adapters: Dict[str, TravelRuleAdapter] = {}

    def register_adapter(self, protocol: str, adapter: TravelRuleAdapter):
        """Register a protocol adapter"""
        self.adapters[protocol] = adapter

    def get_adapter(self, protocol: str) -> Optional[TravelRuleAdapter]:
        """Get adapter for protocol"""
        return self.adapters.get(protocol)

    async def prepare_and_send(self, protocol: str, payload: TravelRulePayload) -> TravelRuleResponse:
        """Prepare and send Travel Rule payload"""
        adapter = self.get_adapter(protocol)
        if not adapter:
            return TravelRuleResponse(
                success=False,
                message=f"Unsupported protocol: {protocol}",
                error_details={"protocol": protocol}
            )

        try:
            prepared = await adapter.prepare_payload(payload)
            response = await adapter.send_payload(prepared)
            return response
        except Exception as e:
            logger.error(f"Travel Rule error for {protocol}: {e}")
            return TravelRuleResponse(
                success=False,
                message=f"Travel Rule failed: {str(e)}",
                error_details={"error": str(e)}
            )


from app.config import settings

# Global instance
travel_rule_manager = TravelRuleManager()

# Register default adapters with config from settings/env
trisa_cfg = {
    "vasp_code": getattr(settings, "VASP_CODE", None) or os.environ.get("VASP_CODE") or "DEV_VASP",
    "endpoint": getattr(settings, "TRISA_ENDPOINT", None) or os.environ.get("TRISA_ENDPOINT") or None,
}
trp_cfg = {
    "vasp_code": getattr(settings, "VASP_CODE", None) or os.environ.get("VASP_CODE") or "DEV_VASP",
    "endpoint": getattr(settings, "TRP_ENDPOINT", None) or os.environ.get("TRP_ENDPOINT") or None,
}

travel_rule_manager.register_adapter("TRISA", TRISAAdapter(trisa_cfg))
travel_rule_manager.register_adapter("TRP", TRPAdapter(trp_cfg))
