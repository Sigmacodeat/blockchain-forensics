"""
Subscription Renewal Cronjob
Runs daily to check expiring subscriptions and process renewals
"""
import logging
import asyncio
from datetime import datetime
from typing import List

from app.services.subscription_service import subscription_service
from app.services.notification_service import notification_service
from app.models.user import User

logger = logging.getLogger(__name__)


async def check_expiring_subscriptions():
    """
    Check for subscriptions expiring in the next 3 days
    Send renewal reminders
    
    Run: Daily at 09:00 UTC
    """
    logger.info("Starting expiring subscriptions check...")
    
    try:
        # In real app: Query database for users with billing_cycle_end in next 3 days
        # SELECT * FROM users WHERE billing_cycle_end BETWEEN NOW() AND NOW() + INTERVAL '3 days'
        
        expiring_users: List[User] = []  # Mock - would be DB query
        
        for user in expiring_users:
            # Send renewal reminder
            await notification_service.send_renewal_reminder(
                user_email=user.email,
                renewal_date=user.billing_cycle_end,
                plan=user.plan.value,
                amount=4900  # Mock amount
            )
            
            logger.info(f"Sent renewal reminder to {user.email}")
        
        logger.info(f"Processed {len(expiring_users)} expiring subscriptions")
        return {'status': 'success', 'reminders_sent': len(expiring_users)}
    
    except Exception as e:
        logger.error(f"Error checking expiring subscriptions: {e}")
        return {'status': 'error', 'error': str(e)}


async def process_subscription_renewals():
    """
    Process automatic subscription renewals
    Check subscriptions that ended today
    
    Run: Daily at 00:30 UTC
    """
    logger.info("Starting subscription renewals...")
    
    try:
        # Query users with billing_cycle_end = today
        users_to_renew: List[User] = []  # Mock
        
        results = []
        for user in users_to_renew:
            try:
                result = await subscription_service.process_renewal(user)
                results.append({
                    'user_id': user.id,
                    'status': result['status']
                })
                
                logger.info(f"Renewed subscription for {user.email}: {result['status']}")
            
            except Exception as e:
                logger.error(f"Failed to renew subscription for {user.email}: {e}")
                results.append({
                    'user_id': user.id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        logger.info(f"Processed {len(results)} subscription renewals")
        return {'status': 'success', 'renewals': results}
    
    except Exception as e:
        logger.error(f"Error processing renewals: {e}")
        return {'status': 'error', 'error': str(e)}


async def check_grace_period_expirations():
    """
    Check for subscriptions past grace period
    Downgrade to Community if payment still failed
    
    Run: Daily at 02:00 UTC
    """
    logger.info("Checking grace period expirations...")
    
    try:
        # Query users with subscription_status = 'past_due' 
        # AND billing_cycle_end + 7 days < NOW()
        
        expired_users: List[User] = []  # Mock
        
        downgrades = []
        for user in expired_users:
            result = await subscription_service.check_expired_subscriptions(user)
            
            if result['status'] == 'downgraded':
                # Send notification
                await notification_service.send_downgrade_warning_email(
                    user_email=user.email,
                    current_plan=user.plan.value,
                    downgrade_date=datetime.now(),
                    reason="payment_failure"
                )
                
                downgrades.append(user.id)
                logger.info(f"Downgraded {user.email} to Community due to payment failure")
        
        logger.info(f"Processed {len(downgrades)} downgrades")
        return {'status': 'success', 'downgrades': downgrades}
    
    except Exception as e:
        logger.error(f"Error checking grace periods: {e}")
        return {'status': 'error', 'error': str(e)}


async def retry_failed_payments():
    """
    Retry failed payments for past_due subscriptions
    Attempt to charge customer again
    
    Run: Daily at 10:00 UTC
    """
    logger.info("Retrying failed payments...")
    
    try:
        # Query users with subscription_status = 'past_due'
        past_due_users: List[User] = []  # Mock
        
        results = await subscription_service.retry_failed_payments(past_due_users)
        
        successful = [r for r in results if r['status'] == 'retried']
        failed = [r for r in results if r['status'] == 'failed']
        
        logger.info(f"Retry results: {len(successful)} successful, {len(failed)} failed")
        
        return {
            'status': 'success',
            'successful_retries': len(successful),
            'failed_retries': len(failed)
        }
    
    except Exception as e:
        logger.error(f"Error retrying payments: {e}")
        return {'status': 'error', 'error': str(e)}


async def process_scheduled_cancellations():
    """
    Process subscriptions scheduled to cancel at period end
    Downgrade to Community
    
    Run: Daily at 03:00 UTC
    """
    logger.info("Processing scheduled cancellations...")
    
    try:
        # Query users with subscription_status = 'cancelling'
        # AND billing_cycle_end <= NOW()
        
        cancelling_users: List[User] = []  # Mock
        
        cancelled = []
        for user in cancelling_users:
            # Downgrade to Community
            from app.services.user_service import user_service
            await user_service.downgrade_to_community(user_id=user.id)
            
            # Send confirmation
            await notification_service.send_subscription_cancelled_email(
                user_email=user.email,
                plan=user.plan.value,
                end_date=datetime.now()
            )
            
            cancelled.append(user.id)
            logger.info(f"Cancelled subscription for {user.email}")
        
        logger.info(f"Processed {len(cancelled)} cancellations")
        return {'status': 'success', 'cancellations': cancelled}
    
    except Exception as e:
        logger.error(f"Error processing cancellations: {e}")
        return {'status': 'error', 'error': str(e)}


# Main cron job runner
async def run_all_subscription_jobs():
    """
    Run all subscription-related cron jobs
    Can be called by scheduler (e.g., APScheduler, Celery Beat)
    """
    logger.info("=" * 80)
    logger.info("Starting subscription cron jobs")
    logger.info("=" * 80)
    
    results = {}
    
    # Run jobs sequentially
    results['renewals'] = await process_subscription_renewals()
    results['expiring'] = await check_expiring_subscriptions()
    results['grace_periods'] = await check_grace_period_expirations()
    results['retry_payments'] = await retry_failed_payments()
    results['cancellations'] = await process_scheduled_cancellations()
    
    logger.info("=" * 80)
    logger.info("Completed subscription cron jobs")
    logger.info(f"Results: {results}")
    logger.info("=" * 80)
    
    return results


if __name__ == "__main__":
    # Run cronjobs manually for testing
    asyncio.run(run_all_subscription_jobs())
