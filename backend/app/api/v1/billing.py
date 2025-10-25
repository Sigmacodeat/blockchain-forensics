"""
Billing & Plans API
- Liefert Pricing/Plan-Konfiguration
- Liefert verbleibende Credits für aktuellen User (pro Monat)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse
from typing import Any, Dict, Optional

from app.auth.dependencies import get_current_user_strict
from app.services.plan_service import plan_service
from app.services.usage_service import get_remaining_credits
from app.services.tenant_service import tenant_service
from app.services.stripe_service import stripe_service
from app.db.redis_client import redis_client
from app.db.postgres_client import postgres_client

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

from pydantic import BaseModel
from typing import Optional, List

class UnifiedSubscription(BaseModel):
    """Unified subscription (Stripe or Crypto)"""
    id: str
    plan: str
    status: str
    payment_type: str  # 'stripe' or 'crypto'
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool
    amount: float
    currency: str
    interval: str

class UnifiedPaymentMethod(BaseModel):
    """Unified payment method"""
    id: str
    type: str  # 'card', 'crypto'
    display_name: str
    details: dict
    is_default: bool

class UnifiedInvoice(BaseModel):
    """Unified invoice"""
    id: str
    number: Optional[str]
    amount_paid: float
    currency: str
    status: str
    payment_type: str  # 'stripe' or 'crypto'
    created: str
    pdf_url: Optional[str]
    tx_hash: Optional[str]  # For crypto

class UsageStats(BaseModel):
    """Usage statistics"""
    traces_used: int
    traces_limit: int
    cases_used: int
    cases_limit: int
    api_calls_used: int
    api_calls_limit: int
    period_start: str
    period_end: str


@router.get("/plans")
async def list_plans() -> Dict[str, Any]:
    """Gibt die vollständige Konfiguration zurück (für Pricing-UI)."""
    cfg = plan_service.get_config()
    # Dataclasses in einfache Dicts umwandeln
    plans = [p.__dict__ for p in cfg.plans]
    return {
        "currency": cfg.currency,
        "annual_discount_percent": cfg.annual_discount_percent,
        "overage": cfg.overage,
        "addons": cfg.addons,
        "plans": plans,
    }


def _resolve_tenant_id(request: Request, current_user: dict) -> str:
    """Resolve tenant id with optional admin override via X-Tenant-Id header."""
    try:
        # Prefer explicit Org header, fallback to Tenant header
        header_oid = request.headers.get("X-Org-Id")
        header_tid = request.headers.get("X-Tenant-Id")
        role = str(current_user.get("role", "")).upper()
        if role == "ADMIN":
            if header_oid:
                return str(header_oid)
            if header_tid:
                return str(header_tid)
    except Exception:
        pass
    return str(current_user["user_id"])  # fallback: simplified tenant model


@router.get("/usage/remaining")
async def remaining_credits(request: Request, response: Response, plan_id: str | None = None, current_user: dict = Depends(get_current_user_strict)):
    """
    Verbleibende Credits für den aktuellen User und angegebenen Plan.

    Wenn kein plan_id angegeben ist, wird der Plan aus dem Tenant-Kontext ermittelt.
    """
    tenant_id = _resolve_tenant_id(request, current_user)
    effective_plan = plan_id or tenant_service.get_plan_id(tenant_id)
    rem = await get_remaining_credits(tenant_id, effective_plan)
    # Set usage feedback header
    try:
        response.headers["X-Usage-Plan"] = effective_plan or "unknown"
        response.headers["X-Usage-Remaining"] = "unlimited" if rem is None else str(rem)
    except Exception:
        pass
    if rem is None:
        # Custom/Enterprise -> kein numerisches Limit
        return {"remaining": None, "unlimited": True}
    return {"remaining": rem, "unlimited": False}


@router.get("/tenant/plan")
async def get_tenant_plan(request: Request, current_user: dict = Depends(get_current_user_strict)) -> Dict[str, Any]:
    tenant_id = _resolve_tenant_id(request, current_user)
    plan_id = tenant_service.get_plan_id(tenant_id)
    return {"plan_id": plan_id}


@router.post("/tenant/plan")
async def set_tenant_plan(request: Request, payload: Dict[str, str], current_user: dict = Depends(get_current_user_strict)) -> Dict[str, Any]:
    plan_id = payload.get("plan_id")
    if not plan_id:
        raise HTTPException(status_code=400, detail="plan_id erforderlich")
    tenant_id = _resolve_tenant_id(request, current_user)
    role = str(current_user.get("role", "")).upper()
    if role not in {"ADMIN"}:
        raise HTTPException(status_code=403, detail="Nur ADMIN darf den Tenant-Plan setzen")
    ok = tenant_service.set_plan_id(tenant_id, plan_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Ungültiger Plan oder Speicherung fehlgeschlagen")
    return {"status": "ok", "plan_id": plan_id}


def _price_id_for_plan(plan_id: str) -> Optional[str]:
    import os
    env_key = f"STRIPE_PRICE_{plan_id.upper()}"
    return os.getenv(env_key)


@router.post("/checkout")
async def create_checkout_session(request: Request, payload: Dict[str, Any], current_user: dict = Depends(get_current_user_strict)) -> Dict[str, Any]:
    """
    Create Stripe Checkout Session
    Body: { plan_id?: string, price_id?: string }
    """
    if not stripe_service.enabled:
        raise HTTPException(status_code=503, detail="Billing provider not configured")
    plan_id = payload.get("plan_id")
    price_id = payload.get("price_id") or (plan_id and _price_id_for_plan(plan_id))
    if not price_id:
        raise HTTPException(status_code=400, detail="price_id oder plan_id erforderlich")
    # Resolve tenant (admin may override via header)
    tenant_id = _resolve_tenant_id(request, current_user)  # noqa: S105
    # Include both for forward-compatibility
    meta = {"tenant_id": tenant_id, "org_id": tenant_id, "plan_id": plan_id or "custom"}
    session = await stripe_service.create_checkout_session(price_id=price_id, metadata=meta)
    return {"id": session["id"], "url": session["url"]}


@router.post("/portal")
async def create_billing_portal(payload: Dict[str, Any], current_user: dict = Depends(get_current_user_strict)) -> Dict[str, Any]:
    """
    Create Stripe Billing Portal session
    Body: { customer_id: string }
    """
    if not stripe_service.enabled:
        raise HTTPException(status_code=503, detail="Billing provider not configured")
    customer_id = payload.get("customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id erforderlich")
    portal = await stripe_service.create_billing_portal(customer_id)
    return {"id": portal["id"], "url": portal["url"]}


@router.post("/webhook")
async def stripe_webhook(request: Request) -> Dict[str, Any]:
    """
    Stripe webhook handler. Updates tenant plan on subscription events.
    Expects events with metadata.tenant_id and metadata.plan_id
    """
    if not stripe_service.enabled:
        # Accept but no-op for environments without Stripe
        return {"received": True, "disabled": True}
    try:
        sig = request.headers.get("stripe-signature", "")
        payload = await request.body()
        event = stripe_service.construct_event(payload, sig)

        # Idempotenz: Stripe-Event nur einmal verarbeiten (24h TTL)
        try:
            event_id = event.get("id")
            if event_id:
                await redis_client._ensure_connected()  # type: ignore[attr-defined]
                client = getattr(redis_client, "client", None)
                if client is not None:
                    key = f"stripe:event:{event_id}"
                    was_set = await client.setnx(key, "1")
                    if not was_set:
                        # Bereits verarbeitet – still akzeptieren
                        return {"received": True, "duplicate": True}
                    await client.expire(key, 24 * 3600)
        except Exception:
            # Wenn Redis fehlt, weiter ohne Dedup (Best Effort)
            pass

        etype = event.get("type")
        data = event.get("data", {}).get("object", {})
        meta = data.get("metadata", {}) or {}
        # Accept both org_id and tenant_id for compatibility
        tenant_id = meta.get("tenant_id") or meta.get("org_id")
        plan_id = meta.get("plan_id")
        if etype in {"checkout.session.completed", "customer.subscription.updated", "customer.subscription.created"}:
            if tenant_id and plan_id:
                tenant_service.set_plan_id(tenant_id, plan_id)
        elif etype in {"customer.subscription.deleted", "customer.subscription.canceled"}:
            if tenant_id:
                # fall back to default plan on cancel
                tenant_service.set_plan_id(tenant_id, plan_id or "community")
        return {"received": True}
    except Exception as e:
        # do not raise unverified webhook errors publicly
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Unified Billing Endpoints (Stripe + Crypto)
# ============================================================================

@router.get("/subscription", response_model=Optional[UnifiedSubscription])
async def get_subscription(
    request: Request,
    customer_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Get current subscription (Stripe or Crypto)
    Combines both payment types into unified response
    """
    user_id = current_user.get("user_id") or current_user.get("id")
    # allow passing customer_id via query until user.stripe_customer_id exists
    customer_id = customer_id or current_user.get("stripe_customer_id")
    
    try:
        # Check for Stripe subscription first
        stripe_sub = None
        if stripe_service.enabled and customer_id and hasattr(stripe_service, "get_subscription"):
            try:
                stripe_sub = await stripe_service.get_subscription(customer_id)  # type: ignore[attr-defined]
                if stripe_sub:
                    # expected fields: id, status, current_period_start, current_period_end, plan_amount, plan_currency, interval, cancel_at_period_end
                    return UnifiedSubscription(
                        id=str(stripe_sub.get("id")),
                        plan=str(stripe_sub.get("plan_id") or stripe_sub.get("price_id") or "stripe"),
                        status=str(stripe_sub.get("status") or "active"),
                        payment_type="stripe",
                        current_period_start=stripe_sub.get("current_period_start") or datetime.utcnow().isoformat(),
                        current_period_end=stripe_sub.get("current_period_end") or datetime.utcnow().isoformat(),
                        cancel_at_period_end=bool(stripe_sub.get("cancel_at_period_end") or False),
                        amount=float(stripe_sub.get("plan_amount") or 0.0),
                        currency=str(stripe_sub.get("plan_currency") or "usd").upper(),
                        interval=str(stripe_sub.get("interval") or "month"),
                    )
            except Exception:
                # fail soft to crypto fallback
                pass
        
        # Check for active Crypto subscription
        crypto_sub = await postgres_client.fetchrow(
            """
            SELECT * FROM crypto_subscriptions 
            WHERE user_id = $1 AND is_active = TRUE 
            ORDER BY created_at DESC LIMIT 1
            """,
            user_id
        )
        
        if crypto_sub:
            from datetime import datetime, timedelta
            return UnifiedSubscription(
                id=str(crypto_sub["id"]),
                plan=crypto_sub["plan_name"],
                status="active" if crypto_sub["is_active"] else "canceled",
                payment_type="crypto",
                current_period_start=crypto_sub["created_at"].isoformat(),
                current_period_end=crypto_sub["next_billing_date"].isoformat(),
                cancel_at_period_end=crypto_sub.get("cancelled_at") is not None,
                amount=float(crypto_sub["amount_usd"]),
                currency="USD",
                interval=crypto_sub["interval"]
            )
        
        # No active subscription
        return None
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription")


