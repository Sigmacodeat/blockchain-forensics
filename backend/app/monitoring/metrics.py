"""
Prometheus Metrics für Enterprise Features
===========================================

Metrics für:
- Universal Screening
- Custom Entities
- Advanced Indirect Risk
- Custom Ledgers
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Universal Screening Metrics
# ============================================================================

universal_screening_requests = Counter(
    'universal_screening_requests_total',
    'Total Universal Screening requests',
    ['status', 'chains_count']
)

universal_screening_duration = Histogram(
    'universal_screening_duration_seconds',
    'Universal Screening request duration',
    ['chains_count'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

universal_screening_chains_screened = Histogram(
    'universal_screening_chains_screened',
    'Number of chains screened per request',
    buckets=[1, 5, 10, 20, 50, 90, 100]
)

universal_screening_risk_score = Histogram(
    'universal_screening_risk_score',
    'Risk scores from Universal Screening',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

universal_screening_sanctioned = Counter(
    'universal_screening_sanctioned_total',
    'Sanctioned addresses found',
    ['chain_id']
)

# ============================================================================
# Custom Entities Metrics
# ============================================================================

custom_entities_total = Gauge(
    'custom_entities_total',
    'Total number of custom entities'
)

custom_entities_addresses = Histogram(
    'custom_entities_addresses_per_entity',
    'Number of addresses per entity',
    buckets=[1, 10, 100, 1000, 10000, 100000, 1000000]
)

custom_entities_operations = Counter(
    'custom_entities_operations_total',
    'Custom entities operations',
    ['operation', 'status']
)

custom_entities_insights_duration = Histogram(
    'custom_entities_insights_duration_seconds',
    'Duration to compute aggregate insights',
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# ============================================================================
# Advanced Indirect Risk Metrics
# ============================================================================

indirect_risk_requests = Counter(
    'indirect_risk_requests_total',
    'Total indirect risk analysis requests',
    ['status', 'max_hops']
)

indirect_risk_duration = Histogram(
    'indirect_risk_duration_seconds',
    'Indirect risk analysis duration',
    ['max_hops'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

indirect_risk_paths_found = Histogram(
    'indirect_risk_paths_found',
    'Number of paths found per analysis',
    buckets=[1, 10, 100, 500, 1000, 5000, 10000]
)

indirect_risk_score = Histogram(
    'indirect_risk_aggregate_score',
    'Aggregate indirect risk scores',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

indirect_risk_chains_analyzed = Histogram(
    'indirect_risk_chains_analyzed',
    'Number of chains analyzed per request',
    buckets=[1, 2, 5, 10, 20, 50, 90]
)

# ============================================================================
# Custom Ledgers Metrics
# ============================================================================

custom_ledgers_total = Gauge(
    'custom_ledgers_total',
    'Total number of custom ledgers'
)

custom_ledgers_transfers = Histogram(
    'custom_ledgers_transfers_per_ledger',
    'Number of transfers per ledger',
    buckets=[1, 100, 1000, 10000, 100000, 1000000, 10000000]
)

custom_ledgers_csv_upload = Counter(
    'custom_ledgers_csv_uploads_total',
    'CSV uploads to ledgers',
    ['status']
)

custom_ledgers_csv_size = Histogram(
    'custom_ledgers_csv_size_mb',
    'CSV upload file sizes in MB',
    buckets=[0.1, 1, 10, 50, 100, 250, 500]
)

custom_ledgers_analysis_duration = Histogram(
    'custom_ledgers_analysis_duration_seconds',
    'Ledger analysis duration',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# ============================================================================
# API Performance Metrics
# ============================================================================

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method', 'status'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status']
)

# ============================================================================
# System Metrics
# ============================================================================

active_users = Gauge(
    'active_users',
    'Currently active users'
)

database_connections = Gauge(
    'database_connections',
    'Active database connections'
)

redis_connections = Gauge(
    'redis_connections',
    'Active Redis connections'
)

# ============================================================================
# Decorators
# ============================================================================

def track_universal_screening():
    """Decorator to track Universal Screening metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            chains_count = 0
            status = 'success'
            
            try:
                result = await func(*args, **kwargs)
                
                # Extract metrics from result
                if hasattr(result, 'total_chains_checked'):
                    chains_count = result.total_chains_checked
                    universal_screening_chains_screened.observe(chains_count)
                
                if hasattr(result, 'aggregate_risk_score'):
                    universal_screening_risk_score.observe(result.aggregate_risk_score)
                
                if hasattr(result, 'is_sanctioned_any_chain') and result.is_sanctioned_any_chain:
                    for chain in result.screened_chains:
                        universal_screening_sanctioned.labels(chain_id=chain).inc()
                
                return result
                
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                universal_screening_duration.labels(chains_count=str(chains_count)).observe(duration)
                universal_screening_requests.labels(
                    status=status,
                    chains_count=str(chains_count)
                ).inc()
        
        return wrapper
    return decorator


