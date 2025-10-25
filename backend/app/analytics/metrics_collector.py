"""
Metrics Collector
Prometheus-compatible metrics
"""

import logging
from prometheus_client import Counter, Histogram, Gauge, Summary

logger = logging.getLogger(__name__)

# Request Metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Trace Metrics
traces_total = Counter(
    'traces_total',
    'Total traces executed',
    ['taint_model', 'direction']
)

trace_duration = Histogram(
    'trace_duration_seconds',
    'Trace execution duration in seconds',
    ['taint_model']
)

trace_nodes = Histogram(
    'trace_nodes_total',
    'Number of nodes per trace',
    buckets=[10, 50, 100, 500, 1000, 5000, 10000]
)

# Risk Metrics
high_risk_addresses = Counter(
    'high_risk_addresses_total',
    'Total high-risk addresses detected',
    ['risk_level']
)

sanctioned_entities = Counter(
    'sanctioned_entities_total',
    'Total sanctioned entities detected',
    ['sanction_list']
)

# Database Metrics
db_connections = Gauge(
    'db_connections_active',
    'Active database connections',
    ['database']
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['database', 'operation']
)

# AI Metrics
ai_requests = Counter(
    'ai_requests_total',
    'Total AI agent requests',
    ['model']
)

ai_tokens_used = Counter(
    'ai_tokens_used_total',
    'Total AI tokens consumed',
    ['model', 'type']
)

# ML Metrics
ml_predictions = Counter(
    'ml_predictions_total',
    'Total ML model predictions',
    ['model', 'outcome']
)

ml_inference_duration = Summary(
    'ml_inference_duration_seconds',
    'ML model inference duration'
)


class MetricsCollector:
    """Centralized metrics collection"""
    
    @staticmethod
    def record_trace(taint_model: str, direction: str, duration: float, nodes: int):
        """Record trace metrics"""
        traces_total.labels(taint_model=taint_model, direction=direction).inc()
        trace_duration.labels(taint_model=taint_model).observe(duration)
        trace_nodes.observe(nodes)
    
    @staticmethod
    def record_high_risk(risk_level: str):
        """Record high-risk detection"""
        high_risk_addresses.labels(risk_level=risk_level).inc()
    
    @staticmethod
    def record_sanctioned(sanction_list: str):
        """Record sanctioned entity detection"""
        sanctioned_entities.labels(sanction_list=sanction_list).inc()
    
    @staticmethod
    def record_ai_request(model: str, tokens: int):
        """Record AI usage"""
        ai_requests.labels(model=model).inc()
        ai_tokens_used.labels(model=model, type='total').inc(tokens)


metrics_collector = MetricsCollector()
