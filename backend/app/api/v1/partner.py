"""
Partner / Affiliate API
- Account & Referral-Link
- Commissions Übersicht
- Referrals Übersicht
- Payout Requests
"""
from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.auth.dependencies import require_roles, require_admin
from app.auth.models import UserRole
from app.db.postgres_client import postgres_client
from app.services.partner_service import partner_service
from app.config import settings
from app.auth.jwt import get_password_hash
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.services.notification_service_premium import PremiumNotificationService
from app.models.user import UserORM
import io
import csv

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/partner", tags=["Partner"])


@router.get("/account")
async def get_or_create_partner_account(user: dict = Depends(require_roles([UserRole.PARTNER, UserRole.ADMIN]))):
    """
    Liefert den Partner-Account des aktuellen Users
    Falls nicht vorhanden: wird automatisch erzeugt.
    """
    try:
        acct = await partner_service.ensure_partner_account(user_id=str(user["user_id"]))
        # Stats laden
        stats = {
            "pending": 0.0,
            "approved": 0.0,
            "paid": 0.0,
            "total": 0.0,
        }
        try:
            rows = await postgres_client.fetch(
                """
                SELECT status, COALESCE(SUM(commission_usd),0) AS sum
                FROM partner_commissions
                WHERE partner_id = $1
                GROUP BY status
                """,
                acct["id"],
            )
            for r in rows or []:
                stats[str(r["status"]) or "pending"] = float(r["sum"] or 0)
            stats["total"] = sum(stats.values())
        except Exception:
            pass
        # Referral URL bereitstellen (für Onboarding/Sharing)
        try:
            base = getattr(settings, "FRONTEND_URL", "") or ""
            referral_url = f"{base.rstrip('/')}/register?ref={acct.get('referral_code')}" if base else None
        except Exception:
            referral_url = None
        return {"account": acct, "stats": stats, "referral_url": referral_url}
    except Exception as e:
        logger.error(f"get_or_create_partner_account failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load partner account")


@router.get("/commissions")
async def list_commissions(
    status: Optional[str] = Query(None, description="Filter: pending, approved, paid, canceled"),
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(require_roles([UserRole.PARTNER, UserRole.ADMIN]))
):
    """Liste von Kommissionen für aktuellen Partner."""
    try:
        acct = await partner_service.ensure_partner_account(user_id=str(user["user_id"]))
        if status:
            rows = await postgres_client.fetch(
                """
                SELECT * FROM partner_commissions
                WHERE partner_id = $1 AND status = $2
                ORDER BY event_time DESC
                LIMIT $3 OFFSET $4
                """,
                acct["id"], status, limit, offset,
            )
        else:
            rows = await postgres_client.fetch(
                """
                SELECT * FROM partner_commissions
                WHERE partner_id = $1
                ORDER BY event_time DESC
                LIMIT $2 OFFSET $3
                """,
                acct["id"], limit, offset,
            )
        total = await postgres_client.fetchval(
            "SELECT COUNT(*) FROM partner_commissions WHERE partner_id = $1" + (" AND status = $2" if status else ""),
            acct["id"], status,
        ) if status else await postgres_client.fetchval(
            "SELECT COUNT(*) FROM partner_commissions WHERE partner_id = $1",
            acct["id"],
        )
        return {"data": [dict(r) for r in rows or []], "total": total or 0}
    except Exception as e:
        logger.error(f"list_commissions failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list commissions")


@router.get("/referrals")
async def list_referrals(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(require_roles([UserRole.PARTNER, UserRole.ADMIN]))
):
    """Liste der referenzierten Nutzer."""
    try:
        acct = await partner_service.ensure_partner_account(user_id=str(user["user_id"]))
        rows = await postgres_client.fetch(
            """
            SELECT pr.*, u.email AS user_email
            FROM partner_referrals pr
            LEFT JOIN users u ON u.id = pr.referred_user_id
            WHERE pr.partner_id = $1
            ORDER BY pr.created_at DESC
            LIMIT $2 OFFSET $3
            """,
            acct["id"], limit, offset,
        )
        total = await postgres_client.fetchval(
            "SELECT COUNT(*) FROM partner_referrals WHERE partner_id = $1",
            acct["id"],
        )
        return {"data": [dict(r) for r in rows or []], "total": total or 0}
    except Exception as e:
        logger.error(f"list_referrals failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list referrals")


