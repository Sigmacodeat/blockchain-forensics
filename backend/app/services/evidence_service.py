"""
Evidence Chain-of-Custody Service
===================================

Provides cryptographic chain-of-custody for case evidence:
- SHA-256 hashing of attachments
- Timestamping with RFC3161 support
- Signature generation (eIDAS-ready)
- Evidence package export for courts
- Tamper detection
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class EvidenceItem:
    """Single evidence item with custody chain"""
    file_hash: str
    filename: str
    uploaded_at: str
    uploaded_by: str
    chain_position: int
    previous_hash: Optional[str] = None
    signature: Optional[str] = None
    timestamp_token: Optional[str] = None


@dataclass
class ChainOfCustody:
    """Complete chain of custody for a case"""
    case_id: str
    items: List[EvidenceItem]
    created_at: str
    chain_hash: str
    is_valid: bool = True
    

class EvidenceService:
    """Manages evidence chain-of-custody"""
    
    def __init__(self):
        self._chains: Dict[str, List[EvidenceItem]] = {}
    
    def add_evidence(
        self,
        case_id: str,
        file_hash: str,
        filename: str,
        uploaded_by: str,
        file_content: Optional[bytes] = None
    ) -> EvidenceItem:
        """Add evidence item to chain with automatic linking"""
        if case_id not in self._chains:
            self._chains[case_id] = []
        
        chain = self._chains[case_id]
        position = len(chain)
        
        # Get previous hash for chain linking
        previous_hash = chain[-1].file_hash if chain else None
        
        # Create evidence item
        item = EvidenceItem(
            file_hash=file_hash,
            filename=filename,
            uploaded_at=datetime.utcnow().isoformat(),
            uploaded_by=uploaded_by,
            chain_position=position,
            previous_hash=previous_hash
        )
        
        # Optional: Generate timestamp token (RFC3161 stub)
        if file_content:
            item.timestamp_token = self._generate_timestamp(file_content)
        
        # Optional: Generate signature (eIDAS-ready stub)
        item.signature = self._generate_signature(item)
        
        chain.append(item)
        
        logger.info(f"Evidence added to case {case_id}: {filename} at position {position}")
        # Best-effort: append to Evidence Vault asynchronously (does not block request)
        try:
            asyncio.create_task(self._append_evidence_vault_async(case_id, item))
        except Exception:
            pass
        return item
    
    def get_chain(self, case_id: str) -> Optional[ChainOfCustody]:
        """Get complete chain of custody for case"""
        if case_id not in self._chains:
            return None
        
        chain = self._chains[case_id]
        if not chain:
            return None
        
        # Calculate chain hash
        chain_data = json.dumps([
            {
                "hash": item.file_hash,
                "pos": item.chain_position,
                "prev": item.previous_hash
            }
            for item in chain
        ], sort_keys=True)
        
        chain_hash = hashlib.sha256(chain_data.encode()).hexdigest()
        
        # Verify chain integrity
        is_valid = self._verify_chain(chain)
        
        return ChainOfCustody(
            case_id=case_id,
            items=chain,
            created_at=chain[0].uploaded_at if chain else "",
            chain_hash=chain_hash,
            is_valid=is_valid
        )
    
    def _verify_chain(self, chain: List[EvidenceItem]) -> bool:
        """Verify chain integrity"""
        if not chain:
            return True
        
        # First item should have no previous
        if chain[0].previous_hash is not None:
            return False
        
        # Check all links
        for i in range(1, len(chain)):
            if chain[i].previous_hash != chain[i-1].file_hash:
                logger.error(f"Chain broken at position {i}")
                return False
        
        return True
    
    def _generate_timestamp(self, content: bytes) -> str:
        """Generate RFC3161 timestamp token (stub)
        
        In production, this would call a TSA (Time Stamping Authority)
        """
        # Stub: Simple hash-based timestamp
        ts = datetime.utcnow().isoformat()
        data = f"{ts}:{hashlib.sha256(content).hexdigest()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _generate_signature(self, item: EvidenceItem) -> str:
        """Generate cryptographic signature (eIDAS-ready stub)
        
        In production, this would use proper PKI/eIDAS infrastructure
        """
        # Stub: HMAC-style signature
        sig_data = f"{item.file_hash}:{item.uploaded_at}:{item.uploaded_by}"
        return hashlib.sha256(sig_data.encode()).hexdigest()
    
    async def _append_evidence_vault_async(self, case_id: str, item: EvidenceItem) -> None:
        """Append an entry to the append-only Evidence Vault (best-effort)."""
        try:
            from app.services.evidence_vault import evidence_vault
            payload = {
                "case_id": case_id,
                "filename": item.filename,
                "file_hash": item.file_hash,
                "uploaded_at": item.uploaded_at,
                "uploaded_by": item.uploaded_by,
                "previous_hash": item.previous_hash,
                "chain_position": item.chain_position,
            }
            meta = {"source": "evidence_service"}
            await evidence_vault.append("evidence_added", payload, meta)
        except Exception:
            # Non-fatal; Evidence Vault may be disabled or DB unavailable
            pass
    
    def export_package(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Export evidence package for court submission"""
        chain = self.get_chain(case_id)
        if not chain:
            return None
        
        package = {
            "case_id": case_id,
            "export_date": datetime.utcnow().isoformat(),
            "chain_hash": chain.chain_hash,
            "is_valid": chain.is_valid,
            "evidence_count": len(chain.items),
            "items": [
                {
                    "position": item.chain_position,
                    "filename": item.filename,
                    "hash": item.file_hash,
                    "uploaded_at": item.uploaded_at,
                    "uploaded_by": item.uploaded_by,
                    "previous_hash": item.previous_hash,
                    "signature": item.signature,
                    "timestamp_token": item.timestamp_token
                }
                for item in chain.items
            ],
            "verification": {
                "method": "SHA-256 chain linking",
                "algorithm": "RFC3161 timestamping (stub)",
                "signature_standard": "eIDAS-ready (stub)"
            }
        }
        
        return package
    
    def verify_package(self, package: Dict[str, Any]) -> bool:
        """Verify exported evidence package"""
        try:
            items = package.get("items", [])
            if not items:
                return False
            
            # Verify chain links
            for i in range(1, len(items)):
                if items[i]["previous_hash"] != items[i-1]["hash"]:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Package verification failed: {e}")
            return False


# Global instance
evidence_service = EvidenceService()