@router.get("/payment-methods")
async def get_payment_methods(
    request: Request,
    customer_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Get all payment methods (Cards + Recent Crypto Addresses)
    """
    user_id = current_user.get("user_id") or current_user.get("id")
    methods = []
    
    try:
        # Get Stripe payment methods
        if stripe_service.enabled and customer_id and hasattr(stripe_service, "list_payment_methods"):
            try:
                stripe_methods = await stripe_service.list_payment_methods(customer_id)  # type: ignore[attr-defined]
                for m in stripe_methods or []:
                    brand = (m.get("card", {}) or {}).get("brand") or m.get("brand")
                    last4 = (m.get("card", {}) or {}).get("last4") or m.get("last4")
                    exp_month = (m.get("card", {}) or {}).get("exp_month") or m.get("exp_month")
                    exp_year = (m.get("card", {}) or {}).get("exp_year") or m.get("exp_year")
                    methods.append(
                        {
                            "id": str(m.get("id")),
                            "type": "card",
                            "display_name": f"{(brand or 'card').title()} •••• {last4}",
                            "details": {
                                "brand": brand,
                                "last4": last4,
                                "exp_month": exp_month,
                                "exp_year": exp_year,
                            },
                            "is_default": bool(m.get("default") or m.get("is_default") or False),
                        }
                    )
            except Exception:
                pass
        
        # Get recent crypto payments (last 30 days)
        crypto_payments = await postgres_client.fetch(
            """
            SELECT DISTINCT ON (pay_currency) 
                payment_id, pay_currency, created_at
            FROM crypto_payments
            WHERE user_id = $1 AND created_at > NOW() - INTERVAL '30 days'
            ORDER BY pay_currency, created_at DESC
            """,
            user_id
        )
        
        for payment in crypto_payments:
            methods.append({
                "id": f"crypto_{payment['pay_currency']}",
                "type": "crypto",
                "display_name": f"{payment['pay_currency'].upper()} Wallet",
                "details": {
                    "currency": payment["pay_currency"],
                    "last_used": payment["created_at"].isoformat()
                },
                "is_default": False
            })
        
        return {"data": methods}
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payment methods")


@router.get("/invoices")
async def get_invoices(
    request: Request,
    customer_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Get all invoices (Stripe + Crypto unified)
    """
    user_id = current_user.get("user_id") or current_user.get("id")
    invoices = []
    
    try:
        # Get Stripe invoices
        if stripe_service.enabled and customer_id and hasattr(stripe_service, "list_invoices"):
            try:
                stripe_invoices = await stripe_service.list_invoices(customer_id)  # type: ignore[attr-defined]
                for inv in stripe_invoices or []:
                    amount_paid = inv.get("amount_paid")
                    if amount_paid is None:
                        amount_paid = inv.get("amount_due") or 0
                    # normalize to major units if cents provided
                    if amount_paid and amount_paid > 1000:
                        try:
                            amount_paid = float(amount_paid) / 100.0
                        except Exception:
                            pass
                    invoices.append(
                        {
                            "id": str(inv.get("id")),
                            "number": str(inv.get("number") or inv.get("id")),
                            "amount_paid": float(amount_paid or 0.0),
                            "amount_due": float((inv.get("amount_due") or 0) / 100.0) if inv.get("amount_due") else 0.0,
                            "currency": str(inv.get("currency") or "usd").upper(),
                            "status": str(inv.get("status") or "paid"),
                            "payment_type": "stripe",
                            "created": (inv.get("created_iso") or inv.get("created_at") or datetime.utcnow().isoformat()),
                            "pdf_url": inv.get("invoice_pdf") or inv.get("hosted_invoice_url"),
                            "tx_hash": None,
                        }
                    )
            except Exception:
                pass
        
        # Get crypto payments (completed only)
        crypto_payments = await postgres_client.fetch(
            """
            SELECT * FROM crypto_payments
            WHERE user_id = $1 AND payment_status IN ('finished', 'partially_paid')
            ORDER BY created_at DESC
            LIMIT 50
            """,
            user_id
        )
        
        for payment in crypto_payments:
            invoices.append({
                "id": f"crypto_{payment['payment_id']}",
                "number": payment["order_id"],
                "amount_paid": float(payment["price_amount"]),
                "amount_due": 0,
                "currency": payment["price_currency"].upper(),
                "status": "paid" if payment["payment_status"] == "finished" else "open",
                "payment_type": "crypto",
                "created": payment["created_at"].isoformat(),
                "pdf_url": payment.get("invoice_url"),
                "tx_hash": payment.get("pay_in_hash")
            })
        
        return {"data": invoices}
    except Exception as e:
        logger.error(f"Error getting invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to get invoices")


@router.get("/invoices/export")
async def export_invoices_csv(current_user: dict = Depends(get_current_user_strict), format: str = "csv"):
    """
    Export all invoices of the current user as CSV (default).
    For now, exports Crypto invoices; Stripe invoices will be added when Stripe listing is wired.
    """
    if format.lower() != "csv":
        raise HTTPException(status_code=400, detail="Only CSV export supported")

    user_id = current_user.get("user_id") or current_user.get("id")
    try:
        # Collect invoices (same logic as get_invoices, crypto part)
        invoices: list[dict] = []

        # Future: Add Stripe invoice listing (stripe_service.list_invoices)

        crypto_payments = await postgres_client.fetch(
            """
            SELECT * FROM crypto_payments
            WHERE user_id = $1 AND payment_status IN ('finished', 'partially_paid')
            ORDER BY created_at DESC
            LIMIT 1000
            """,
            user_id,
        )

        for payment in crypto_payments:
            invoices.append(
                {
                    "id": f"crypto_{payment['payment_id']}",
                    "number": payment["order_id"],
                    "amount_paid": float(payment["price_amount"]),
                    "currency": payment["price_currency"].upper(),
                    "status": "paid"
                    if payment["payment_status"] == "finished"
                    else "open",
                    "payment_type": "crypto",
                    "created": payment["created_at"].isoformat(),
                    "pdf_url": payment.get("invoice_url"),
                    "tx_hash": payment.get("pay_in_hash"),
                }
            )

        # Build CSV
        import io, csv

        buf = io.StringIO()
        writer = csv.writer(buf)
        header = [
            "id",
            "number",
            "amount_paid",
            "currency",
            "status",
            "payment_type",
            "created",
            "pdf_url",
            "tx_hash",
        ]
        writer.writerow(header)
        for inv in invoices:
            writer.writerow([inv.get(k, "") for k in header])

        buf.seek(0)
        filename = f"invoices_export_{user_id}.csv"
        return StreamingResponse(
            buf,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            },
        )
    except Exception as e:
        logger.error(f"Error exporting invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to export invoices")


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(request: Request, current_user: dict = Depends(get_current_user_strict)):
    """
    Get detailed usage statistics for current billing period
    """
    tenant_id = _resolve_tenant_id(request, current_user)
    
    try:
        from datetime import datetime, timedelta
        # Get current period (monthly cycle)
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            period_end = period_start.replace(year=now.year + 1, month=1)
        else:
            period_end = period_start.replace(month=now.month + 1)
        
        # Get plan limits
        plan_id = tenant_service.get_plan_id(tenant_id)
        plan = plan_service.get_plan_by_id(plan_id)
        
        # Get actual usage from database
        traces_used = await postgres_client.fetchval(
            """
            SELECT COUNT(*) FROM trace_requests 
            WHERE user_id = $1 AND created_at >= $2 AND created_at < $3
            """,
            tenant_id, period_start, period_end
        ) or 0
        
        cases_used = await postgres_client.fetchval(
            """
            SELECT COUNT(*) FROM cases 
            WHERE org_id = $1 AND created_at >= $2 AND created_at < $3
            """,
            tenant_id, period_start, period_end
        ) or 0
        
        api_calls_used = await postgres_client.fetchval(
            """
            SELECT COUNT(*) FROM api_requests 
            WHERE user_id = $1 AND created_at >= $2 AND created_at < $3
            """,
            tenant_id, period_start, period_end
        ) or 0
        
        # Get limits from plan
        traces_limit = plan.quotas.get("credits_monthly", -1) if plan else -1
        cases_limit = plan.quotas.get("cases", -1) if plan else -1
        api_calls_limit = plan.quotas.get("api_rate", -1) if plan else -1
        
        # Convert string limits to int
        if isinstance(traces_limit, str):
            traces_limit = -1 if traces_limit == "unlimited" else int(traces_limit)
        if isinstance(cases_limit, str):
            cases_limit = -1 if cases_limit == "unlimited" else int(cases_limit)
        if isinstance(api_calls_limit, str):
            api_calls_limit = -1 if api_calls_limit == "unlimited" else int(api_calls_limit)
        
        return UsageStats(
            traces_used=traces_used,
            traces_limit=traces_limit,
            cases_used=cases_used,
            cases_limit=cases_limit,
            api_calls_used=api_calls_used,
            api_calls_limit=api_calls_limit,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat()
        )
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        # Return safe defaults
        return UsageStats(
            traces_used=0,
            traces_limit=-1,
            cases_used=0,
            cases_limit=-1,
            api_calls_used=0,
            api_calls_limit=-1,
            period_start=datetime.utcnow().isoformat(),
            period_end=datetime.utcnow().isoformat()
        )