from pydantic import BaseModel, Field

class PayoutRequest(BaseModel):
    amount_usd: float = Field(..., gt=0, description="Auszahlungsbetrag in USD")


@router.post("/payouts/request")
async def request_payout(
    body: PayoutRequest,
    user: dict = Depends(require_roles([UserRole.PARTNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Erstellt eine Auszahlungsanfrage, wenn Mindestbetrag erreicht ist."""
    try:
        acct = await partner_service.ensure_partner_account(user_id=str(user["user_id"]))
        min_amount = float(acct.get("min_payout_usd") or 50.0)
        if body.amount_usd < min_amount:
            raise HTTPException(status_code=400, detail=f"Mindestbetrag für Auszahlung: {min_amount} USD")
        # Prüfe verfügbares pending/approved-Guthaben
        sums = await postgres_client.fetch(
            """
            SELECT status, COALESCE(SUM(commission_usd),0) AS sum
            FROM partner_commissions
            WHERE partner_id = $1 AND status IN ('pending','approved')
            GROUP BY status
            """,
            acct["id"],
        )
        available = 0.0
        for s in sums or []:
            available += float(s["sum"] or 0)
        if body.amount_usd > available:
            raise HTTPException(status_code=400, detail=f"Nicht genügend verfügbares Guthaben ({available:.2f} USD)")
        row = await postgres_client.fetchrow(
            """
            INSERT INTO partner_payouts (partner_id, amount_usd, status)
            VALUES ($1, $2, 'requested')
            RETURNING *
            """,
            acct["id"], body.amount_usd,
        )
        # Notifications (best-effort): Partner + Admins
        try:
            pns = PremiumNotificationService(db)
            # Partner user_id auflösen
            partner_user = await postgres_client.fetchrow("SELECT user_id FROM partner_accounts WHERE id = $1", acct["id"])  # type: ignore
            if partner_user and partner_user.get("user_id"):
                await pns.send_notification(
                    user_id=str(partner_user["user_id"]),
                    title="Auszahlung angefragt",
                    message=f"Ihre Auszahlungsanfrage über ${body.amount_usd:.2f} wurde erstellt.",
                    type="payment",
                    priority="normal",
                    action_url=f"{settings.FRONTEND_URL}/partner" if getattr(settings, "FRONTEND_URL", None) else None,
                    metadata={"payout_id": str(row["id"]) if row else None, "amount_usd": float(body.amount_usd)},
                )
            # Admin informieren
            admins = db.query(UserORM).filter(UserORM.role == 'admin', UserORM.is_active == True).limit(10).all()
            for adm in admins:
                try:
                    await pns.send_notification(
                        user_id=str(adm.id),
                        title="Neue Partner-Auszahlungsanfrage",
                        message=f"Partner payout request ${body.amount_usd:.2f} wartet auf Prüfung.",
                        type="payment",
                        priority="high",
                        action_url=f"{settings.FRONTEND_URL}/admin/partners" if getattr(settings, "FRONTEND_URL", None) else None,
                        metadata={"payout_id": str(row["id"]) if row else None, "partner_id": acct["id"]},
                    )
                except Exception:
                    continue
        except Exception:
            pass
        return {"payout": dict(row) if row else None}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"request_payout failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to request payout")


# =============================
# Partner-Clients (Onboarding)
# =============================

class CreateClientRequest(BaseModel):
    email: str
    username: Optional[str] = None
    plan: Optional[str] = Field("community", description="Initialer Plan des Kunden (default: community)")
    role: Optional[str] = Field("viewer", description="Rolle des Kunden (viewer/analyst; default: viewer)")


@router.get("/clients")
async def list_clients(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(require_roles([UserRole.PARTNER, UserRole.ADMIN]))
):
    """Liste der Kunden, die diesem Partner zugeordnet sind."""
    try:
        acct = await partner_service.ensure_partner_account(user_id=str(user["user_id"]))
        rows = await postgres_client.fetch(
            """
            SELECT u.id, u.email, u.username, u.plan, u.created_at, u.role
            FROM users u
            WHERE u.referred_by_partner_id = $1
            ORDER BY u.created_at DESC
            LIMIT $2 OFFSET $3
            """,
            acct["id"], limit, offset,
        )
        total = await postgres_client.fetchval(
            "SELECT COUNT(*) FROM users WHERE referred_by_partner_id = $1",
            acct["id"],
        )
        return {"data": [dict(r) for r in rows or []], "total": total or 0}
    except Exception as e:
        logger.error(f"list_clients failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list clients")


@router.post("/clients")
async def create_client(
    body: CreateClientRequest,
    user: dict = Depends(require_roles([UserRole.PARTNER, UserRole.ADMIN]))
):
    """Erstellt einen Kunden-Account und verknüpft ihn mit dem Partner.

    - Setzt `referred_by_partner_id` und `referred_at`
    - Erlaubte Rollen: viewer, analyst (kein Admin)
    - Initialer Plan: community (Standard) oder explizit übergeben
    """
    try:
        acct = await partner_service.ensure_partner_account(user_id=str(user["user_id"]))
        # Validierung Email-Uniqueness
        existing = await postgres_client.fetchval("SELECT 1 FROM users WHERE email = $1 LIMIT 1", body.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email bereits registriert")

        # Begrenze erlaubte Rollen/Pläne
        allowed_roles = {"viewer", "analyst"}
        role = (body.role or "viewer").lower()
        if role not in allowed_roles:
            role = "viewer"
        plan = (body.plan or "community").lower()

        # Generiere temporäres Passwort (Partner teilt Invite-Flow/Reset-LInk extern)
        import secrets
        temp_password = secrets.token_urlsafe(12)
        hashed = get_password_hash(temp_password)
        username = body.username or (body.email.split("@")[0])

        row = await postgres_client.fetchrow(
            """
            INSERT INTO users (email, username, hashed_password, role, is_active, created_at, updated_at, plan, features, referred_by_partner_id, referred_at)
            VALUES ($1, $2, $3, $4, TRUE, NOW(), NOW(), $5, '[]'::jsonb, $6, NOW())
            RETURNING id, email, username, plan, role, created_at
            """,
            body.email, username, hashed, role, plan, acct["id"],
        )

        return {"client": dict(row), "temp_password": temp_password}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"create_client failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create client")


# =============================
# Admin: Payout Review & Actions
# =============================

@router.get("/admin/payouts")
async def admin_list_payouts(
    status: Optional[str] = Query(None, description="requested|approved|paid|canceled"),
    limit: int = 50,
    offset: int = 0,
    _user: dict = Depends(require_admin)
):
    try:
        if status:
            rows = await postgres_client.fetch(
                """
                SELECT pp.*, pa.user_id AS partner_user_id
                FROM partner_payouts pp
                JOIN partner_accounts pa ON pa.id = pp.partner_id
                WHERE pp.status = $1
                ORDER BY requested_at DESC
                LIMIT $2 OFFSET $3
                """,
                status, limit, offset,
            )
        else:
            rows = await postgres_client.fetch(
                """
                SELECT pp.*, pa.user_id AS partner_user_id
                FROM partner_payouts pp
                JOIN partner_accounts pa ON pa.id = pp.partner_id
                ORDER BY requested_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit, offset,
            )
        return {"data": [dict(r) for r in rows or []]}
    except Exception as e:
        logger.error(f"admin_list_payouts failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list payouts")


@router.put("/admin/payouts/{payout_id}/approve")
async def admin_approve_payout(
    payout_id: str,
    _user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        row = await postgres_client.fetchrow(
            """
            UPDATE partner_payouts
            SET status = 'approved', updated_at = NOW()
            WHERE id = $1 AND status = 'requested'
            RETURNING *
            """,
            payout_id,
        )
        if not row:
            raise HTTPException(status_code=400, detail="Payout not in requested state or not found")
        # Notify partner
        try:
            pns = PremiumNotificationService(db)
            acct = await postgres_client.fetchrow("SELECT user_id FROM partner_accounts WHERE id = $1", row["partner_id"])  # type: ignore
            if acct and acct.get("user_id"):
                await pns.send_notification(
                    user_id=str(acct["user_id"]),
                    title="Auszahlung genehmigt",
                    message=f"Ihre Auszahlungsanfrage ${float(row['amount_usd']):.2f} wurde genehmigt.",
                    type="payment",
                    priority="high",
                    action_url=f"{settings.FRONTEND_URL}/partner" if getattr(settings, "FRONTEND_URL", None) else None,
                    metadata={"payout_id": str(row["id"])},
                )
        except Exception:
            pass
        return {"payout": dict(row)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_approve_payout failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to approve payout")


class PayPayoutRequest(BaseModel):
    tx_ref: Optional[str] = Field(None, description="Transaktionsreferenz / TX-Hash")


@router.put("/admin/payouts/{payout_id}/pay")
async def admin_pay_payout(
    payout_id: str,
    body: PayPayoutRequest,
    _user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        row = await postgres_client.fetchrow(
            """
            UPDATE partner_payouts
            SET status = 'paid', paid_at = NOW(), tx_ref = COALESCE($2, tx_ref), updated_at = NOW()
            WHERE id = $1 AND status IN ('approved','requested')
            RETURNING *
            """,
            payout_id, body.tx_ref,
        )
        if not row:
            raise HTTPException(status_code=400, detail="Payout not found or invalid state")
        # Notify partner
        try:
            pns = PremiumNotificationService(db)
            acct = await postgres_client.fetchrow("SELECT user_id FROM partner_accounts WHERE id = $1", row["partner_id"])  # type: ignore
            if acct and acct.get("user_id"):
                await pns.send_notification(
                    user_id=str(acct["user_id"]),
                    title="Auszahlung ausgezahlt",
                    message=f"Ihre Auszahlung ${float(row['amount_usd']):.2f} wurde ausgeführt.",
                    type="payment",
                    priority="high",
                    action_url=f"{settings.FRONTEND_URL}/partner" if getattr(settings, "FRONTEND_URL", None) else None,
                    metadata={"payout_id": str(row["id"]), "tx_ref": row.get("tx_ref")},
                )
        except Exception:
            pass
        return {"payout": dict(row)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_pay_payout failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to mark payout as paid")


# =============================
# CSV-Export: Partner Commissions
# =============================

@router.get("/commissions/export")
async def export_commissions_csv(
    status: Optional[str] = Query(None, description="pending|approved|paid|canceled"),
    user: dict = Depends(require_roles([UserRole.PARTNER, UserRole.ADMIN]))
):
    try:
        acct = await partner_service.ensure_partner_account(user_id=str(user["user_id"]))
        if status:
            rows = await postgres_client.fetch(
                """
                SELECT * FROM partner_commissions
                WHERE partner_id = $1 AND status = $2
                ORDER BY event_time DESC
                """,
                acct["id"], status,
            )
        else:
            rows = await postgres_client.fetch(
                """
                SELECT * FROM partner_commissions
                WHERE partner_id = $1
                ORDER BY event_time DESC
                """,
                acct["id"],
            )
        # Build CSV
        buf = io.StringIO()
        writer = csv.writer(buf)
        header = ["id","referred_user_id","payment_id","order_id","plan_name","amount_usd","commission_rate","commission_usd","status","event_time"]
        writer.writerow(header)
        for r in rows or []:
            writer.writerow([
                r.get("id"), r.get("referred_user_id"), r.get("payment_id"), r.get("order_id"), r.get("plan_name"),
                float(r.get("amount_usd") or 0), float(r.get("commission_rate") or 0), float(r.get("commission_usd") or 0),
                r.get("status"), (r.get("event_time").isoformat() if r.get("event_time") else None)
            ])
        buf.seek(0)
        filename = f"partner_commissions_{acct['id']}.csv"
        return StreamingResponse(buf, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})
    except Exception as e:
        logger.error(f"export_commissions_csv failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export commissions")
