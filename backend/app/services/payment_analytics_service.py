"""
Payment Analytics & Revenue Dashboard Service
Comprehensive analytics for payment tracking and business insights
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.db.session import get_db
from app.config import settings

logger = logging.getLogger(__name__)


class PaymentAnalyticsService:
    """Service for payment analytics and revenue tracking."""

    def get_revenue_summary(self, days: int = 30) -> Dict[str, any]:
        """Get revenue summary for the last N days."""
        db: Session = next(get_db())
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Revenue from crypto payments
            crypto_revenue = db.query(
                func.sum(CryptoPayment.pay_amount).label("total_crypto"),
                func.count(CryptoPayment.id).label("crypto_count")
            ).filter(
                and_(
                    CryptoPayment.payment_status == "finished",
                    CryptoPayment.created_at >= cutoff_date
                )
            ).first()

            # Revenue from user subscriptions (active)
            subscription_revenue = db.query(
                func.sum(UserSubscription.crypto_amount).label("total_subscription"),
                func.count(UserSubscription.id).label("subscription_count")
            ).filter(
                and_(
                    UserSubscription.status == "active",
                    UserSubscription.created_at >= cutoff_date
                )
            ).first()

            # Revenue by currency
            currency_breakdown = db.query(
                CryptoPayment.pay_currency,
                func.sum(CryptoPayment.pay_amount).label("amount"),
                func.count(CryptoPayment.id).label("count")
            ).filter(
                and_(
                    CryptoPayment.payment_status == "finished",
                    CryptoPayment.created_at >= cutoff_date
                )
            ).group_by(CryptoPayment.pay_currency).all()

            # Revenue by plan
            plan_breakdown = db.query(
                CryptoPayment.plan_name,
                func.sum(CryptoPayment.pay_amount).label("amount"),
                func.count(CryptoPayment.id).label("count")
            ).filter(
                and_(
                    CryptoPayment.payment_status == "finished",
                    CryptoPayment.created_at >= cutoff_date
                )
            ).group_by(CryptoPayment.plan_name).all()

            return {
                "period_days": days,
                "total_revenue_crypto": float(crypto_revenue.total_crypto or 0),
                "total_revenue_subscription": float(subscription_revenue.total_subscription or 0),
                "total_revenue": float((crypto_revenue.total_crypto or 0) + (subscription_revenue.total_subscription or 0)),
                "total_transactions": (crypto_revenue.crypto_count or 0) + (subscription_revenue.subscription_count or 0),
                "currency_breakdown": [
                    {
                        "currency": curr[0],
                        "amount": float(curr[1]),
                        "count": curr[2]
                    } for curr in currency_breakdown
                ],
                "plan_breakdown": [
                    {
                        "plan": plan[0],
                        "amount": float(plan[1]),
                        "count": plan[2]
                    } for plan in plan_breakdown
                ]
            }

        finally:
            db.close()

    def get_daily_revenue(self, days: int = 30) -> List[Dict[str, any]]:
        """Get daily revenue breakdown."""
        db: Session = next(get_db())
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Daily crypto payments
            crypto_daily = db.query(
                func.date(CryptoPayment.created_at).label("date"),
                func.sum(CryptoPayment.pay_amount).label("crypto_amount"),
                func.count(CryptoPayment.id).label("crypto_count")
            ).filter(
                and_(
                    CryptoPayment.payment_status == "finished",
                    CryptoPayment.created_at >= cutoff_date
                )
            ).group_by(func.date(CryptoPayment.created_at)).all()

            # Daily subscription activations
            sub_daily = db.query(
                func.date(UserSubscription.created_at).label("date"),
                func.sum(UserSubscription.crypto_amount).label("sub_amount"),
                func.count(UserSubscription.id).label("sub_count")
            ).filter(
                and_(
                    UserSubscription.status == "active",
                    UserSubscription.created_at >= cutoff_date
                )
            ).group_by(func.date(UserSubscription.created_at)).all()

            # Combine results
            daily_data = {}
            for row in crypto_daily:
                date_str = row.date.isoformat()
                daily_data[date_str] = {
                    "date": date_str,
                    "crypto_revenue": float(row.crypto_amount or 0),
                    "crypto_count": row.crypto_count,
                    "subscription_revenue": 0,
                    "subscription_count": 0
                }

            for row in sub_daily:
                date_str = row.date.isoformat()
                if date_str not in daily_data:
                    daily_data[date_str] = {
                        "date": date_str,
                        "crypto_revenue": 0,
                        "crypto_count": 0,
                        "subscription_revenue": float(row.sub_amount or 0),
                        "subscription_count": row.sub_count
                    }
                else:
                    daily_data[date_str]["subscription_revenue"] = float(row.sub_amount or 0)
                    daily_data[date_str]["subscription_count"] = row.sub_count

            # Calculate totals
            for data in daily_data.values():
                data["total_revenue"] = data["crypto_revenue"] + data["subscription_revenue"]
                data["total_count"] = data["crypto_count"] + data["subscription_count"]

            return sorted(daily_data.values(), key=lambda x: x["date"])

        finally:
            db.close()

    def get_payment_conversion_funnel(self, days: int = 30) -> Dict[str, any]:
        """Get payment conversion funnel data."""
        db: Session = next(get_db())
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Invoice creation attempts
            total_invoices = db.query(func.count(CryptoDepositAddress.id)).filter(
                CryptoDepositAddress.created_at >= cutoff_date
            ).scalar() or 0

            # Pending payments
            pending_payments = db.query(func.count(CryptoDepositAddress.id)).filter(
                and_(
                    CryptoDepositAddress.status == "pending",
                    CryptoDepositAddress.created_at >= cutoff_date
                )
            ).scalar() or 0

            # Paid invoices
            paid_invoices = db.query(func.count(CryptoDepositAddress.id)).filter(
                and_(
                    CryptoDepositAddress.status == "paid",
                    CryptoDepositAddress.created_at >= cutoff_date
                )
            ).scalar() or 0

            # Expired invoices
            expired_invoices = db.query(func.count(CryptoDepositAddress.id)).filter(
                and_(
                    CryptoDepositAddress.status == "expired",
                    CryptoDepositAddress.created_at >= cutoff_date
                )
            ).scalar() or 0

            # Subscription activations
            subscriptions_activated = db.query(func.count(UserSubscription.id)).filter(
                and_(
                    UserSubscription.status == "active",
                    UserSubscription.created_at >= cutoff_date
                )
            ).scalar() or 0

            return {
                "period_days": days,
                "funnel": {
                    "invoices_created": total_invoices,
                    "pending_payments": pending_payments,
                    "paid_invoices": paid_invoices,
                    "expired_invoices": expired_invoices,
                    "subscriptions_activated": subscriptions_activated
                },
                "conversion_rates": {
                    "pending_to_paid": (paid_invoices / max(pending_payments, 1)) * 100,
                    "paid_to_subscription": (subscriptions_activated / max(paid_invoices, 1)) * 100,
                    "overall_conversion": (subscriptions_activated / max(total_invoices, 1)) * 100
                }
            }

        finally:
            db.close()

    def get_top_performing_assets(self, days: int = 30) -> List[Dict[str, any]]:
        """Get top performing payment assets by revenue."""
        db: Session = next(get_db())
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Top crypto currencies by revenue
            crypto_performance = db.query(
                CryptoPayment.pay_currency.label("asset"),
                func.sum(CryptoPayment.pay_amount).label("revenue"),
                func.count(CryptoPayment.id).label("transaction_count"),
                func.avg(CryptoPayment.pay_amount).label("avg_transaction")
            ).filter(
                and_(
                    CryptoPayment.payment_status == "finished",
                    CryptoPayment.created_at >= cutoff_date
                )
            ).group_by(CryptoPayment.pay_currency).all()

            # Top subscription plans
            plan_performance = db.query(
                UserSubscription.plan_name.label("asset"),
                func.sum(UserSubscription.crypto_amount).label("revenue"),
                func.count(UserSubscription.id).label("transaction_count"),
                func.avg(UserSubscription.crypto_amount).label("avg_transaction")
            ).filter(
                and_(
                    UserSubscription.status == "active",
                    UserSubscription.created_at >= cutoff_date
                )
            ).group_by(UserSubscription.plan_name).all()

            # Combine and sort by revenue
            all_performance = []
            for row in crypto_performance:
                all_performance.append({
                    "asset": row.asset,
                    "type": "crypto_payment",
                    "revenue": float(row.revenue),
                    "transaction_count": row.transaction_count,
                    "avg_transaction": float(row.avg_transaction)
                })

            for row in plan_performance:
                all_performance.append({
                    "asset": row.asset,
                    "type": "subscription",
                    "revenue": float(row.revenue),
                    "transaction_count": row.transaction_count,
                    "avg_transaction": float(row.avg_transaction)
                })

            return sorted(all_performance, key=lambda x: x["revenue"], reverse=True)[:10]

        finally:
            db.close()

    def get_payment_geography(self, days: int = 30) -> List[Dict[str, any]]:
        """Get payment geography data (if user location is tracked)."""
        # This would require user location tracking
        # For now, return mock data
        return [
            {"country": "Germany", "revenue": 12500, "transactions": 45},
            {"country": "USA", "revenue": 8900, "transactions": 32},
            {"country": "UK", "revenue": 6700, "transactions": 28},
            {"country": "France", "revenue": 4500, "transactions": 18},
            {"country": "Canada", "revenue": 3200, "transactions": 12}
        ]


# Import models here to avoid circular imports
from app.models.crypto_payment import CryptoPayment, CryptoDepositAddress
from app.models.user import UserSubscription

# Global instance
payment_analytics_service = PaymentAnalyticsService()
