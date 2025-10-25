"""
Database Query Optimizations
=============================

Implements database-level optimizations:
- Critical index creation
- Query plan optimization
- Batch operations
- Connection pooling tuning
- Prepared statements

Target: <50ms database queries, 10k+ concurrent connections
"""

from __future__ import annotations
import logging
from typing import List

logger = logging.getLogger(__name__)


# Critical indices for performance
PERFORMANCE_INDICES = [
    # Transaction tracing
    {
        "name": "idx_transactions_from_address",
        "table": "transactions",
        "columns": ["from_address", "timestamp"],
        "type": "btree",
        "priority": "critical"
    },
    {
        "name": "idx_transactions_to_address",
        "table": "transactions",
        "columns": ["to_address", "timestamp"],
        "type": "btree",
        "priority": "critical"
    },
    {
        "name": "idx_transactions_hash",
        "table": "transactions",
        "columns": ["tx_hash"],
        "type": "hash",
        "priority": "critical"
    },
    {
        "name": "idx_transactions_block",
        "table": "transactions",
        "columns": ["block_number", "chain"],
        "type": "btree",
        "priority": "high"
    },
    
    # Entity labels (fast lookups)
    {
        "name": "idx_labels_address_chain",
        "table": "entity_labels",
        "columns": ["address", "chain"],
        "type": "btree",
        "priority": "critical"
    },
    {
        "name": "idx_labels_category",
        "table": "entity_labels",
        "columns": ["category", "sub_category"],
        "type": "btree",
        "priority": "medium"
    },
    
    # Sanctions screening
    {
        "name": "idx_multi_sanctions_addresses",
        "table": "multi_sanctions",
        "columns": ["addresses"],
        "type": "gin",
        "priority": "critical"
    },
    {
        "name": "idx_multi_sanctions_jurisdictions",
        "table": "multi_sanctions",
        "columns": ["jurisdictions"],
        "type": "gin",
        "priority": "high"
    },
    
    # Risk scoring
    {
        "name": "idx_risk_scores_address",
        "table": "risk_scores",
        "columns": ["address", "chain", "updated_at"],
        "type": "btree",
        "priority": "critical"
    },
    
    # Cases (investigation)
    {
        "name": "idx_cases_org_status",
        "table": "cases",
        "columns": ["org_id", "status", "created_at"],
        "type": "btree",
        "priority": "high"
    },
    {
        "name": "idx_case_addresses_case",
        "table": "case_addresses",
        "columns": ["case_id", "address"],
        "type": "btree",
        "priority": "high"
    },
    
    # Alerts
    {
        "name": "idx_alerts_org_severity",
        "table": "alerts",
        "columns": ["org_id", "severity", "created_at"],
        "type": "btree",
        "priority": "high"
    },
    {
        "name": "idx_alerts_address",
        "table": "alerts",
        "columns": ["address", "chain"],
        "type": "btree",
        "priority": "medium"
    },
    
    # Users & Auth (fast session lookups)
    {
        "name": "idx_users_email",
        "table": "users",
        "columns": ["email"],
        "type": "hash",
        "priority": "critical"
    },
    {
        "name": "idx_users_org",
        "table": "users",
        "columns": ["org_id", "is_active"],
        "type": "btree",
        "priority": "high"
    },
    
    # Graph analytics
    {
        "name": "idx_graph_edges_from",
        "table": "graph_edges",
        "columns": ["from_address", "chain"],
        "type": "btree",
        "priority": "high"
    },
    {
        "name": "idx_graph_edges_to",
        "table": "graph_edges",
        "columns": ["to_address", "chain"],
        "type": "btree",
        "priority": "high"
    },
]


async def create_performance_indices(db_conn) -> dict:
    """
    Create all performance-critical indices
    
    Returns dict with creation status
    """
    results = {
        "created": [],
        "existing": [],
        "failed": []
    }
    
    for index in PERFORMANCE_INDICES:
        try:
            # Check if index exists
            check_query = f"""
                SELECT 1 FROM pg_indexes 
                WHERE indexname = '{index['name']}'
            """
            exists = await db_conn.fetchval(check_query)
            
            if exists:
                results["existing"].append(index["name"])
                continue
            
            # Create index
            columns = ", ".join(index["columns"])
            
            if index["type"] == "gin":
                # GIN index for arrays/JSON
                create_query = f"""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS {index['name']}
                    ON {index['table']} USING GIN ({columns})
                """
            elif index["type"] == "hash":
                # Hash index for equality lookups
                create_query = f"""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS {index['name']}
                    ON {index['table']} USING HASH ({columns})
                """
            else:
                # B-tree index (default)
                create_query = f"""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS {index['name']}
                    ON {index['table']} ({columns})
                """
            
            await db_conn.execute(create_query)
            results["created"].append(index["name"])
            logger.info(f"Created index: {index['name']} ({index['priority']} priority)")
        
        except Exception as e:
            results["failed"].append({"name": index["name"], "error": str(e)})
            logger.error(f"Failed to create index {index['name']}: {e}")
    
    return results


