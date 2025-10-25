"""
TimescaleDB Client
Für Time-Series Transaction Data und Metrics
"""

import logging
import os
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from app.config import settings

logger = logging.getLogger(__name__)


class PostgresClient:
    """TimescaleDB Client für Transaction Storage"""
    
    def __init__(self):
        # In Test-Umgebung keine Engine erstellen (vermeidet asyncpg-Abhängigkeit)
        is_test_env = os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TEST_MODE") == "1"
        if is_test_env:
            self.async_engine = None
            self.AsyncSessionLocal = None
            logger.info("PostgreSQL client initialization skipped in test mode")
            return

        # Async engine for async operations
        self.async_engine = create_async_engine(
            settings.POSTGRES_URL.replace('postgresql://', 'postgresql+asyncpg://'),
            echo=settings.DEBUG,
            pool_size=10,
            max_overflow=20
        )
        
        # Async session factory
        self.AsyncSessionLocal = sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("PostgreSQL/TimescaleDB client initialized")
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session"""
        if self.AsyncSessionLocal is None:
            raise RuntimeError("PostgreSQL AsyncSessionLocal not initialized (test mode)")
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def get_transactions(
        self,
        address: str,
        direction: str = "both",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Fetch transactions for an address
        
        Args:
            address: Ethereum address
            direction: 'incoming', 'outgoing', or 'both'
            start_time: Start timestamp
            end_time: End timestamp
            limit: Max results
        
        Returns:
            List of transactions
        """
        async with self.get_session() as session:
            query_parts = []
            params = {"address": address.lower(), "limit": limit}
            
            if direction in ["incoming", "both"]:
                incoming = """
                    SELECT 
                        tx_hash,
                        from_address,
                        to_address,
                        value,
                        block_number,
                        timestamp,
                        'incoming' as direction
                    FROM transactions
                    WHERE to_address = :address
                """
                if start_time:
                    incoming += " AND timestamp >= :start_time"
                    params["start_time"] = start_time
                if end_time:
                    incoming += " AND timestamp <= :end_time"
                    params["end_time"] = end_time
                
                query_parts.append(incoming)
            
            if direction in ["outgoing", "both"]:
                outgoing = """
                    SELECT 
                        tx_hash,
                        from_address,
                        to_address,
                        value,
                        block_number,
                        timestamp,
                        'outgoing' as direction
                    FROM transactions
                    WHERE from_address = :address
                """
                if start_time:
                    outgoing += " AND timestamp >= :start_time"
                if end_time:
                    outgoing += " AND timestamp <= :end_time"
                
                query_parts.append(outgoing)
            
            # Combine queries
            query = " UNION ALL ".join(query_parts)
            query += " ORDER BY timestamp DESC LIMIT :limit"
            
            result = await session.execute(text(query), params)
            
            transactions = []
            for row in result:
                transactions.append({
                    "tx_hash": row.tx_hash,
                    "from_address": row.from_address,
                    "to_address": row.to_address,
                    "value": str(row.value),
                    "block_number": row.block_number,
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "direction": row.direction
                })
            
            return transactions
    
    async def get_address_metrics(
        self,
        address: str,
        time_bucket: str = "1 day"
    ) -> List[Dict]:
        """
        Get time-series metrics for an address using TimescaleDB
        
        Args:
            address: Ethereum address
            time_bucket: Time bucket size (e.g., '1 hour', '1 day')
        
        Returns:
            Time-series metrics
        """
        async with self.get_session() as session:
            query = text("""
                SELECT 
                    time_bucket(:bucket, timestamp) AS bucket,
                    COUNT(*) as tx_count,
                    SUM(CASE WHEN from_address = :address THEN value ELSE 0 END) as outflow,
                    SUM(CASE WHEN to_address = :address THEN value ELSE 0 END) as inflow
                FROM transactions
                WHERE from_address = :address OR to_address = :address
                GROUP BY bucket
                ORDER BY bucket DESC
                LIMIT 100
            """)
            
            result = await session.execute(
                query,
                {"address": address.lower(), "bucket": time_bucket}
            )
            
            metrics = []
            for row in result:
                metrics.append({
                    "timestamp": row.bucket.isoformat(),
                    "tx_count": row.tx_count,
                    "outflow": str(row.outflow),
                    "inflow": str(row.inflow)
                })
            
            return metrics
    
    async def verify_connectivity(self):
        """Verify database connection"""
        async with self.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    
    async def close(self):
        """Close database connections"""
        if self.async_engine is not None:
            await self.async_engine.dispose()
            logger.info("PostgreSQL connections closed")


# Singleton instance with safe fallback for test environments
try:
    postgres_client = PostgresClient()
except ModuleNotFoundError:
    # asyncpg not installed in test env; enable TEST_MODE and re-init without engine
    os.environ["TEST_MODE"] = "1"
    postgres_client = PostgresClient()
