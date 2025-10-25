"""
BTC Invoice Payment Monitor Worker
Monitors pending invoices and matches payments via Esplora API.
"""

import asyncio
import logging
import time
from datetime import datetime
from app.services.btc_invoice_service import btc_invoice_service
from app.config import settings

logger = logging.getLogger(__name__)

# Import metrics
try:
    from app import metrics
except ImportError:
    metrics = None


def _track_invoice_monitor(status: str, duration: float = 0.0) -> None:
    """Track invoice monitoring metrics"""
    if not metrics:
        return

    try:
        metrics.INVOICE_MONITOR_CHECKS_TOTAL.labels(status=status).inc()
        if duration > 0:
            metrics.INVOICE_MONITOR_CHECK_DURATION.observe(duration)
    except Exception:
        pass


class BTCInvoiceMonitorWorker:
    """Worker to monitor BTC invoice payments."""

    def __init__(self):
        self.running = False
        self.check_interval = 60  # Check every minute

    async def start_monitoring(self):
        """Start the invoice monitoring loop."""
        self.running = True
        logger.info("BTC Invoice Monitor Worker started")

        while self.running:
            try:
                start_time = time.time()
                await self._check_pending_invoices()
                duration = time.time() - start_time
                _track_invoice_monitor("success", duration)
            except Exception as e:
                logger.error(f"Invoice monitoring error: {e}")
                _track_invoice_monitor("error")

            await asyncio.sleep(self.check_interval)

    def stop_monitoring(self):
        """Stop the monitoring loop."""
        self.running = False
        logger.info("BTC Invoice Monitor Worker stopped")

    async def _check_pending_invoices(self):
        """Check all pending invoices for payments."""
        try:
            pending_invoices = btc_invoice_service.get_pending_invoices()

            if not pending_invoices:
                return

            logger.info(f"Checking {len(pending_invoices)} pending invoices")

            updated_count = 0
            for invoice in pending_invoices:
                try:
                    old_status = btc_invoice_service.check_payment_status(invoice["order_id"])
                    # Force re-check (this will update DB if payment received)
                    status = btc_invoice_service.check_payment_status(invoice["order_id"])

                    if status["status"] != old_status.get("status", "pending"):
                        updated_count += 1
                        logger.info(f"Invoice {invoice['order_id']} status: {status['status']}")

                        # Broadcast to WebSocket clients
                        try:
                            from app.api.v1.websockets.payment import broadcast_invoice_update
                            await broadcast_invoice_update(invoice["order_id"], status)
                        except Exception as ws_error:
                            logger.warning(f"WebSocket broadcast failed for {invoice['order_id']}: {ws_error}")

                        # Activate subscription if payment was successful
                        if status["status"] == "paid":
                            try:
                                from app.services.subscription_activation_service import handle_paid_invoice
                                await handle_paid_invoice(invoice["order_id"])
                            except Exception as sub_error:
                                logger.error(f"Subscription activation failed for {invoice['order_id']}: {sub_error}")
                except Exception as e:
                    logger.error(f"Error checking invoice {invoice['order_id']}: {e}")

            if updated_count > 0:
                logger.info(f"Updated {updated_count} invoices")

        except Exception as e:
            logger.error(f"Error in invoice monitoring: {e}")


# Global instance
btc_invoice_monitor = BTCInvoiceMonitorWorker()


async def start_btc_invoice_monitor():
    """Start the BTC invoice monitor (call this from main app)."""
    asyncio.create_task(btc_invoice_monitor.start_monitoring())


def stop_btc_invoice_monitor():
    """Stop the BTC invoice monitor."""
    btc_invoice_monitor.stop_monitoring()
