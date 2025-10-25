"""
PostgreSQL Database Client
User persistence and relational data
"""

import logging
import time
import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import os
try:
    import asyncpg  # type: ignore
    _ASYNCPG_AVAILABLE = True
except Exception:
    asyncpg = None  # type: ignore
    _ASYNCPG_AVAILABLE = False
from app.config import settings

logger = logging.getLogger(__name__)


class PostgresClient:
    """
    PostgreSQL Client for user management and relational data
    
    **Schema:**
    - users: User accounts
    - audit_logs: Audit trail
    - sessions: Active sessions
    - api_keys: API key management
    """
    
    def __init__(self):
        self.pool: Optional["asyncpg.Pool"] = None  # type: ignore
        self._connection_stats = {
            "total_connections": 0,
            "failed_connections": 0,
            "last_connection_attempt": 0.0,
            "pool_size": 0,
        }
    
    async def connect(self):
        """Establish connection pool with optimized settings"""
        if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST") or not _ASYNCPG_AVAILABLE:
            logger.warning("PostgreSQL connect skipped (test mode or asyncpg not available)")
            return
        try:
            start_time = time.time()
            self.pool = await asyncpg.create_pool(  # type: ignore
                settings.POSTGRES_URL,
                min_size=10,  # Increased for better concurrency
                max_size=50,  # Increased for high load scenarios
                max_queries=50000,  # Prevent query queue buildup
                max_inactive_connection_lifetime=300.0,  # 5 minutes
                command_timeout=60,
                server_settings={
                    'jit': 'off',  # Disable JIT for predictable performance
                    'application_name': 'blockchain-forensics',
                },
                init=self._init_connection
            )
            connection_time = time.time() - start_time
            self._connection_stats["total_connections"] += 1
            self._connection_stats["last_connection_attempt"] = time.time()
            logger.info(f"✅ PostgreSQL connected in {connection_time:.2f}s")
            # Initialize schema
            await self.init_schema()
        except Exception as e:
            self._connection_stats["failed_connections"] += 1
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            raise
    
    async def _init_connection(self, conn):
        """Initialize connection with performance optimizations"""
        # Set connection-level settings for better performance
        try:
            await conn.execute("SET statement_timeout = '60s'")
            await conn.execute("SET idle_in_transaction_session_timeout = '300s'")
            await conn.execute("SET lock_timeout = '30s'")
        except Exception as e:
            logger.warning(f"PostgreSQL connection init settings failed: {e}")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL disconnected")
    
    async def init_schema(self):
        """Initialize database schema"""
        if not self.pool:
            return
        
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
                    organization VARCHAR(255),
                    is_active BOOLEAN DEFAULT TRUE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    verification_token TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    last_login TIMESTAMP
                )
            """)

            # Knowledge base documents (simple RAG store)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS kb_docs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    path TEXT,
                    title TEXT,
                    content TEXT,
                    ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

            # Optional pgvector extension and embeddings table
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS kb_embeddings (
                        doc_id UUID REFERENCES kb_docs(id) ON DELETE CASCADE,
                        embedding vector(1536)
                    )
                """)
            except Exception as e:
                logger.warning(f"pgvector not available or embeddings table creation failed: {e}")
            
            # Audit logs table (with TimescaleDB hypertable)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    user_email VARCHAR(255),
                    user_role VARCHAR(50),
                    action VARCHAR(100) NOT NULL,
                    resource_type VARCHAR(100),
                    resource_id TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    ip_address INET,
                    user_agent TEXT,
                    metadata JSONB,
                    session_id TEXT,
                    request_id TEXT
                )
            """)
            
            # Create hypertable for audit_logs (if TimescaleDB extension is available)
            try:
                await conn.execute("""
                    SELECT create_hypertable('audit_logs', 'timestamp', 
                        if_not_exists => TRUE)
                """)
                logger.info("✅ TimescaleDB hypertable created for audit_logs")
            except Exception as e:
                logger.warning(f"TimescaleDB extension not available: {e}")
            
            # Sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL,
                    refresh_token_hash TEXT,
                    ip_address INET,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Password reset tokens
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Labels (dev → prod persistence)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS labels (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    chain VARCHAR(50) NOT NULL,
                    address TEXT NOT NULL,
                    label TEXT NOT NULL,
                    category VARCHAR(100) DEFAULT 'generic',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Ensure compatibility with infra schema: add missing column if pre-created without 'chain'
            await conn.execute("""
                ALTER TABLE labels
                ADD COLUMN IF NOT EXISTS chain VARCHAR(50);
            """)
            
            # Compliance watchlist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS compliance_watchlist (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    chain VARCHAR(50) NOT NULL,
                    address TEXT NOT NULL,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # VASP risk scoring history (persistent storage)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS vasp_risk_records (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    vasp_id TEXT NOT NULL,
                    vasp_name TEXT NOT NULL,
                    scored_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    overall_risk TEXT NOT NULL,
                    risk_score DOUBLE PRECISION NOT NULL,
                    compliance_status TEXT NOT NULL,
                    sanctions_hit BOOLEAN NOT NULL DEFAULT FALSE,
                    pep_hit BOOLEAN NOT NULL DEFAULT FALSE,
                    adverse_media_hit BOOLEAN NOT NULL DEFAULT FALSE,
                    adverse_media_count INTEGER NOT NULL DEFAULT 0,
                    recommended_action TEXT NOT NULL,
                    risk_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
                    compliance_issues JSONB NOT NULL DEFAULT '[]'::jsonb,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)

            # Web analytics events (First-Party)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS web_events (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    user_id TEXT,
                    session_id TEXT,
                    event TEXT NOT NULL,
                    properties JSONB,
                    path TEXT,
                    referrer TEXT,
                    ua TEXT,
                    ip_hash TEXT,
                    method TEXT,
                    status INT,
                    duration DOUBLE PRECISION
                )
            """)
            
            # Indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
                CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
                CREATE INDEX IF NOT EXISTS idx_labels_chain_address ON labels(chain, address);
                CREATE INDEX IF NOT EXISTS idx_cw_chain_address ON compliance_watchlist(chain, address);
                CREATE UNIQUE INDEX IF NOT EXISTS uq_labels_chain_address_label ON labels(chain, address, label);
                CREATE UNIQUE INDEX IF NOT EXISTS uq_cw_chain_address ON compliance_watchlist(chain, address);
                CREATE INDEX IF NOT EXISTS idx_web_events_ts ON web_events(ts DESC);
                CREATE INDEX IF NOT EXISTS idx_web_events_event ON web_events(event);
                CREATE INDEX IF NOT EXISTS idx_web_events_user ON web_events(user_id);
                CREATE INDEX IF NOT EXISTS idx_web_events_session ON web_events(session_id);
                CREATE INDEX IF NOT EXISTS idx_kb_docs_ts ON kb_docs(ts DESC);
                CREATE INDEX IF NOT EXISTS idx_kb_docs_title ON kb_docs(title);
                -- embeddings index optional (if vector ext is present)
            """)
            try:
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_kb_embeddings_cosine ON kb_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                """)
            except Exception as e:
                logger.warning(f"Could not create ivfflat index for kb_embeddings: {e}")

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_vasp_risk_records_vasp_id_scored_at
                ON vasp_risk_records(vasp_id, scored_at DESC);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_vasp_risk_records_scored_at
                ON vasp_risk_records(scored_at DESC);
            """)


            logger.info("✅ Database schema initialized")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool with monitoring"""
        if not self.pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        
        start_time = time.time()
        try:
            async with self.pool.acquire() as conn:
                self._connection_stats["pool_size"] = self.pool.get_size()
                yield conn
        finally:
            connection_time = time.time() - start_time
            # Log slow queries (optional, can be disabled in production)
            if connection_time > 1.0:  # More than 1 second
                logger.warning(f"Slow PostgreSQL query detected: {connection_time:.2f}s")
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if not self.pool:
            return self._connection_stats
        
        return {
            **self._connection_stats,
            "pool_size": self.pool.get_size(),
            "pool_idle": self.pool.get_idle_size(),
        }


# Singleton instance with safe fallback
try:
    postgres_client = PostgresClient()
except Exception:
    os.environ["TEST_MODE"] = "1"
    postgres_client = PostgresClient()
