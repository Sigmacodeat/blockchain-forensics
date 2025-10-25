"""
BTC Invoice Service
Handles invoice creation, payment monitoring, and matching.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.btc_wallet_service import btc_wallet_service
from app.config import settings


class BTCInvoiceService:
    """Service for BTC invoice management and payment matching."""

    def create_invoice(self, user_id: str, plan_name: str, amount_btc: float, expires_hours: int = 24) -> Dict[str, str]:
        """Create a new BTC invoice with unique address."""
        order_id = f"btc_inv_{uuid.uuid4().hex[:16]}"

        # Generate unique address for this invoice
        invoice_data = btc_wallet_service.generate_invoice_address(order_id, plan_name, amount_btc)

        # Store in database
        db: Session = next(get_db())
        try:
            from app.models.crypto_payment import CryptoDepositAddress
            deposit_addr = CryptoDepositAddress(
                user_id=user_id,
                order_id=order_id,
                plan_name=plan_name,
                currency="BTC",
                address=invoice_data["address"],
                private_key_encrypted=invoice_data["encrypted_private_key"],
                expected_amount_btc=amount_btc,
                expires_at=datetime.utcnow() + timedelta(hours=expires_hours)
            )
            db.add(deposit_addr)
            db.commit()
            db.refresh(deposit_addr)

            return {
                "order_id": order_id,
                "address": invoice_data["address"],
                "expected_amount_btc": str(amount_btc),
                "expires_at": deposit_addr.expires_at.isoformat(),
                "plan_name": plan_name
            }
        finally:
            db.close()

    def check_payment_status(self, order_id: str) -> Dict[str, any]:
        """Check if invoice payment has been received."""
        db: Session = next(get_db())
        try:
            from app.models.crypto_payment import CryptoDepositAddress
            deposit_addr = db.query(CryptoDepositAddress).filter(
                CryptoDepositAddress.order_id == order_id
            ).first()

            if not deposit_addr:
                return {"status": "not_found"}

            if deposit_addr.status == "paid":
                return {
                    "status": "paid",
                    "received_amount_btc": str(deposit_addr.received_amount_btc),
                    "expected_amount_btc": str(deposit_addr.expected_amount_btc),
                    "address": deposit_addr.address,
                    "plan_name": deposit_addr.plan_name,
                    "expires_at": deposit_addr.expires_at.isoformat() if deposit_addr.expires_at else None,
                    "txid": deposit_addr.txid,
                    "paid_at": deposit_addr.paid_at.isoformat() if deposit_addr.paid_at else None,
                }

            if deposit_addr.expires_at < datetime.utcnow():
                deposit_addr.status = "expired"
                db.commit()
                return {
                    "status": "expired",
                    "expected_amount_btc": str(deposit_addr.expected_amount_btc),
                    "address": deposit_addr.address,
                    "plan_name": deposit_addr.plan_name,
                    "expires_at": deposit_addr.expires_at.isoformat() if deposit_addr.expires_at else None,
                }

            # Check current received amount
            total_received = btc_wallet_service.get_total_received(deposit_addr.address)
            deposit_addr.received_amount_btc = total_received

            if total_received >= deposit_addr.expected_amount_btc:
                deposit_addr.status = "paid"
                deposit_addr.paid_at = datetime.utcnow()
                # In production, get actual TXID from recent transactions
                txs = btc_wallet_service.get_transactions(deposit_addr.address)
                if txs:
                    deposit_addr.txid = txs[0]["hash"]
                db.commit()

                return {
                    "status": "paid",
                    "received_amount_btc": str(total_received),
                    "expected_amount_btc": str(deposit_addr.expected_amount_btc),
                    "address": deposit_addr.address,
                    "plan_name": deposit_addr.plan_name,
                    "expires_at": deposit_addr.expires_at.isoformat() if deposit_addr.expires_at else None,
                    "txid": deposit_addr.txid,
                    "paid_at": deposit_addr.paid_at.isoformat() if deposit_addr.paid_at else None,
                }

            db.commit()
            return {
                "status": "pending",
                "received_amount_btc": str(total_received),
                "expected_amount_btc": str(deposit_addr.expected_amount_btc),
                "address": deposit_addr.address,
                "plan_name": deposit_addr.plan_name,
                "expires_at": deposit_addr.expires_at.isoformat() if deposit_addr.expires_at else None,
            }
        finally:
            db.close()

    def get_pending_invoices(self) -> List[Dict[str, any]]:
        """Get all pending invoices for monitoring."""
        db: Session = next(get_db())
        try:
            from app.models.crypto_payment import CryptoDepositAddress
            invoices = db.query(CryptoDepositAddress).filter(
                CryptoDepositAddress.status == "pending",
                CryptoDepositAddress.expires_at > datetime.utcnow()
            ).all()

            return [{
                "order_id": inv.order_id,
                "user_id": inv.user_id,
                "address": inv.address,
                "expected_amount_btc": str(inv.expected_amount_btc),
                "plan_name": inv.plan_name
            } for inv in invoices]
        finally:
            db.close()


# Global instance
btc_invoice_service = BTCInvoiceService()
