"""
BTC Invoice Payment Monitor Worker
Monitors pending invoices and matches payments via Esplora API.
"""

import asyncio
import logging
from datetime import datetime
from app.services.btc_invoice_service import btc_invoice_service
from app.config import settings

logger = logging.getLogger(__name__)


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
                await self._check_pending_invoices()
            except Exception as e:
                logger.error(f"Invoice monitoring error: {e}")

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
                    status = btc_invoice_service.check_payment_status(invoice["order_id"])
                    if status["status"] in ["paid", "expired"]:
                        updated_count += 1
                        logger.info(f"Invoice {invoice['order_id']} status: {status['status']}")
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