def track_custom_entity_operation(operation: str):
    """Decorator to track Custom Entity operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            status = 'success'
            
            try:
                result = await func(*args, **kwargs)
                
                # Track entity creation
                if operation == 'create' and hasattr(result, 'total_addresses'):
                    custom_entities_addresses.observe(result.total_addresses)
                
                return result
                
            except Exception as e:
                status = 'error'
                raise
            finally:
                custom_entities_operations.labels(
                    operation=operation,
                    status=status
                ).inc()
        
        return wrapper
    return decorator


def track_indirect_risk():
    """Decorator to track Indirect Risk metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            max_hops = kwargs.get('max_hops', 3)
            status = 'success'
            
            try:
                result = await func(*args, **kwargs)
                
                # Extract metrics
                if hasattr(result, 'total_paths_found'):
                    indirect_risk_paths_found.observe(result.total_paths_found)
                
                if hasattr(result, 'aggregate_risk_score'):
                    indirect_risk_score.observe(result.aggregate_risk_score)
                
                if hasattr(result, 'chains_analyzed'):
                    indirect_risk_chains_analyzed.observe(len(result.chains_analyzed))
                
                return result
                
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                indirect_risk_duration.labels(max_hops=str(max_hops)).observe(duration)
                indirect_risk_requests.labels(
                    status=status,
                    max_hops=str(max_hops)
                ).inc()
        
        return wrapper
    return decorator


def track_ledger_operation(operation: str):
    """Decorator to track Custom Ledger operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Track transfers per ledger
                if operation == 'upload_csv' and hasattr(result, 'total_transfers'):
                    custom_ledgers_transfers.observe(result.total_transfers)
                    custom_ledgers_csv_upload.labels(status='success').inc()
                
                return result
                
            except Exception as e:
                if operation == 'upload_csv':
                    custom_ledgers_csv_upload.labels(status='error').inc()
                raise
        
        return wrapper
    return decorator


def track_api_request(endpoint: str):
    """Decorator to track API requests"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 200
            method = 'GET'
            
            # Try to extract method from request
            request = kwargs.get('request')
            if request and hasattr(request, 'method'):
                method = request.method
            
            try:
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                api_request_duration.labels(
                    endpoint=endpoint,
                    method=method,
                    status=str(status)
                ).observe(duration)
                api_requests_total.labels(
                    endpoint=endpoint,
                    method=method,
                    status=str(status)
                ).inc()
        
        return wrapper
    return decorator


# ============================================================================
# Utility Functions
# ============================================================================

def update_entity_count(count: int):
    """Update total custom entities count"""
    custom_entities_total.set(count)


def update_ledger_count(count: int):
    """Update total custom ledgers count"""
    custom_ledgers_total.set(count)


def update_active_users(count: int):
    """Update active users count"""
    active_users.set(count)


def update_database_connections(count: int):
    """Update database connections count"""
    database_connections.set(count)


def update_redis_connections(count: int):
    """Update Redis connections count"""
    redis_connections.set(count)
