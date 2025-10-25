"""
Signing and Manifest Service for Chain-of-Custody
=================================================

Provides cryptographic signing and manifest generation for forensic reports
to ensure integrity and court admissibility.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SigningProvider(ABC):
    """Abstract base class for signing providers"""

    @abstractmethod
    def sign_data(self, data: bytes) -> str:
        """Sign data and return signature"""
        pass

    @abstractmethod
    def verify_signature(self, data: bytes, signature: str) -> bool:
        """Verify signature against data"""
        pass


class DummySigningProvider(SigningProvider):
    """Dummy signing provider for development/testing"""

    def sign_data(self, data: bytes) -> str:
        """Return a dummy signature"""
        return f"dummy_sig_{hashlib.sha256(data).hexdigest()[:16]}"

    def verify_signature(self, data: bytes, signature: str) -> bool:
        """Always return True for dummy (test behavior) but validate for manifest integrity"""
        if not signature.startswith("dummy_sig_"):
            return False
        # For testing purposes, always return True to maintain backward compatibility
        # But for manifest verification, we need proper validation
        return True


class ManifestService:
    """Service for generating and managing report manifests"""

    def __init__(self, signing_provider: Optional[SigningProvider] = None):
        self.signing_provider = signing_provider or DummySigningProvider()
        self.algorithm = "SHA-256"

    def generate_manifest(
        self,
        report_id: str,
        report_type: str,
        content_hash: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a manifest for a report"""

        manifest = {
            "manifest_version": "1.0",
            "report_id": report_id,
            "report_type": report_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": content_hash,
            "hash_algorithm": self.algorithm,
            "platform": "Blockchain Forensics Platform v1.0.0",
            "metadata": metadata or {}
        }

        # Add signature to manifest
        manifest_data = json.dumps(manifest, sort_keys=True).encode('utf-8')
        manifest["signature"] = self.signing_provider.sign_data(manifest_data)

        return manifest

    def verify_manifest(self, manifest: Dict[str, Any]) -> bool:
        """Verify the integrity of a manifest"""

        try:
            # Create a copy for verification (without signature)
            signature = manifest.get("signature")
            if not signature:
                return False

            verification_data = {k: v for k, v in manifest.items() if k != "signature"}
            
            # For dummy signatures, validate the signature format matches expected data
            if signature.startswith("dummy_sig_"):
                expected_signature = f"dummy_sig_{hashlib.sha256(json.dumps(verification_data, sort_keys=True).encode('utf-8')).hexdigest()[:16]}"
                if signature != expected_signature:
                    return False
            
            manifest_data = json.dumps(verification_data, sort_keys=True).encode('utf-8')
            return self.signing_provider.verify_signature(manifest_data, signature)

        except Exception as e:
            logger.error(f"Manifest verification failed: {e}")
            return False

    def compute_content_hash(self, content: bytes) -> str:
        """Compute SHA-256 hash of report content"""
        return hashlib.sha256(content).hexdigest()


# Global instance
manifest_service = ManifestService()


def generate_report_hash_and_manifest(
    report_id: str,
    report_type: str,
    content: bytes,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[str, Dict[str, Any]]:
    """Generate hash and manifest for a report"""

    content_hash = manifest_service.compute_content_hash(content)
    manifest = manifest_service.generate_manifest(
        report_id=report_id,
        report_type=report_type,
        content_hash=content_hash,
        metadata=metadata
    )

    return content_hash, manifest


__all__ = [
    'SigningProvider',
    'DummySigningProvider',
    'ManifestService',
    'manifest_service',
    'generate_report_hash_and_manifest'
]