async def optimize_query_planner(db_conn):
    """Optimize PostgreSQL query planner settings"""
    optimizations = [
        # Increase work_mem for complex queries
        "SET work_mem = '256MB'",
        
        # Increase shared_buffers for caching
        "SET shared_buffers = '2GB'",
        
        # Optimize random page cost for SSD
        "SET random_page_cost = 1.1",
        
        # Increase effective_cache_size
        "SET effective_cache_size = '8GB'",
        
        # Enable parallel query execution
        "SET max_parallel_workers_per_gather = 4",
        
        # Optimize join algorithms
        "SET enable_hashjoin = ON",
        "SET enable_mergejoin = ON",
    ]
    
    for opt in optimizations:
        try:
            await db_conn.execute(opt)
            logger.info(f"Applied optimization: {opt}")
        except Exception as e:
            logger.warning(f"Failed to apply {opt}: {e}")


async def analyze_tables(db_conn, tables: List[str] = None):
    """
    Run ANALYZE on tables to update statistics
    
    Helps query planner make better decisions
    """
    if tables is None:
        # Analyze all critical tables
        tables = [
            "transactions",
            "entity_labels",
            "multi_sanctions",
            "risk_scores",
            "cases",
            "alerts",
            "users",
            "graph_edges"
        ]
    
    for table in tables:
        try:
            await db_conn.execute(f"ANALYZE {table}")
            logger.info(f"Analyzed table: {table}")
        except Exception as e:
            logger.warning(f"Failed to analyze {table}: {e}")


async def vacuum_tables(db_conn, tables: List[str] = None):
    """
    Run VACUUM on tables to reclaim space and update stats
    
    Should be run periodically (e.g., weekly)
    """
    if tables is None:
        tables = [
            "transactions",
            "entity_labels",
            "alerts",
            "graph_edges"
        ]
    
    for table in tables:
        try:
            # VACUUM ANALYZE combines both operations
            await db_conn.execute(f"VACUUM ANALYZE {table}")
            logger.info(f"Vacuumed table: {table}")
        except Exception as e:
            logger.warning(f"Failed to vacuum {table}: {e}")


# Optimized query templates (prepared statements)
QUERY_TEMPLATES = {
    "get_transactions_by_address": """
        SELECT * FROM transactions 
        WHERE (from_address = $1 OR to_address = $1)
        AND chain = $2
        AND timestamp >= $3
        ORDER BY timestamp DESC
        LIMIT $4
    """,
    
    "get_entity_label": """
        SELECT * FROM entity_labels
        WHERE address = $1 AND chain = $2
        LIMIT 1
    """,
    
    "check_sanctions": """
        SELECT * FROM multi_sanctions
        WHERE $1 = ANY(addresses)
        LIMIT 1
    """,
    
    "get_risk_score": """
        SELECT score, factors FROM risk_scores
        WHERE address = $1 AND chain = $2
        ORDER BY updated_at DESC
        LIMIT 1
    """,
    
    "get_user_by_email": """
        SELECT * FROM users
        WHERE email = $1 AND is_active = true
        LIMIT 1
    """,
}


async def prepare_statements(db_conn):
    """Prepare frequently used statements for faster execution"""
    for name, query in QUERY_TEMPLATES.items():
        try:
            await db_conn.execute(f"PREPARE {name} AS {query}")
            logger.info(f"Prepared statement: {name}")
        except Exception as e:
            # May already exist
            logger.debug(f"Statement {name} preparation: {e}")


# Connection pool settings (for asyncpg)
POOL_CONFIG = {
    "min_size": 10,           # Minimum connections
    "max_size": 100,          # Maximum connections (supports 10k concurrent via multiplexing)
    "max_queries": 50000,     # Max queries per connection before recycling
    "max_inactive_connection_lifetime": 300,  # 5 minutes
    "timeout": 60,            # Connection acquisition timeout
    "command_timeout": 30,    # Command execution timeout
}


def get_pool_config() -> dict:
    """Get optimized connection pool configuration"""
    return POOL_CONFIG.copy()
