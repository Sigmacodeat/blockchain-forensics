"""
Data Retention Service
======================

Automatic cleanup of expired data per retention policies
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RetentionService:
    """Data retention policy enforcement"""
    
    # Retention periods (days)
    POLICIES = {
        "chat_messages": 90,        # 3 months
        "reports": 365,             # 1 year
        "traces": 365,              # 1 year
        "audit_logs": 730,          # 2 years (compliance)
        "cases": 1095,              # 3 years
        "temp_files": 7,            # 1 week
    }
    
    async def cleanup_expired_data(self) -> Dict[str, Any]:
        """
        Cleanup expired data based on retention policies
        
        Should be run as CRON job (daily)
        
        Returns:
            Summary of deleted data
        """
        try:
            from app.db.postgres_client import postgres_client
            
            logger.info("Starting retention cleanup...")
            
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "deleted": {}
            }
            
            # 1. Chat messages (90 days)
            cutoff_chat = datetime.utcnow() - timedelta(days=self.POLICIES["chat_messages"])
            deleted_chat = await postgres_client.execute(
                "DELETE FROM chat_messages WHERE created_at < $1",
                cutoff_chat
            )
            summary["deleted"]["chat_messages"] = deleted_chat
            logger.info(f"Deleted {deleted_chat} old chat messages")
            
            # 2. Reports (365 days)
            cutoff_reports = datetime.utcnow() - timedelta(days=self.POLICIES["reports"])
            deleted_reports = await postgres_client.execute(
                "DELETE FROM reports WHERE created_at < $1",
                cutoff_reports
            )
            summary["deleted"]["reports"] = deleted_reports
            logger.info(f"Deleted {deleted_reports} old reports")
            
            # 3. Traces (365 days)
            cutoff_traces = datetime.utcnow() - timedelta(days=self.POLICIES["traces"])
            deleted_traces = await postgres_client.execute(
                "DELETE FROM traces WHERE created_at < $1",
                cutoff_traces
            )
            summary["deleted"]["traces"] = deleted_traces
            logger.info(f"Deleted {deleted_traces} old traces")
            
            # 4. Audit logs (730 days - compliance requirement)
            cutoff_audit = datetime.utcnow() - timedelta(days=self.POLICIES["audit_logs"])
            deleted_audit = await postgres_client.execute(
                "DELETE FROM audit_logs WHERE timestamp < $1",
                cutoff_audit
            )
            summary["deleted"]["audit_logs"] = deleted_audit
            logger.info(f"Deleted {deleted_audit} old audit logs")
            
            # 5. Cases (1095 days = 3 years)
            cutoff_cases = datetime.utcnow() - timedelta(days=self.POLICIES["cases"])
            deleted_cases = await postgres_client.execute(
                "DELETE FROM cases WHERE created_at < $1",
                cutoff_cases
            )
            summary["deleted"]["cases"] = deleted_cases
            logger.info(f"Deleted {deleted_cases} old cases")
            
            logger.info(f"Retention cleanup completed: {summary}")
            
            return summary
        
        except Exception as e:
            logger.error(f"Retention cleanup failed: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def get_cleanup_estimate(self) -> Dict[str, Any]:
        """
        Estimate how much data would be deleted
        
        Returns:
            Counts of records that would be deleted
        """
        try:
            from app.db.postgres_client import postgres_client
            
            estimate = {}
            
            # Chat messages
            cutoff = datetime.utcnow() - timedelta(days=self.POLICIES["chat_messages"])
            count = await postgres_client.fetch_val(
                "SELECT COUNT(*) FROM chat_messages WHERE created_at < $1",
                cutoff
            )
            estimate["chat_messages"] = count
            
            # Reports
            cutoff = datetime.utcnow() - timedelta(days=self.POLICIES["reports"])
            count = await postgres_client.fetch_val(
                "SELECT COUNT(*) FROM reports WHERE created_at < $1",
                cutoff
            )
            estimate["reports"] = count
            
            # Traces
            cutoff = datetime.utcnow() - timedelta(days=self.POLICIES["traces"])
            count = await postgres_client.fetch_val(
                "SELECT COUNT(*) FROM traces WHERE created_at < $1",
                cutoff
            )
            estimate["traces"] = count
            
            return estimate
        
        except Exception as e:
            logger.error(f"Failed to estimate cleanup: {e}")
            return {"error": str(e)}


# Global singleton
retention_service = RetentionService()
