"""
Partner/Affiliate Service
- Schema-Initialisierung (Create-If-Not-Exists)
- Referral-Attribution und Kommissionsbuchung
"""
from __future__ import annotations

import os
import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime

from app.db.postgres import postgres_client
from app.services.plan_service import plan_service

logger = logging.getLogger(__name__)


class PartnerService:
    DEFAULT_COMMISSION_RATE = 20.0  # % für Erst- und Folgezahlungen (einfaches Modell)
    DEFAULT_RECURRING_RATE = 20.0   # %
    DEFAULT_COOKIE_DAYS = 30
    DEFAULT_MIN_PAYOUT_USD = 50.0

    def __init__(self):
        self._initialized = False

    async def init(self):
        if self._initialized:
            return
        # In Test-Umgebung überspringen, wenn kein Pool vorhanden
        try:
            await self._ensure_schema()
            self._initialized = True
            logger.info("✅ PartnerService initialized (schema ensured)")
        except Exception as e:
            logger.error(f"PartnerService init failed: {e}", exc_info=True)

    async def _ensure_schema(self) -> None:
        """Erzeugt benötigte Tabellen/Spalten (idempotent)."""
        # Skip when no postgres pool (e.g., TEST_MODE)
        if getattr(postgres_client, "pool", None) is None and os.getenv("TEST_MODE") == "1":
            logger.info("PartnerService schema skipped in TEST_MODE")
            return

        # Tables
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS partner_accounts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                name TEXT,
                referral_code TEXT UNIQUE,
                commission_rate NUMERIC(5,2) DEFAULT 20.0,
                recurring_rate NUMERIC(5,2) DEFAULT 20.0,
                cookie_duration_days INT DEFAULT 30,
                min_payout_usd NUMERIC(12,2) DEFAULT 50.0,
                payout_method TEXT,
                payout_details JSONB,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )
        await postgres_client.execute(
            """
            CREATE TABLE IF NOT EXISTS partner_referrals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                partner_id UUID REFERENCES partner_accounts(id) ON DELETE CASCADE,
                referred_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                source TEXT,
                tracking_id TEXT,
                first_touch_at TIMESTAMPTZ DEFAULT NOW(),
                last_touch_at TIMESTAMPTZ DEFAULT NOW(),
                attributions JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_partner_referrals_partner ON partner_referrals(partner_id);
            CREATE INDEX IF NOT EXISTS idx_partner_referrals_user ON partner_referrals(referred_user_id);
            """
        )
        await postgres_client.execute(
            """
            CREATE TABLE IF NOT EXISTS partner_commissions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                partner_id UUID REFERENCES partner_accounts(id) ON DELETE CASCADE,
                referred_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                payment_id INT,
                order_id TEXT,
                plan_name TEXT,
                amount_usd NUMERIC(12,2) NOT NULL,
                commission_rate NUMERIC(5,2) NOT NULL,
                commission_usd NUMERIC(12,2) NOT NULL,
                status TEXT DEFAULT 'pending',
                event_time TIMESTAMPTZ DEFAULT NOW(),
                notes TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_partner_comm_partner ON partner_commissions(partner_id);
            CREATE INDEX IF NOT EXISTS idx_partner_comm_user ON partner_commissions(referred_user_id);
            CREATE INDEX IF NOT EXISTS idx_partner_comm_status ON partner_commissions(status);
            CREATE INDEX IF NOT EXISTS idx_partner_comm_order ON partner_commissions(order_id);
            """
        )
        await postgres_client.execute(
            """
            CREATE TABLE IF NOT EXISTS partner_payouts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                partner_id UUID REFERENCES partner_accounts(id) ON DELETE CASCADE,
                amount_usd NUMERIC(12,2) NOT NULL,
                status TEXT DEFAULT 'requested',
                requested_at TIMESTAMPTZ DEFAULT NOW(),
                paid_at TIMESTAMPTZ,
                tx_ref TEXT,
                details JSONB
            );
            CREATE INDEX IF NOT EXISTS idx_partner_payouts_partner ON partner_payouts(partner_id);
            CREATE INDEX IF NOT EXISTS idx_partner_payouts_status ON partner_payouts(status);
            """
        )
        # Users: referred_by_partner_id, referred_at
        await self._execute(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS referred_by_partner_id UUID REFERENCES partner_accounts(id),
            ADD COLUMN IF NOT EXISTS referred_at TIMESTAMPTZ;
            """
        )

    async def ensure_partner_account(self, user_id: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Erstellt Partner-Account für user_id, falls nicht vorhanden."""
        acct = await self._fetchrow(
            "SELECT * FROM partner_accounts WHERE user_id = $1",
            user_id,
        )
        if acct:
            return dict(acct)
        # generate code
        code = f"p-{secrets.token_urlsafe(6)}".lower()
        await self._execute(
            """
            INSERT INTO partner_accounts (user_id, name, referral_code, commission_rate, recurring_rate, cookie_duration_days, min_payout_usd, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE)
            """,
            user_id,
            name or "Partner",
            code,
            self.DEFAULT_COMMISSION_RATE,
            self.DEFAULT_RECURRING_RATE,
            self.DEFAULT_COOKIE_DAYS,
            self.DEFAULT_MIN_PAYOUT_USD,
        )
        acct = await self._fetchrow(
            "SELECT * FROM partner_accounts WHERE user_id = $1",
            user_id,
        )
        return dict(acct) if acct else {"user_id": user_id, "referral_code": code}

    async def get_partner_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        row = await self._fetchrow(
            "SELECT * FROM partner_accounts WHERE referral_code = $1 AND is_active = TRUE",
            referral_code,
        )
        return dict(row) if row else None

    async def assign_referral(self, referred_user_id: str, referral_code: str, tracking_id: Optional[str] = None, source: Optional[str] = None) -> bool:
        """Verknüpft einen User mit einem Partner anhand referral_code (First-touch)."""
        partner = await self.get_partner_by_referral_code(referral_code)
        if not partner:
            return False
        pid = partner["id"]
        # If already referred, do not overwrite
        existing = await self._fetchrow(
            "SELECT referred_by_partner_id FROM users WHERE id = $1",
            referred_user_id,
        )
        if existing and (existing.get("referred_by_partner_id") is not None):
            return True
        await self._execute(
            """
            UPDATE users SET referred_by_partner_id = $1, referred_at = NOW() WHERE id = $2
            """,
            pid, referred_user_id,
        )
        await self._execute(
            """
            INSERT INTO partner_referrals (partner_id, referred_user_id, source, tracking_id, attributions)
            VALUES ($1, $2, $3, $4, $5)
            """,
            pid, referred_user_id, source, tracking_id, None,
        )
        return True

    async def _resolve_partner_for_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        row = await self._fetchrow(
            "SELECT pa.* FROM users u JOIN partner_accounts pa ON u.referred_by_partner_id = pa.id WHERE u.id = $1",
            user_id,
        )
        if row:
            return dict(row)
        # fallback: check referrals table
        row = await self._fetchrow(
            """
            SELECT pa.*
            FROM partner_referrals pr
            JOIN partner_accounts pa ON pr.partner_id = pa.id
            WHERE pr.referred_user_id = $1
            ORDER BY pr.first_touch_at ASC
            LIMIT 1
            """,
            user_id,
        )
        return dict(row) if row else None

    async def record_commission_on_payment(self, user_id: str, plan_name: str, amount_usd: float, payment_id: int, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Wird beim Payment-Webhook (finished) aufgerufen und legt eine Kommission an.
        """
        try:
            partner = await self._resolve_partner_for_user(user_id)
            if not partner:
                return None
            rate = float(partner.get("commission_rate") or self.DEFAULT_COMMISSION_RATE)
            commission_usd = round((amount_usd or 0.0) * (rate / 100.0), 2)
            row = await self._fetchrow(
                """
                INSERT INTO partner_commissions (partner_id, referred_user_id, payment_id, order_id, plan_name, amount_usd, commission_rate, commission_usd, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')
                RETURNING *
                """,
                partner["id"], user_id, payment_id, order_id, plan_name, amount_usd, rate, commission_usd,
            )
            logger.info(
                f"Commission recorded: partner={partner.get('id')} user={user_id} payment={payment_id} gross={amount_usd} rate={rate}% net={commission_usd}"
            )
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"record_commission_on_payment failed: {e}", exc_info=True)
            return None

    async def record_commission_on_usage(
        self,
        user_id: str,
        feature: str,
        tokens: int,
    ) -> Optional[Dict[str, Any]]:
        """Erzeugt oder aggregiert eine nutzungsbasierte Kommission.

        - Tokens werden über Pricing (overage.price_per_1000_credits_usd) in USD konvertiert.
        - Aggregation pro Tag und Feature über order_id = "usage:YYYY-MM-DD:feature" (pending-Status).
        - Best-Effort: Bei Fehlern kein Raise (aus Aufrufer-Sicht).
        """
        try:
            if not tokens or tokens <= 0:
                return None
            partner = await self._resolve_partner_for_user(user_id)
            if not partner:
                return None

            # Preis für Overage ermitteln (USD pro 1000 Credits)
            cfg = plan_service.get_config()
            overage = getattr(cfg, "overage", {}) or {}
            price_per_1000 = float(overage.get("price_per_1000_credits_usd", 10))

            gross_usd = round((float(tokens) / 1000.0) * price_per_1000, 2)
            if gross_usd <= 0:
                return None

            rate = float(partner.get("recurring_rate") or self.DEFAULT_RECURRING_RATE)
            commission_usd = round(gross_usd * (rate / 100.0), 2)

            order_id = f"usage:{datetime.utcnow().strftime('%Y-%m-%d')}:{feature}"

            # Versuche Aggregations-Update (pending-Reihe pro Tag/Feature)
            row = await self._fetchrow(
                """
                UPDATE partner_commissions
                SET amount_usd = amount_usd + $1,
                    commission_usd = commission_usd + $2,
                    event_time = NOW()
                WHERE partner_id = $3 AND referred_user_id = $4 AND order_id = $5 AND status = 'pending'
                RETURNING *
                """,
                gross_usd, commission_usd, partner["id"], user_id, order_id,
            )
            if row:
                return dict(row)

            # Falls keine bestehende Aggregationszeile: neu anlegen
            row = await self._fetchrow(
                """
                INSERT INTO partner_commissions (
                    partner_id, referred_user_id, payment_id, order_id, plan_name,
                    amount_usd, commission_rate, commission_usd, status
                )
                VALUES ($1, $2, NULL, $3, 'usage', $4, $5, $6, 'pending')
                RETURNING *
                """,
                partner["id"], user_id, order_id, gross_usd, rate, commission_usd,
            )
            return dict(row) if row else None
        except Exception as e:
            logger.debug(f"record_commission_on_usage skipped: {e}")
            return None

    async def _execute(self, query: str, *args) -> None:
        async with postgres_client.acquire() as conn:
            await conn.execute(query, *args)

    async def _fetchrow(self, query: str, *args):
        async with postgres_client.acquire() as conn:
            return await conn.fetchrow(query, *args)


partner_service = PartnerService()
