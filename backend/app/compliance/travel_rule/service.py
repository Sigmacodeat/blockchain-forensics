"""
Travel Rule Compliance Service
Manages Travel Rule obligations for VASPs (Virtual Asset Service Providers)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

from .adapters import (
    TravelRulePayload,
    TravelRuleResponse,
    travel_rule_manager
)

logger = logging.getLogger(__name__)


class TravelRuleService:
    """
    Travel Rule compliance service following FATF Recommendation 16
    
    Ensures VASPs exchange required customer information for transactions
    above threshold ($1000 USD equivalent).
    """
    
    # FATF threshold for Travel Rule
    THRESHOLD_USD = 1000.0
    
    def __init__(self):
        self.transaction_log: List[Dict[str, Any]] = []
        self.pending_transfers: Dict[str, Dict[str, Any]] = {}
        # Optional Redis client for persistence (best-effort)
        try:
            from app.db.redis_client import redis_client  # type: ignore
            self._redis_client = redis_client
        except Exception:
            self._redis_client = None
    
    async def check_travel_rule_required(
        self,
        chain: str,
        amount: float,
        currency: str = "USD"
    ) -> bool:
        """
        Check if Travel Rule applies to transaction.
        
        Args:
            chain: Blockchain network
            amount: Transaction amount
            currency: Currency (default USD)
            
        Returns:
            True if Travel Rule required
        """
        # Convert to USD if needed (simplified - production would use real exchange rates)
        amount_usd = amount
        
        if currency != "USD":
            # Simplified conversion
            if currency == "EUR":
                amount_usd = amount * 1.1
            elif currency == "GBP":
                amount_usd = amount * 1.27
            # For crypto: would need real-time price feeds
            elif currency in ["BTC", "ETH"]:
                # Placeholder - would integrate with price oracles
                amount_usd = amount * 50000  # Simplified
        
        return amount_usd >= self.THRESHOLD_USD
    
    async def initiate_transfer(
        self,
        protocol: str,
        sender_vasp: str,
        receiver_vasp: str,
        tx_hash: Optional[str],
        chain: str,
        amount: float,
        currency: str,
        originator: Dict[str, Any],
        beneficiary: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> TravelRuleResponse:
        """
        Initiate Travel Rule compliant transfer.
        
        Args:
            protocol: Travel Rule protocol (TRISA, TRP)
            sender_vasp: Sending VASP identifier
            receiver_vasp: Receiving VASP identifier
            tx_hash: Transaction hash (if available)
            chain: Blockchain network
            amount: Transfer amount
            currency: Currency code
            originator: Originator information (name, address, account, etc.)
            beneficiary: Beneficiary information
            metadata: Additional metadata
            
        Returns:
            Travel Rule response with reference ID
        """
        # Validate required fields
        required_originator = ["name", "account_number"]
        required_beneficiary = ["name", "account_number"]
        
        if not all(k in originator for k in required_originator):
            return TravelRuleResponse(
                success=False,
                message="Missing required originator information",
                error_details={"missing": [k for k in required_originator if k not in originator]}
            )
        
        if not all(k in beneficiary for k in required_beneficiary):
            return TravelRuleResponse(
                success=False,
                message="Missing required beneficiary information",
                error_details={"missing": [k for k in required_beneficiary if k not in beneficiary]}
            )
        
        # Check if Travel Rule applies
        is_required = await self.check_travel_rule_required(chain, amount, currency)
        
        if not is_required:
            logger.info(f"Travel Rule not required for {amount} {currency}")
            return TravelRuleResponse(
                success=True,
                message="Travel Rule threshold not reached",
                delivery_status="not_required"
            )
        
        # Create payload
        payload = TravelRulePayload(
            sender_vasp=sender_vasp,
            receiver_vasp=receiver_vasp,
            tx_hash=tx_hash,
            amount=amount,
            amount_currency=currency,
            originator=originator,
            beneficiary=beneficiary,
            metadata={
                "chain": chain,
                "initiated_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
        )
        
        # Send via protocol
        response = await travel_rule_manager.prepare_and_send(protocol, payload)
        
        # Log transaction
        self.transaction_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "protocol": protocol,
            "sender_vasp": sender_vasp,
            "receiver_vasp": receiver_vasp,
            "tx_hash": tx_hash,
            "amount": amount,
            "currency": currency,
            "reference_id": response.reference_id,
            "status": response.delivery_status,
            "success": response.success
        })
        
        # Track pending if not immediately completed
        if response.reference_id and response.delivery_status in ["pending", "submitted", "prepared"]:
            self.pending_transfers[response.reference_id] = {
                "payload": payload.__dict__,
                "protocol": protocol,
                "initiated_at": datetime.utcnow().isoformat()
            }
            # Mirror to Redis (best-effort)
            try:
                if self._redis_client:
                    client = await self._redis_client.get_client()
                    if client:
                        key = f"travel_rule:pending:{response.reference_id}"
                        await client.set(key, json.dumps(self.pending_transfers[response.reference_id]))
            except Exception:
                pass
        
        return response
    
    async def receive_inbound(
        self,
        protocol: str,
        reference_id: str,
        status: str | None,
        payload: dict | None = None,
    ) -> dict:
        """Receive inbound Travel Rule notification/webhook from counterparty VASP.

        Updates pending transfer status and keeps last inbound payload for auditing.
        """
        # Normalize
        status_norm = (status or "received").lower()
        # Track last inbound by reference
        inbound_key = f"inbound:{reference_id}"
        try:
            # Store lightweight audit snapshot in memory (best-effort)
            self.pending_transfers.setdefault(reference_id, {})
            self.pending_transfers[reference_id]["last_inbound"] = {
                "protocol": protocol,
                "status": status_norm,
                "received_at": datetime.utcnow().isoformat(),
            }
            # Mirror to Redis
            try:
                if self._redis_client:
                    client = await self._redis_client.get_client()
                    if client:
                        key = f"travel_rule:pending:{reference_id}"
                        if reference_id in self.pending_transfers:
                            await client.set(key, json.dumps(self.pending_transfers[reference_id]))
            except Exception:
                pass
        except Exception:
            pass

        # If delivered/confirmed/completed -> clear pending
        if status_norm in ["delivered", "confirmed", "completed"]:
            self.pending_transfers.pop(reference_id, None)
            try:
                if self._redis_client:
                    client = await self._redis_client.get_client()
                    if client:
                        await client.delete(f"travel_rule:pending:{reference_id}")
            except Exception:
                pass

        return {
            "reference_id": reference_id,
            "protocol": protocol,
            "status": status_norm,
            "pending": reference_id in self.pending_transfers,
        }
    
    async def check_transfer_status(
        self,
        protocol: str,
        reference_id: str
    ) -> TravelRuleResponse:
        """
        Check status of Travel Rule transfer.
        
        Args:
            protocol: Protocol used (TRISA, TRP)
            reference_id: Reference ID from initiate_transfer
            
        Returns:
            Current status
        """
        adapter = travel_rule_manager.get_adapter(protocol)
        if not adapter:
            return TravelRuleResponse(
                success=False,
                message=f"Unknown protocol: {protocol}",
                error_details={"protocol": protocol}
            )
        
        response = await adapter.check_status(reference_id)
        
        # Update pending transfers
        if reference_id in self.pending_transfers:
            if response.delivery_status in ["delivered", "confirmed", "completed"]:
                # Remove from pending
                self.pending_transfers.pop(reference_id, None)
        
        return response
    
    def get_transaction_history(
        self,
        vasp: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get Travel Rule transaction history.
        
        Args:
            vasp: Filter by VASP (sender or receiver)
            limit: Maximum records to return
            
        Returns:
            List of transactions
        """
        logs = self.transaction_log
        
        if vasp:
            logs = [
                log for log in logs
                if log.get("sender_vasp") == vasp or log.get("receiver_vasp") == vasp
            ]
        
        # Sort by timestamp descending
        logs = sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return logs[:limit]
    
    def get_pending_transfers(self) -> List[Dict[str, Any]]:
        """Get all pending Travel Rule transfers.

        If Redis is available, read from Redis keys; otherwise return in-memory map.
        """
        out: List[Dict[str, Any]] = []
        try:
            if self._redis_client:
                import asyncio
                # Use async Redis client
                async def _load() -> List[Dict[str, Any]]:
                    items: List[Dict[str, Any]] = []
                    client = await self._redis_client.get_client()
                    if not client:
                        return items
                    # Scan keys (limited scope)
                    cursor = 0
                    pattern = "travel_rule:pending:*"
                    while True:
                        cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
                        for k in keys:
                            try:
                                val = await client.get(k)
                                if val:
                                    data = json.loads(val)
                                    ref = str(k).split(":")[-1]
                                    items.append({"reference_id": ref, **data})
                            except Exception:
                                continue
                        if cursor == 0:
                            break
                    return items
                # Run the async loader (this method is sync)
                try:
                    import asyncio as _asyncio
                    loop = None
                    try:
                        loop = _asyncio.get_event_loop()
                    except Exception:
                        loop = None
                    if loop and loop.is_running():
                        # In running loop context, fallback to in-memory
                        raise RuntimeError("async loop running")
                    out = _asyncio.run(_load())
                except Exception:
                    out = []
        except Exception:
            out = []
        if out:
            return out
        # Fallback to in-memory map
        return [
            {"reference_id": ref_id, **data}
            for ref_id, data in self.pending_transfers.items()
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Travel Rule compliance statistics"""
        total = len(self.transaction_log)
        successful = sum(1 for log in self.transaction_log if log.get("success"))
        pending = len(self.pending_transfers)
        
        # By protocol
        by_protocol = {}
        for log in self.transaction_log:
            protocol = log.get("protocol", "unknown")
            by_protocol[protocol] = by_protocol.get(protocol, 0) + 1
        
        return {
            "total_transfers": total,
            "successful": successful,
            "failed": total - successful,
            "pending": pending,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "by_protocol": by_protocol
        }


# Global service instance
travel_rule_service = TravelRuleService()
