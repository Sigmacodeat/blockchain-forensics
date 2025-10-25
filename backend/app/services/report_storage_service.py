"""Report Storage Service - S3-based persistent storage"""

import logging
import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta
import os
import base64

logger = logging.getLogger(__name__)

try:
    import boto3
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

class ReportStorageService:
    """S3-based report storage"""
    
    def __init__(self):
        self.enabled = S3_AVAILABLE and os.getenv("REPORTS_S3_ENABLED") == "true"
        if self.enabled:
            self.s3 = boto3.client('s3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "us-east-1"))
            self.bucket = os.getenv("REPORTS_S3_BUCKET", "forensics-reports")
    
    async def store_report(self, report_id: str, content: bytes, format: str, user_id: str) -> str:
        """Store report and return download URL"""
        if not self.enabled:
            # Fallback: data URI
            b64 = base64.b64encode(content).decode()
            return f"data:application/{format};base64,{b64}"
        
        try:
            key = f"reports/{user_id}/{report_id}.{format}"
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=content,
                ServerSideEncryption='AES256',
                Metadata={'user-id': user_id, 'report-id': report_id})
            
            url = self.s3.generate_presigned_url('get_object',
                Params={'Bucket': self.bucket, 'Key': key}, ExpiresIn=604800)
            
            await self._save_metadata(report_id, user_id, key, url, format, len(content))
            return url
        except Exception as e:
            logger.error(f"S3 storage failed: {e}")
            return f"data:application/{format};base64,{base64.b64encode(content).decode()}"
    
    async def _save_metadata(self, report_id, user_id, key, url, format, size):
        from app.db.postgres_client import postgres_client
        await postgres_client.execute(
            "INSERT INTO reports (report_id, user_id, s3_key, url, format, size_bytes, expires_at) VALUES ($1,$2,$3,$4,$5,$6,$7)",
            report_id, user_id, key, url, format, size, datetime.utcnow() + timedelta(days=7))

report_storage = ReportStorageService()
