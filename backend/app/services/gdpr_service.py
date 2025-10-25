"""
GDPR Compliance Service
=======================

Data protection and privacy compliance (GDPR Art. 17, 20, etc.)
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class GDPRService:
    """GDPR Compliance and Data Protection"""
    
    def __init__(self):
        self.anonymization_marker = "ANONYMIZED_"
    
    async def export_user_data(self, user_id: str) -> bytes:
        """
        Export all user data (GDPR Art. 20 - Right to Data Portability)
        
        Args:
            user_id: User ID
        
        Returns:
            JSON bytes with all user data
        """
        try:
            from app.db.postgres_client import postgres_client
            
            logger.info(f"GDPR: Exporting data for user {user_id}")
            
            # Collect all user data
            data = {
                "export_date": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "data_categories": {}
            }
            
            # 1. User Profile
            user = await postgres_client.fetch_one(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
            if user:
                data["data_categories"]["profile"] = dict(user)
            
            # 2. Cases
            cases = await postgres_client.fetch_all(
                "SELECT * FROM cases WHERE owner_id = $1",
                user_id
            )
            data["data_categories"]["cases"] = [dict(c) for c in cases]
            
            # 3. Traces
            traces = await postgres_client.fetch_all(
                "SELECT * FROM traces WHERE user_id = $1",
                user_id
            )
            data["data_categories"]["traces"] = [dict(t) for t in traces]
            
            # 4. Chat History (last 90 days)
            # Assuming chat messages are stored
            # chat_messages = await get_user_chat_messages(user_id, days=90)
            # data["data_categories"]["chat_history"] = chat_messages
            
            # 5. Audit Logs
            from app.services.audit_service import audit_service
            audit_logs = await audit_service.get_user_audit_trail(
                user_id=user_id,
                days=730  # 2 years
            )
            data["data_categories"]["audit_logs"] = audit_logs
            
            # 6. Crypto Payments
            payments = await postgres_client.fetch_all(
                "SELECT * FROM crypto_payments WHERE user_id = $1",
                user_id
            )
            data["data_categories"]["payments"] = [dict(p) for p in payments]
            
            # Convert to JSON
            json_data = json.dumps(data, indent=2, default=str)
            
            logger.info(f"GDPR: Exported {len(json_data)} bytes for user {user_id}")
            
            return json_data.encode('utf-8')
        
        except Exception as e:
            logger.error(f"GDPR export failed for user {user_id}: {e}", exc_info=True)
            raise
    
    async def delete_user_data(
        self,
        user_id: str,
        mode: str = "anonymize"
    ) -> Dict[str, Any]:
        """
        Delete or anonymize user data (GDPR Art. 17 - Right to Erasure)
        
        Args:
            user_id: User ID
            mode: 'delete' (hard delete) or 'anonymize' (soft delete)
        
        Returns:
            Summary of deleted/anonymized data
        """
        try:
            from app.db.postgres_client import postgres_client
            
            logger.warning(f"GDPR: {mode} user data for {user_id}")
            
            summary = {
                "user_id": user_id,
                "mode": mode,
                "deleted_at": datetime.utcnow().isoformat(),
                "categories": {}
            }
            
            if mode == "delete":
                # HARD DELETE (irreversible)
                
                # 1. Delete cases
                result = await postgres_client.execute(
                    "DELETE FROM cases WHERE owner_id = $1",
                    user_id
                )
                summary["categories"]["cases"] = f"deleted {result}"
                
                # 2. Delete traces
                result = await postgres_client.execute(
                    "DELETE FROM traces WHERE user_id = $1",
                    user_id
                )
                summary["categories"]["traces"] = f"deleted {result}"
                
                # 3. Delete audit logs (careful! might be required for compliance)
                # Usually keep audit logs for legal reasons
                summary["categories"]["audit_logs"] = "retained (compliance)"
                
                # 4. Delete user profile
                await postgres_client.execute(
                    "UPDATE users SET deleted_at = $1, email = $2 WHERE user_id = $3",
                    datetime.utcnow(),
                    f"deleted_{user_id}@privacy.local",
                    user_id
                )
                summary["categories"]["profile"] = "deleted"
            
            else:
                # ANONYMIZE (soft delete, preserves analytics)
                
                # 1. Anonymize cases
                await postgres_client.execute(
                    """
                    UPDATE cases 
                    SET title = $1 || case_id,
                        description = 'REDACTED',
                        owner_id = $2
                    WHERE owner_id = $3
                    """,
                    self.anonymization_marker,
                    f"{self.anonymization_marker}{user_id}",
                    user_id
                )
                summary["categories"]["cases"] = "anonymized"
                
                # 2. Anonymize traces
                await postgres_client.execute(
                    """
                    UPDATE traces
                    SET user_id = $1
                    WHERE user_id = $2
                    """,
                    f"{self.anonymization_marker}{user_id}",
                    user_id
                )
                summary["categories"]["traces"] = "anonymized"
                
                # 3. Anonymize user profile
                await postgres_client.execute(
                    """
                    UPDATE users
                    SET 
                        email = $1,
                        name = 'Anonymous User',
                        deleted_at = $2
                    WHERE user_id = $3
                    """,
                    f"anonymized_{user_id}@privacy.local",
                    datetime.utcnow(),
                    user_id
                )
                summary["categories"]["profile"] = "anonymized"
            
            logger.info(f"GDPR: {mode} completed for user {user_id}")
            
            return summary
        
        except Exception as e:
            logger.error(f"GDPR deletion failed for user {user_id}: {e}", exc_info=True)
            raise
    
    async def anonymize_address_in_reports(
        self,
        address: str,
        replacement: Optional[str] = None
    ) -> str:
        """
        Pseudonymize blockchain address in reports
        
        Args:
            address: Original address
            replacement: Optional replacement (default: hash)
        
        Returns:
            Pseudonymized address
        """
        if not replacement:
            import hashlib
            replacement = f"ADDR_{hashlib.sha256(address.encode()).hexdigest()[:8].upper()}"
        
        return replacement
    
    async def get_data_retention_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get data retention status for user
        
        Returns:
            Status of each data category
        """
        try:
            from app.db.postgres_client import postgres_client
            
            status = {
                "user_id": user_id,
                "checked_at": datetime.utcnow().isoformat(),
                "categories": {}
            }
            
            # Check cases
            cases_count = await postgres_client.fetch_val(
                "SELECT COUNT(*) FROM cases WHERE owner_id = $1",
                user_id
            )
            status["categories"]["cases"] = {
                "count": cases_count,
                "retention_period": "3 years",
                "will_expire_after": (datetime.utcnow() + timedelta(days=1095)).isoformat()
            }
            
            # Check traces
            traces_count = await postgres_client.fetch_val(
                "SELECT COUNT(*) FROM traces WHERE user_id = $1",
                user_id
            )
            status["categories"]["traces"] = {
                "count": traces_count,
                "retention_period": "1 year",
                "will_expire_after": (datetime.utcnow() + timedelta(days=365)).isoformat()
            }
            
            # Check audit logs
            audit_count = await postgres_client.fetch_val(
                "SELECT COUNT(*) FROM audit_logs WHERE user_id = $1",
                user_id
            )
            status["categories"]["audit_logs"] = {
                "count": audit_count,
                "retention_period": "2 years (compliance)",
                "will_expire_after": (datetime.utcnow() + timedelta(days=730)).isoformat()
            }
            
            return status
        
        except Exception as e:
            logger.error(f"Failed to get retention status for {user_id}: {e}")
            return {"error": str(e)}


# Global singleton
gdpr_service = GDPRService()