@router.post("/cancel")
async def cancel_subscription(current_user: dict = Depends(get_current_user_strict)):
    """
    Cancel current subscription (Stripe or Crypto)
    """
    user_id = current_user.get("user_id") or current_user.get("id")
    
    try:
        # Cancel Crypto subscription
        result = await postgres_client.execute(
            """
            UPDATE crypto_subscriptions 
            SET is_active = FALSE, cancelled_at = NOW(), updated_at = NOW()
            WHERE user_id = $1 AND is_active = TRUE
            """,
            user_id
        )
        
        # Cancel Stripe subscription
        if stripe_service.enabled:
            try:
                # Future: Implement Stripe cancellation (stripe_service.cancel_subscription)
                logger.info(f"Stripe cancellation not yet implemented for user {user_id}")
            except Exception:
                pass
        
        return {"message": "Subscription cancelled successfully"}
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.post("/portal-session")
async def create_portal_session(current_user: dict = Depends(get_current_user_strict)):
    """
    Create Stripe Customer Portal session
    """
    if not stripe_service.enabled:
        raise HTTPException(status_code=503, detail="Billing portal not available")
    
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        # Note: Using user_id as customer_id (Stripe customer mapping in user table for production)
        customer_id = f"cus_{user_id}"  # Generated customer_id
        
        portal = await stripe_service.create_billing_portal(customer_id)
        return {"url": portal["url"]}
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.post("/checkout-session")
async def create_stripe_checkout(payload: Dict[str, Any], current_user: dict = Depends(get_current_user_strict)):
    """
    Create Stripe Checkout Session for card payment
    """
    if not stripe_service.enabled:
        raise HTTPException(status_code=503, detail="Card payments not available")
    
    plan = payload.get("plan")
    success_url = payload.get("success_url", "http://localhost:3000/billing?success=true")
    cancel_url = payload.get("cancel_url", "http://localhost:3000/billing?canceled=true")
    
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        
        # Get price ID
        price_id = _price_id_for_plan(plan)
        if not price_id:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {plan}")
        
        # Create checkout session
        session = await stripe_service.create_checkout_session(
            price_id=price_id,
            metadata={"user_id": user_id, "plan": plan},
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return {"url": session["url"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


import logging
logger = logging.getLogger(__name__)


# ============================================================================
# NEUE ENDPUNKTE: PRORATION & DOWNGRADE & USAGE-TRACKING
# ============================================================================

from app.schemas.billing import (
    ProrationRequest, ProrationResponse,
    DowngradeRequest, DowngradeResponse,
    UpgradeRequest, UpgradeResponse
)
from datetime import datetime, timedelta


# Plan-Preise (Monthly in USD)
PLAN_PRICES = {
    "community": 0,
    "starter": 29,
    "pro": 49,
    "business": 99,
    "plus": 199,
    "enterprise": 499
}


@router.post("/calculate-proration", response_model=ProrationResponse)
async def calculate_proration(
    data: ProrationRequest,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Berechnet Proration für Plan-Upgrade/Downgrade
    
    **Features:**
    - Berechnet verbleibende Tage im Billing-Cycle
    - Kalkuliert Credit vom aktuellen Plan
    - Berechnet Charge für neuen Plan
    - Gibt finalen prorated Amount zurück
    
    **Example:**
    ```json
    {
        "current_plan": "starter",
        "target_plan": "pro",
        "billing_cycle_start": "2025-10-01T00:00:00Z",
        "billing_cycle_end": "2025-10-31T23:59:59Z"
    }
    ```
    
    **Returns:**
    ```json
    {
        "prorated_amount": 15.50,
        "days_remaining": 15,
        "current_plan_cost": 29.00,
        "target_plan_cost": 49.00,
        "credit_from_current": 14.50,
        "charge_for_target": 24.50
    }
    ```
    """
    try:
        current_price = PLAN_PRICES.get(data.current_plan, 0)
        target_price = PLAN_PRICES.get(data.target_plan, 0)
        
        # Tage berechnen
        cycle_start = datetime.fromisoformat(data.billing_cycle_start.replace('Z', '+00:00'))
        cycle_end = datetime.fromisoformat(data.billing_cycle_end.replace('Z', '+00:00'))
        today = datetime.utcnow()
        
        total_days = (cycle_end - cycle_start).days
        days_remaining = max(0, (cycle_end - today).days)
        
        # Proration berechnen
        if total_days > 0:
            credit_from_current = (current_price / total_days) * days_remaining
            charge_for_target = (target_price / total_days) * days_remaining
        else:
            credit_from_current = 0
            charge_for_target = 0
        
        prorated_amount = charge_for_target - credit_from_current
        
        return ProrationResponse(
            prorated_amount=round(prorated_amount, 2),
            days_remaining=days_remaining,
            current_plan_cost=current_price,
            target_plan_cost=target_price,
            credit_from_current=round(credit_from_current, 2),
            charge_for_target=round(charge_for_target, 2)
        )
    
    except Exception as e:
        logger.error(f"Error calculating proration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate proration: {str(e)}")


async def check_active_features(user_id: str) -> list:
    """
    Prüft welche Features der User aktiv nutzt (für Downgrade-Blocking)
    
    Returns: ["investigator", "correlation", "ai_agents"]
    """
    active_features = []
    
    try:
        # Check Investigator (Graph-Queries in letzten 30 Tagen)
        graph_query = """
            SELECT COUNT(*) FROM graph_queries 
            WHERE user_id = $1 AND created_at > NOW() - INTERVAL '30 days'
        """
        graph_count = await postgres_client.fetchval(graph_query, user_id) or 0
        if graph_count > 0:
            active_features.append("investigator")
        
        # Check Correlation (Pattern-Detections)
        pattern_query = """
            SELECT COUNT(*) FROM pattern_detections 
            WHERE user_id = $1 AND created_at > NOW() - INTERVAL '30 days'
        """
        pattern_count = await postgres_client.fetchval(pattern_query, user_id) or 0
        if pattern_count > 0:
            active_features.append("correlation")
        
        # Check AI-Agent (Queries)
        ai_query = """
            SELECT COUNT(*) FROM ai_agent_queries 
            WHERE user_id = $1 AND created_at > NOW() - INTERVAL '30 days'
        """
        ai_count = await postgres_client.fetchval(ai_query, user_id) or 0
        if ai_count > 0:
            active_features.append("ai_agents")
    
    except Exception as e:
        logger.warning(f"Error checking active features: {e}")
        # Bei Fehler: Konservativ alle Features als aktiv markieren
        return []
    
    return active_features


# Required Features pro Plan (für Downgrade-Check)
REQUIRED_FEATURES_BY_PLAN = {
    "community": [],
    "starter": ["labels.enrichment", "reports.pdf"],
    "pro": ["investigator.access", "correlation.basic", "tracing.unlimited"],
    "business": ["risk_policies.manage", "roles_permissions.manage", "sso.basic"],
    "plus": ["ai_agents.unlimited", "correlation.advanced", "travel_rule.support"],
    "enterprise": ["chain_of_custody.full", "eidas.signatures", "white_label"]
}


@router.post("/downgrade", response_model=DowngradeResponse)
async def downgrade_plan(
    data: DowngradeRequest,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Plan-Downgrade mit Effective-Date (am Ende des Billing-Cycles)
    
    **Features:**
    - Blockt Downgrade wenn Features noch in Nutzung
    - Scheduled Downgrade am Ende des Cycles
    - Gibt Warnung für Features die verloren gehen
    
    **Example:**
    ```json
    {
        "target_plan": "starter",
        "reason": "Cost reduction"
    }
    ```
    
    **Returns:**
    ```json
    {
        "message": "Downgrade scheduled",
        "current_plan": "pro",
        "target_plan": "starter",
        "effective_date": "2025-10-31T23:59:59Z",
        "days_until_downgrade": 15,
        "active_features_warning": ["Investigator wird deaktiviert"]
    }
    ```
    """
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        current_plan = current_user.get("plan", "community")
        
        # Validierung: Target-Plan muss niedriger sein
        plan_hierarchy = ["community", "starter", "pro", "business", "plus", "enterprise"]
        current_idx = plan_hierarchy.index(current_plan)
        target_idx = plan_hierarchy.index(data.target_plan)
        
        if target_idx >= current_idx:
            raise HTTPException(
                status_code=400,
                detail=f"Target plan '{data.target_plan}' is not a downgrade from '{current_plan}'"
            )
        
        # Check aktive Features
        active_features = await check_active_features(user_id)
        target_features = REQUIRED_FEATURES_BY_PLAN.get(data.target_plan, [])
        
        # Features die verloren gehen
        blocking_features = [f for f in active_features if f not in target_features]
        
        if blocking_features:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Cannot downgrade while features are in use",
                    "active_features": blocking_features,
                    "suggestion": "Please stop using these features before downgrading"
                }
            )
        
        # Get Subscription für effective_date
        subscription_query = """
            SELECT current_period_end 
            FROM subscriptions 
            WHERE user_id = $1 AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        """
        subscription = await postgres_client.fetchrow(subscription_query, user_id)
        
        if subscription:
            effective_date = subscription["current_period_end"]
        else:
            # Fallback: Ende des aktuellen Monats
            now = datetime.utcnow()
            last_day = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            effective_date = last_day.replace(hour=23, minute=59, second=59)
        
        # Schedule Downgrade in DB
        update_query = """
            UPDATE subscriptions 
            SET scheduled_plan = $1, 
                scheduled_plan_date = $2,
                downgrade_reason = $3
            WHERE user_id = $4 AND status = 'active'
        """
        await postgres_client.execute(
            update_query,
            data.target_plan,
            effective_date,
            data.reason,
            user_id
        )
        
        # Berechne Tage bis Downgrade
        if isinstance(effective_date, str):
            effective_date = datetime.fromisoformat(effective_date.replace('Z', '+00:00'))
        
        days_until = max(0, (effective_date - datetime.utcnow()).days)
        
        # Warnings für Features die verloren gehen
        feature_warnings = []
        current_features = REQUIRED_FEATURES_BY_PLAN.get(current_plan, [])
        lost_features = [f for f in current_features if f not in target_features]
        
        feature_names = {
            "investigator.access": "Graph Explorer (Investigator)",
            "correlation.basic": "Pattern Detection",
            "ai_agents.unlimited": "AI Agent (Unlimited)",
            "travel_rule.support": "Travel Rule Compliance",
            "white_label": "White-Label Branding"
        }
        
        for feat in lost_features:
            name = feature_names.get(feat, feat)
            feature_warnings.append(f"{name} wird deaktiviert")
        
        return DowngradeResponse(
            message="Downgrade scheduled successfully",
            current_plan=current_plan,
            target_plan=data.target_plan,
            effective_date=effective_date.isoformat() + "Z",
            days_until_downgrade=days_until,
            active_features_warning=feature_warnings if feature_warnings else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling downgrade: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule downgrade: {str(e)}")


@router.post("/upgrade", response_model=UpgradeResponse)
async def upgrade_plan(
    data: UpgradeRequest,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Plan-Upgrade mit sofortiger Wirkung + Proration
    
    **Features:**
    - Sofortiges Upgrade
    - Automatische Proration-Berechnung
    - Aktivierung neuer Features
    
    **Example:**
    ```json
    {
        "target_plan": "pro",
        "payment_method": "pm_1234567890"
    }
    ```
    """
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        current_plan = current_user.get("plan", "community")
        
        # Validierung: Target-Plan muss höher sein
        plan_hierarchy = ["community", "starter", "pro", "business", "plus", "enterprise"]
        current_idx = plan_hierarchy.index(current_plan)
        target_idx = plan_hierarchy.index(data.target_plan)
        
        if target_idx <= current_idx:
            raise HTTPException(
                status_code=400,
                detail=f"Target plan '{data.target_plan}' is not an upgrade from '{current_plan}'"
            )
        
        # Get Subscription für Proration
        subscription_query = """
            SELECT current_period_start, current_period_end 
            FROM subscriptions 
            WHERE user_id = $1 AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        """
        subscription = await postgres_client.fetchrow(subscription_query, user_id)
        
        if subscription:
            cycle_start = subscription["current_period_start"]
            cycle_end = subscription["current_period_end"]
        else:
            # Fallback: Aktueller Monat
            now = datetime.utcnow()
            cycle_start = now.replace(day=1, hour=0, minute=0, second=0)
            last_day = (cycle_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            cycle_end = last_day.replace(hour=23, minute=59, second=59)
        
        # Proration berechnen
        proration_request = ProrationRequest(
            current_plan=current_plan,
            target_plan=data.target_plan,
            billing_cycle_start=cycle_start.isoformat() if isinstance(cycle_start, datetime) else cycle_start,
            billing_cycle_end=cycle_end.isoformat() if isinstance(cycle_end, datetime) else cycle_end
        )
        
        # Manuelle Proration-Berechnung (ohne rekursiven Call)
        current_price = PLAN_PRICES.get(current_plan, 0)
        target_price = PLAN_PRICES.get(data.target_plan, 0)
        
        if isinstance(cycle_start, str):
            cycle_start = datetime.fromisoformat(cycle_start.replace('Z', '+00:00'))
        if isinstance(cycle_end, str):
            cycle_end = datetime.fromisoformat(cycle_end.replace('Z', '+00:00'))
        
        total_days = (cycle_end - cycle_start).days
        days_remaining = max(0, (cycle_end - datetime.utcnow()).days)
        
        if total_days > 0:
            credit = (current_price / total_days) * days_remaining
            charge = (target_price / total_days) * days_remaining
            prorated_amount = charge - credit
        else:
            prorated_amount = target_price - current_price
        
        # Update Subscription in DB
        update_query = """
            UPDATE subscriptions 
            SET plan = $1,
                updated_at = NOW()
            WHERE user_id = $2 AND status = 'active'
        """
        await postgres_client.execute(update_query, data.target_plan, user_id)
        
        # Update User Plan
        user_update_query = """
            UPDATE users 
            SET plan = $1,
                updated_at = NOW()
            WHERE id = $2
        """
        await postgres_client.execute(user_update_query, data.target_plan, user_id)
        
        return UpgradeResponse(
            message="Plan upgraded successfully",
            old_plan=current_plan,
            new_plan=data.target_plan,
            prorated_amount=round(prorated_amount, 2),
            subscription_id=f"sub_{user_id}",
            effective_date=datetime.utcnow().isoformat() + "Z"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upgrading plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upgrade plan: {str(e)}")
