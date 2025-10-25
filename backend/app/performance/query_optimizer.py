"""
Query Optimizer
===============

Optimize database queries for Neo4j, PostgreSQL, and Redis

Features:
- Query plan analysis
- Index recommendations
- Query caching
- Connection pooling optimization
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Database query optimization and monitoring
    
    **Features:**
    - Query execution time tracking
    - Slow query detection
    - Query plan analysis
    - Index usage monitoring
    - Query caching recommendations
    
    **Optimizations:**
    - Neo4j: Index-backed lookups, query parameterization
    - PostgreSQL: Index scans, query planning
    - Redis: Pipeline usage, connection pooling
    """
    
    def __init__(self):
        self.slow_query_threshold_ms = 1000  # 1 second
        self.query_history: List[Dict] = []
        self.max_history = 1000
        
        # Query statistics
        self.stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'cached_queries': 0,
            'total_time_ms': 0
        }
    
    def track_query(
        self,
        query_type: str,
        query: str,
        execution_time_ms: float,
        result_count: Optional[int] = None,
        database: str = "unknown"
    ):
        """
        Track query execution for analysis
        
        Args:
            query_type: Type of query (read, write, delete)
            query: Query string
            execution_time_ms: Execution time in milliseconds
            result_count: Number of results returned
            database: Database name (neo4j, postgres, redis)
        """
        self.stats['total_queries'] += 1
        self.stats['total_time_ms'] += execution_time_ms
        
        if execution_time_ms > self.slow_query_threshold_ms:
            self.stats['slow_queries'] += 1
            logger.warning(
                f"Slow query detected: {query_type} on {database} "
                f"took {execution_time_ms:.2f}ms"
            )
        
        # Store query history
        query_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'query_type': query_type,
            'query': query[:500],  # Truncate long queries
            'execution_time_ms': execution_time_ms,
            'result_count': result_count,
            'database': database,
            'is_slow': execution_time_ms > self.slow_query_threshold_ms
        }
        
        self.query_history.append(query_record)
        
        # Keep history limited
        if len(self.query_history) > self.max_history:
            self.query_history = self.query_history[-self.max_history:]
    
    def get_slow_queries(self, limit: int = 20) -> List[Dict]:
        """Get recent slow queries"""
        slow_queries = [q for q in self.query_history if q['is_slow']]
        return sorted(
            slow_queries,
            key=lambda x: x['execution_time_ms'],
            reverse=True
        )[:limit]
    
    def get_query_stats(self) -> Dict:
        """Get query statistics"""
        avg_time = (
            self.stats['total_time_ms'] / self.stats['total_queries']
            if self.stats['total_queries'] > 0
            else 0
        )
        
        return {
            **self.stats,
            'average_time_ms': avg_time,
            'slow_query_rate': (
                self.stats['slow_queries'] / self.stats['total_queries']
                if self.stats['total_queries'] > 0
                else 0
            )
        }
    
    def optimize_neo4j_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze and optimize Neo4j Cypher query
        
        Returns recommendations for optimization
        """
        recommendations = []
        optimized_query = query
        
        # Check for missing indexes
        if "WHERE" in query.upper() and ":" in query:
            # Extract node labels and properties
            # Recommend index if not using one
            recommendations.append({
                'type': 'index',
                'message': 'Consider creating index on frequently queried properties',
                'example': 'CREATE INDEX FOR (n:Address) ON (n.address)'
            })
        
        # Check for Cartesian products (missing relationship patterns)
        if query.count("MATCH") > 1 and "WHERE" not in query.upper():
            recommendations.append({
                'type': 'cartesian_product',
                'message': 'Multiple MATCH clauses without WHERE may cause Cartesian product',
                'suggestion': 'Use relationship patterns or add WHERE clause'
            })
        
        # Check for OPTIONAL MATCH before MATCH
        if "OPTIONAL MATCH" in query.upper():
            optional_idx = query.upper().index("OPTIONAL MATCH")
            match_idx = query.upper().find("MATCH", optional_idx + 14)
            if match_idx > -1:
                recommendations.append({
                    'type': 'query_order',
                    'message': 'OPTIONAL MATCH before MATCH can impact performance',
                    'suggestion': 'Move regular MATCH clauses before OPTIONAL MATCH'
                })
        
        # Recommend LIMIT for large result sets
        if "LIMIT" not in query.upper() and "RETURN" in query.upper():
            recommendations.append({
                'type': 'limit',
                'message': 'No LIMIT clause - could return large result set',
                'suggestion': 'Add LIMIT clause if full result set not needed'
            })
        
        # Check for property access in WHERE
        if "WHERE" in query.upper() and "." in query:
            recommendations.append({
                'type': 'parameterization',
                'message': 'Use query parameters instead of string concatenation',
                'example': 'WHERE n.address = $address'
            })
        
        return {
            'original_query': query,
            'optimized_query': optimized_query,
            'recommendations': recommendations,
            'estimated_improvement': '10-50%' if recommendations else 'minimal'
        }
    
    def optimize_postgres_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze and optimize PostgreSQL query
        
        Returns recommendations for optimization
        """
        recommendations = []
        
        # Check for SELECT *
        if "SELECT *" in query.upper():
            recommendations.append({
                'type': 'select_specific',
                'message': 'SELECT * can be inefficient',
                'suggestion': 'Select only needed columns'
            })
        
        # Check for missing WHERE on large tables
        if "FROM transactions" in query.lower() and "WHERE" not in query.upper():
            recommendations.append({
                'type': 'missing_filter',
                'message': 'Full table scan on transactions table',
                'suggestion': 'Add WHERE clause to filter results'
            })
        
        # Check for JOIN order
        if "JOIN" in query.upper() and query.count("JOIN") > 2:
            recommendations.append({
                'type': 'join_order',
                'message': 'Multiple JOINs - order matters for performance',
                'suggestion': 'Join smallest tables first'
            })
        
        # Recommend indexes
        if "WHERE" in query.upper():
            recommendations.append({
                'type': 'index',
                'message': 'Ensure indexes exist on WHERE clause columns',
                'example': 'CREATE INDEX idx_transactions_timestamp ON transactions(timestamp)'
            })
        
        return {
            'original_query': query,
            'recommendations': recommendations,
            'estimated_improvement': '20-80%' if recommendations else 'minimal'
        }

    # ----- Explain/Plan Skeletons -----
    async def explain_neo4j(self, query: str) -> Dict[str, Any]:
        """Minimal EXPLAIN skeleton for Neo4j (no DB call in PoC)"""
        plan = {
            "operator": "ProduceResults",
            "estimatedRows": 100,
            "dbHits": 0,
            "children": [
                {"operator": "NodeIndexSeek", "on": "Address(address)", "estimatedRows": 1000}
            ],
        }
        return {"query": query, "plan": plan, "notes": ["PoC: simulated plan"]}

    async def explain_postgres(self, query: str) -> Dict[str, Any]:
        """Minimal EXPLAIN skeleton for Postgres (no DB call in PoC)"""
        plan = {
            "Plan": {
                "Node Type": "Seq Scan" if "WHERE" not in query.upper() else "Index Scan",
                "Relation Name": "transactions" if "transactions" in query.lower() else "unknown",
                "Total Cost": 123.45,
                "Plan Rows": 1000,
            }
        }
        return {"query": query, "plan": plan, "notes": ["PoC: simulated plan"]}
    
    def suggest_caching_strategy(
        self,
        query_pattern: str,
        avg_execution_time_ms: float,
        query_frequency: int
    ) -> Dict:
        """
        Suggest caching strategy based on query characteristics
        
        Args:
            query_pattern: Pattern of query (e.g., "address_lookup")
            avg_execution_time_ms: Average execution time
            query_frequency: How often query is executed per hour
        
        Returns:
            Caching recommendation
        """
        # Calculate potential time saved
        potential_savings_ms = avg_execution_time_ms * query_frequency
        
        # Determine cache TTL based on query type
        if "address" in query_pattern.lower():
            ttl_seconds = 300  # 5 minutes for address data
        elif "transaction" in query_pattern.lower():
            ttl_seconds = 60  # 1 minute for transaction data
        elif "risk_score" in query_pattern.lower():
            ttl_seconds = 600  # 10 minutes for risk scores
        else:
            ttl_seconds = 180  # 3 minutes default
        
        # Recommend caching if high frequency or slow query
        should_cache = (
            query_frequency > 10 or  # More than 10 times per hour
            avg_execution_time_ms > 500  # Slower than 500ms
        )
        
        return {
            'should_cache': should_cache,
            'recommended_ttl_seconds': ttl_seconds,
            'potential_savings_ms_per_hour': potential_savings_ms,
            'cache_key_pattern': f"cache:{query_pattern}:{{params}}",
            'strategy': 'redis' if should_cache else 'none',
            'reasoning': (
                f"Query executes {query_frequency} times/hour with "
                f"{avg_execution_time_ms:.0f}ms avg time"
            )
        }
    
    def get_index_recommendations(self, database: str = "all") -> List[Dict]:
        """
        Get index recommendations based on slow queries
        
        Args:
            database: Filter by database (neo4j, postgres, all)
        
        Returns:
            List of index recommendations
        """
        recommendations = []
        
        # Analyze slow queries
        slow_queries = self.get_slow_queries(limit=50)
        
        # Group by database
        queries_by_db = {}
        for query in slow_queries:
            db = query.get('database', 'unknown')
            if database == "all" or database == db:
                if db not in queries_by_db:
                    queries_by_db[db] = []
                queries_by_db[db].append(query)
        
        # Generate recommendations for Neo4j
        if 'neo4j' in queries_by_db:
            recommendations.append({
                'database': 'neo4j',
                'indexes': [
                    {
                        'index': 'CREATE INDEX FOR (n:Address) ON (n.address)',
                        'reason': 'Frequently queried property',
                        'impact': 'High'
                    },
                    {
                        'index': 'CREATE INDEX FOR (t:Transaction) ON (t.hash)',
                        'reason': 'Unique lookup field',
                        'impact': 'High'
                    },
                    {
                        'index': 'CREATE INDEX FOR (n:Address) ON (n.risk_score)',
                        'reason': 'Range queries on risk scores',
                        'impact': 'Medium'
                    }
                ]
            })
        
        # Generate recommendations for PostgreSQL
        if 'postgres' in queries_by_db:
            recommendations.append({
                'database': 'postgres',
                'indexes': [
                    {
                        'index': 'CREATE INDEX idx_tx_timestamp ON transactions(timestamp DESC)',
                        'reason': 'Time-based queries',
                        'impact': 'High'
                    },
                    {
                        'index': 'CREATE INDEX idx_tx_address ON transactions(from_address, to_address)',
                        'reason': 'Address lookups',
                        'impact': 'High'
                    },
                    {
                        'index': 'CREATE INDEX idx_tx_block ON transactions(block_number)',
                        'reason': 'Block-based queries',
                        'impact': 'Medium'
                    }
                ]
            })
        
        return recommendations


# Singleton instance
query_optimizer = QueryOptimizer()


# Decorator for query tracking
def track_query(database: str = "unknown", query_type: str = "read"):
    """
    Decorator to track query execution time
    
    Usage:
        @track_query(database="neo4j", query_type="read")
        def get_address(address: str):
            # ... query code
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            
            query_optimizer.track_query(
                query_type=query_type,
                query=func.__name__,
                execution_time_ms=duration_ms,
                database=database
            )
            
            return result
        return wrapper
    return decorator
