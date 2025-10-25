"""
Stripe Service
Safely integrates Stripe Checkout/Portal/Webhooks with lazy imports and optional enablement.
"""
from __future__ import annotations
import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class StripeService:
    def __init__(self):
        self.enabled = bool(os.getenv("STRIPE_SECRET"))
        self._stripe = None
        if self.enabled:
            try:
                import stripe  # type: ignore
                stripe.api_key = os.getenv("STRIPE_SECRET")
                self._stripe = stripe
            except Exception as e:
                logger.warning(f"Stripe import failed: {e}")
                self.enabled = False

    def _base_url(self) -> str:
        return os.getenv("PUBLIC_BASE_URL", "http://localhost:3000")

    def _success_url(self) -> str:
        return os.getenv("STRIPE_SUCCESS_URL", f"{self._base_url()}/billing/success")

    def _cancel_url(self) -> str:
        return os.getenv("STRIPE_CANCEL_URL", f"{self._base_url()}/billing/cancel")

    def _portal_return_url(self) -> str:
        return os.getenv("STRIPE_PORTAL_RETURN_URL", f"{self._base_url()}/billing")

    async def create_checkout_session(self, price_id: str, customer_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.enabled or not self._stripe:
            raise RuntimeError("Stripe not configured")
        session = self._stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=self._success_url() + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=self._cancel_url(),
            customer=customer_id,
            metadata=metadata or {},
            allow_promotion_codes=True,
        )
        return {"id": session.get("id"), "url": session.get("url")}

    async def create_billing_portal(self, customer_id: str) -> Dict[str, Any]:
        if not self.enabled or not self._stripe:
            raise RuntimeError("Stripe not configured")
        portal = self._stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=self._portal_return_url(),
        )
        return {"id": portal.get("id"), "url": portal.get("url")}

    def construct_event(self, payload: bytes, sig_header: str) -> Any:
        if not self.enabled or not self._stripe:
            raise RuntimeError("Stripe not configured")
        wh_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not wh_secret:
            raise RuntimeError("Stripe webhook secret missing")
        return self._stripe.Webhook.construct_event(payload, sig_header, wh_secret)


stripe_service = StripeService()
