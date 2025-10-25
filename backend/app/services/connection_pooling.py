"""
Advanced Database Connection Pooling Service
Optimizes database connections for high-performance blockchain forensics
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime

from app.observability.metrics import (
    DB_CONNECTION_POOL_SIZE, DB_CONNECTION_POOL_ACTIVE,
    DB_CONNECTION_POOL_IDLE, DB_CONNECTION_POOL_WAITING,
    DB_CONNECTION_CREATE_TIME, DB_CONNECTION_REUSE_TIME
)

logger = logging.getLogger(__name__)


@dataclass
class ConnectionMetrics:
    """Connection pool metrics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    waiting_connections: int = 0
    connection_create_time: float = 0.0
    connection_reuse_time: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)


class ConnectionPool:
    """
    Advanced connection pool for database connections

    Features:
    - Configurable pool sizes
    - Connection health monitoring
    - Automatic connection recycling
    - Metrics collection
    - Graceful shutdown
    """

    def __init__(
        self,
        connection_factory,
        min_size: int = 5,
        max_size: int = 20,
        max_idle_time: int = 300,  # 5 minutes
        health_check_interval: int = 60,  # 1 minute
        connection_timeout: int = 30,
        **connection_kwargs
    ):
        self.connection_factory = connection_factory
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.health_check_interval = health_check_interval
        self.connection_timeout = connection_timeout
        self.connection_kwargs = connection_kwargs

        # Connection pools
        self._available: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._in_use: set = set()
        self._creating: set = set()

        # Control flags
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None

        # Metrics
        self.metrics = ConnectionMetrics()

        logger.info(f"Initialized connection pool: min={min_size}, max={max_size}")

    async def start(self) -> None:
        """Start the connection pool"""
        if self._running:
            return

        self._running = True

        # Create initial connections
        for _ in range(self.min_size):
            await self._create_connection()

        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info(f"Connection pool started with {len(self._in_use) + self._available.qsize()} connections")

    async def stop(self) -> None:
        """Stop the connection pool and close all connections"""
        if not self._running:
            return

        self._running = False

        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()

        # Close all connections
        while not self._available.empty():
            try:
                conn = await self._available.get()
                await self._close_connection(conn)
            except asyncio.QueueEmpty:
                break

        # Close in-use connections (they should finish their work)
        for conn in list(self._in_use):
            await self._close_connection(conn)

        logger.info("Connection pool stopped")

    @asynccontextmanager
    async def acquire(self, timeout: Optional[float] = None):
        """Acquire a connection from the pool"""
        start_time = time.time()

        try:
            # Try to get an available connection
            try:
                conn = self._available.get_nowait()
                DB_CONNECTION_REUSE_TIME.observe(time.time() - start_time)
            except asyncio.QueueEmpty:
                # No available connection, create new one or wait
                if len(self._in_use) + len(self._creating) < self.max_size:
                    await self._create_connection()
                    conn = self._available.get_nowait()
                else:
                    # Wait for available connection
                    self.metrics.waiting_connections += 1
                    DB_CONNECTION_POOL_WAITING.inc()

                    if timeout is None:
                        timeout = self.connection_timeout

                    try:
                        conn = await asyncio.wait_for(self._available.get(), timeout=timeout)
                    finally:
                        self.metrics.waiting_connections -= 1
                        DB_CONNECTION_POOL_WAITING.dec()

            # Mark as in use
            self._in_use.add(conn)
            self.metrics.active_connections = len(self._in_use)
            self.metrics.idle_connections = self._available.qsize()

            DB_CONNECTION_POOL_ACTIVE.set(len(self._in_use))
            DB_CONNECTION_POOL_IDLE.set(self._available.qsize())

            try:
                yield conn
            finally:
                # Return connection to pool
                self._in_use.discard(conn)
                await self._available.put(conn)

                self.metrics.active_connections = len(self._in_use)
                self.metrics.idle_connections = self._available.qsize()

                DB_CONNECTION_POOL_ACTIVE.set(len(self._in_use))
                DB_CONNECTION_POOL_IDLE.set(self._available.qsize())

        except Exception as e:
            logger.error(f"Error acquiring database connection: {e}")
            raise

    async def _create_connection(self) -> None:
        """Create a new database connection"""
        if len(self._in_use) + len(self._creating) >= self.max_size:
            raise RuntimeError("Connection pool exhausted")

        self._creating.add("creating")
        self.metrics.total_connections += 1

        start_time = time.time()
        try:
            conn = await self.connection_factory(**self.connection_kwargs)
            await self._available.put(conn)

            create_time = time.time() - start_time
            self.metrics.connection_create_time = create_time
            DB_CONNECTION_CREATE_TIME.observe(create_time)

            logger.debug(f"Created new database connection in {create_time:.3f}s")

        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            self.metrics.total_connections -= 1
            raise
        finally:
            self._creating.discard("creating")

    async def _close_connection(self, conn) -> None:
        """Close a database connection"""
        try:
            if hasattr(conn, 'close'):
                await conn.close()
            elif hasattr(conn, 'disconnect'):
                await conn.disconnect()
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")

    async def _health_check_loop(self) -> None:
        """Background task to monitor connection health"""
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)

                # Check for stale connections
                stale_connections = []
                current_time = datetime.utcnow()

                # This is a simplified health check
                # In a real implementation, you'd ping each connection
                if self._available.qsize() > self.min_size:
                    # Remove excess idle connections
                    try:
                        excess_conn = self._available.get_nowait()
                        stale_connections.append(excess_conn)
                    except asyncio.QueueEmpty:
                        pass

                # Close stale connections
                for conn in stale_connections:
                    await self._close_connection(conn)

                # Update metrics
                self.metrics.last_updated = current_time
                DB_CONNECTION_POOL_SIZE.set(self.metrics.total_connections)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection health check: {e}")
                await asyncio.sleep(self.health_check_interval)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            "total_connections": self.metrics.total_connections,
            "active_connections": self.metrics.active_connections,
            "idle_connections": self.metrics.idle_connections,
            "waiting_connections": self.metrics.waiting_connections,
            "pool_utilization": (self.metrics.active_connections / max(1, self.metrics.total_connections)) * 100,
            "connection_create_time_avg": self.metrics.connection_create_time,
            "last_updated": self.metrics.last_updated.isoformat()
        }


