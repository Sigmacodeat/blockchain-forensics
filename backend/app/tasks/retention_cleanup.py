"""
Retention Cleanup CRON Job
===========================

Daily cleanup of expired data
"""

import logging
import asyncio
from datetime import datetime

from app.services.retention_service import retention_service
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)


async def run_retention_cleanup():
    """
    Run data retention cleanup
    
    Should be scheduled as daily CRON job:
    - Run at 2 AM UTC (low traffic time)
    - Command: python -m app.tasks.retention_cleanup
    """
    logger.info("=== Starting Daily Retention Cleanup ===")
    start_time = datetime.utcnow()
    
    try:
        # Run cleanup
        summary = await retention_service.cleanup_expired_data()
        
        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Log to audit trail
        await audit_service.log_action(
            user_id="system",
            action="retention_cleanup",
            resource_type="data",
            resource_id="all",
            details={
                "summary": summary,
                "duration_seconds": duration
            }
        )
        
        logger.info(f"=== Retention Cleanup Completed in {duration:.2f}s ===")
        logger.info(f"Summary: {summary}")
        
        return summary
    
    except Exception as e:
        logger.error(f"Retention cleanup failed: {e}", exc_info=True)
        
        # Log failure
        await audit_service.log_action(
            user_id="system",
            action="retention_cleanup_failed",
            resource_type="data",
            resource_id="all",
            details={"error": str(e)}
        )
        
        raise


if __name__ == "__main__":
    # Run cleanup
    asyncio.run(run_retention_cleanup())
