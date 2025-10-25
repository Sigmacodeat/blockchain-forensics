"""
Admin Endpoints for Crypto Payments
Analytics, monitoring, and management
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Query

from app.auth.middleware import require_admin
from app.db.postgres_client import postgres_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/crypto-payments", tags=["admin", "crypto-payments"])


@router.get("/list", dependencies=[Depends(require_admin)])
async def list_all_payments(
    filter: str = Query("all", pattern="^(all|finished|pending|failed)$"),
    date_range: str = Query("month", pattern="^(today|week|month|all)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    List all crypto payments (Admin only)
    
    **Query Params:**
    - filter: all, finished, pending, failed
    - date_range: today, week, month, all
    - limit: Max 1000
    - offset: Pagination offset
    
    **Returns list of all payments**
    """
    try:
        # Build date filter
        date_filter = ""
        if date_range == "today":
            date_filter = "AND created_at >= NOW() - INTERVAL '1 day'"
        elif date_range == "week":
            date_filter = "AND created_at >= NOW() - INTERVAL '7 days'"
        elif date_range == "month":
            date_filter = "AND created_at >= NOW() - INTERVAL '30 days'"
        
        # Build status filter
        status_filter = ""
        if filter == "finished":
            status_filter = "AND payment_status = 'finished'"
        elif filter == "pending":
            status_filter = "AND payment_status IN ('pending', 'waiting', 'confirming')"
        elif filter == "failed":
            status_filter = "AND payment_status IN ('failed', 'expired')"
        
        # Get payments
        query = f"""
            SELECT * FROM crypto_payments
            WHERE 1=1 {date_filter} {status_filter}
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        
        payments = await postgres_client.fetch(query, limit, offset)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) FROM crypto_payments
            WHERE 1=1 {date_filter} {status_filter}
        """
        total = await postgres_client.fetchval(count_query)
        
        return {
            "payments": [dict(p) for p in payments],
            "total": total or 0,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error listing payments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list payments")


@router.get("/analytics", dependencies=[Depends(require_admin)])
async def get_payment_analytics(
    date_range: str = Query("month", pattern="^(today|week|month|all)$")
):
    """
    Get crypto payment analytics (Admin only)
    
    **Returns:**
    - Total payments, revenue
    - Conversion rate
    - Popular currencies
    - Revenue by plan
    """
    try:
        # Build date filter
        date_filter = ""
        if date_range == "today":
            date_filter = "WHERE created_at >= NOW() - INTERVAL '1 day'"
        elif date_range == "week":
            date_filter = "WHERE created_at >= NOW() - INTERVAL '7 days'"
        elif date_range == "month":
            date_filter = "WHERE created_at >= NOW() - INTERVAL '30 days'"
        
        # Total payments
        total_payments = await postgres_client.fetchval(
            f"SELECT COUNT(*) FROM crypto_payments {date_filter}"
        ) or 0
        
        # Successful payments
        successful_payments = await postgres_client.fetchval(
            f"""
            SELECT COUNT(*) FROM crypto_payments
            {date_filter}
            {"AND" if date_filter else "WHERE"} payment_status = 'finished'
            """
        ) or 0
        
        # Failed payments
        failed_payments = await postgres_client.fetchval(
            f"""
            SELECT COUNT(*) FROM crypto_payments
            {date_filter}
            {"AND" if date_filter else "WHERE"} payment_status IN ('failed', 'expired')
            """
        ) or 0
        
        # Pending payments
        pending_payments = await postgres_client.fetchval(
            f"""
            SELECT COUNT(*) FROM crypto_payments
            {date_filter}
            {"AND" if date_filter else "WHERE"} payment_status IN ('pending', 'waiting', 'confirming')
            """
        ) or 0
        
        # Total revenue (finished payments only)
        total_revenue = await postgres_client.fetchval(
            f"""
            SELECT COALESCE(SUM(price_amount), 0) FROM crypto_payments
            {date_filter}
            {"AND" if date_filter else "WHERE"} payment_status = 'finished'
            """
        ) or 0
        
        # Conversion rate
        conversion_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
        
        # Popular currencies
        popular_currencies = await postgres_client.fetch(
            f"""
            SELECT pay_currency as currency, COUNT(*) as count
            FROM crypto_payments
            {date_filter}
            GROUP BY pay_currency
            ORDER BY count DESC
            LIMIT 10
            """
        )
        
        # Revenue by plan
        revenue_by_plan = await postgres_client.fetch(
            f"""
            SELECT plan_name as plan, COALESCE(SUM(price_amount), 0) as revenue
            FROM crypto_payments
            {date_filter}
            {"AND" if date_filter else "WHERE"} payment_status = 'finished'
            GROUP BY plan_name
            ORDER BY revenue DESC
            """
        )
        
        return {
            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "pending_payments": pending_payments,
            "total_revenue_usd": float(total_revenue),
            "conversion_rate": conversion_rate,
            "popular_currencies": [dict(c) for c in popular_currencies],
            "revenue_by_plan": [dict(r) for r in revenue_by_plan]
        }
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.get("/statistics", dependencies=[Depends(require_admin)])
async def get_payment_statistics():
    """
    Get detailed payment statistics (Admin only)
    
    **Returns:**
    - Daily revenue (last 30 days)
    - Payment status distribution
    - Average payment time
    - Top users by spending
    """
    try:
        # Daily revenue (last 30 days)
        daily_revenue = await postgres_client.fetch(
            """
            SELECT
                DATE(created_at) as date,
                COUNT(*) as payments,
                COALESCE(SUM(price_amount), 0) as revenue
            FROM crypto_payments
            WHERE created_at >= NOW() - INTERVAL '30 days'
                AND payment_status = 'finished'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """
        )
        
        # Payment status distribution
        status_distribution = await postgres_client.fetch(
            """
            SELECT payment_status as status, COUNT(*) as count
            FROM crypto_payments
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY payment_status
            """
        )
        
        # Average payment time (from created to finished)
        avg_payment_time = await postgres_client.fetchval(
            """
            SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 60) as avg_minutes
            FROM crypto_payments
            WHERE payment_status = 'finished'
                AND created_at >= NOW() - INTERVAL '30 days'
            """
        ) or 0
        
        # Top users by spending
        top_users = await postgres_client.fetch(
            """
            SELECT
                user_id,
                COUNT(*) as payment_count,
                COALESCE(SUM(price_amount), 0) as total_spent
            FROM crypto_payments
            WHERE payment_status = 'finished'
                AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY user_id
            ORDER BY total_spent DESC
            LIMIT 10
            """
        )
        
        return {
            "daily_revenue": [dict(d) for d in daily_revenue],
            "status_distribution": [dict(s) for s in status_distribution],
            "avg_payment_time_minutes": float(avg_payment_time),
            "top_users": [dict(u) for u in top_users]
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.get("/payment/{payment_id}", dependencies=[Depends(require_admin)])
async def get_payment_details(payment_id: int):
    """
    Get detailed payment information (Admin only)
    
    **Returns full payment details including user info**
    """
    try:
        payment = await postgres_client.fetchrow(
            """
            SELECT
                cp.*,
                u.email as user_email,
                u.username as user_username
            FROM crypto_payments cp
            LEFT JOIN users u ON cp.user_id = u.id
            WHERE cp.payment_id = $1
            """,
            payment_id
        )
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return dict(payment)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payment details")


@router.get("/subscriptions", dependencies=[Depends(require_admin)])
async def list_all_subscriptions():
    """
    List all crypto subscriptions (Admin only)
    
    **Returns all active and cancelled subscriptions**
    """
    try:
        subscriptions = await postgres_client.fetch(
            """
            SELECT
                cs.*,
                u.email as user_email,
                u.username as user_username
            FROM crypto_subscriptions cs
            LEFT JOIN users u ON cs.user_id = u.id
            ORDER BY created_at DESC
            """
        )
        
        return {
            "subscriptions": [dict(s) for s in subscriptions],
            "total": len(subscriptions)
        }
    except Exception as e:
        logger.error(f"Error listing subscriptions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list subscriptions")