# Global connection pools
postgres_pool: Optional[ConnectionPool] = None
neo4j_pool: Optional[ConnectionPool] = None
redis_pool: Optional[ConnectionPool] = None


async def initialize_connection_pools() -> None:
    """Initialize all database connection pools"""
    global postgres_pool, neo4j_pool, redis_pool

    # For now, use mock connections to avoid database dependency issues
    logger.info("Initializing connection pools with mock connections for testing")

    # PostgreSQL connection pool
    async def postgres_factory(**kwargs):
        return MockConnection("postgres")

    postgres_pool = ConnectionPool(
        connection_factory=postgres_factory,
        min_size=2,
        max_size=5,
    )
    await postgres_pool.start()

    # Neo4j connection pool
    async def neo4j_factory(**kwargs):
        return MockConnection("neo4j")

    neo4j_pool = ConnectionPool(
        connection_factory=neo4j_factory,
        min_size=1,
        max_size=3,
    )
    await neo4j_pool.start()

    # Redis connection pool
    async def redis_factory(**kwargs):
        return MockConnection("redis")

    redis_pool = ConnectionPool(
        connection_factory=redis_factory,
        min_size=2,
        max_size=5,
    )
    await redis_pool.start()

    logger.info("All database connection pools initialized with mock connections")


async def shutdown_connection_pools() -> None:
    """Shutdown all database connection pools"""
    global postgres_pool, neo4j_pool, redis_pool

    if postgres_pool:
        await postgres_pool.stop()
    if neo4j_pool:
        await neo4j_pool.stop()
    if redis_pool:
        await redis_pool.stop()

    logger.info("All database connection pools shut down")


class MockConnection:
    """Mock database connection for testing"""

    def __init__(self, db_type: str):
        self.db_type = db_type
        self.connected = True

    async def close(self):
        """Close the mock connection"""
        self.connected = False

    async def ping(self) -> bool:
        """Ping the mock connection"""
        return self.connected


# Database connection context managers
@asynccontextmanager
async def get_postgres_connection():
    """Get a PostgreSQL connection from the pool"""
    if postgres_pool is None:
        raise RuntimeError("PostgreSQL connection pool not initialized")

    async with postgres_pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_neo4j_connection():
    """Get a Neo4j connection from the pool"""
    if neo4j_pool is None:
        raise RuntimeError("Neo4j connection pool not initialized")

    async with neo4j_pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_redis_connection():
    """Get a Redis connection from the pool"""
    if redis_pool is None:
        raise RuntimeError("Redis connection pool not initialized")

    async with redis_pool.acquire() as conn:
        yield conn


def get_pool_stats() -> Dict[str, Any]:
    """Get statistics for all connection pools"""
    stats = {}

    if postgres_pool:
        stats["postgres"] = postgres_pool.get_stats()
    if neo4j_pool:
        stats["neo4j"] = neo4j_pool.get_stats()
    if redis_pool:
        stats["redis"] = redis_pool.get_stats()

    return stats
