"""
Prometheus Metrics for Forensics Modules
==========================================

Comprehensive metrics for KYT, SAR, NFT, Chain Coverage, and Advanced Features.
"""

from prometheus_client import Counter, Histogram, Gauge, Summary, Info
import time
from functools import wraps
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# KYT (Know Your Transaction) Metrics
# ============================================================================

KYT_SCREENING_TOTAL = Counter(
    'kyt_screening_total',
    'Total KYT screenings performed',
    ['chain', 'decision', 'risk_level']
)

KYT_SCREENING_DURATION = Histogram(
    'kyt_screening_duration_seconds',
    'KYT screening duration',
    ['chain', 'screening_type'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

KYT_ALERTS_TRIGGERED = Counter(
    'kyt_alerts_triggered_total',
    'Total KYT alerts triggered',
    ['alert_type', 'severity', 'chain']
)

KYT_FALSE_POSITIVES = Counter(
    'kyt_false_positives_total',
    'KYT false positives reported',
    ['alert_type', 'chain']
)

KYT_BATCH_SIZE = Histogram(
    'kyt_batch_size',
    'Size of KYT batch screenings',
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000]
)

# ============================================================================
# SAR/STR (Suspicious Activity Reporting) Metrics
# ============================================================================

SAR_REPORTS_GENERATED = Counter(
    'sar_reports_generated_total',
    'Total SAR reports generated',
    ['jurisdiction', 'report_type', 'format']
)

SAR_GENERATION_DURATION = Histogram(
    'sar_generation_duration_seconds',
    'SAR report generation duration',
    ['format'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

SAR_SUBMISSIONS = Counter(
    'sar_submissions_total',
    'Total SAR submissions to regulators',
    ['destination', 'status', 'jurisdiction']
)

SAR_VALIDATION_ERRORS = Counter(
    'sar_validation_errors_total',
    'SAR validation errors',
    ['error_type', 'field']
)

SAR_CASE_CONVERSION_TIME = Histogram(
    'sar_case_conversion_seconds',
    'Time to convert case to SAR',
    buckets=[5, 10, 30, 60, 120, 300, 600, 1800]
)

# ============================================================================
# NFT Wash-Trading Detection Metrics
# ============================================================================

NFT_WASH_DETECTIONS = Counter(
    'nft_wash_detections_total',
    'Total NFT wash-trading patterns detected',
    ['pattern_type', 'confidence_level']
)

NFT_TRADES_ANALYZED = Counter(
    'nft_trades_analyzed_total',
    'Total NFT trades analyzed',
    ['marketplace', 'chain']
)

NFT_DETECTION_DURATION = Histogram(
    'nft_detection_duration_seconds',
    'NFT wash-trading detection duration',
    ['trade_count_bucket'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

NFT_SUSPICIOUS_PATTERNS = Gauge(
    'nft_suspicious_patterns_active',
    'Currently active suspicious NFT patterns',
    ['pattern_type']
)

NFT_CONFIDENCE_DISTRIBUTION = Histogram(
    'nft_confidence_score',
    'NFT wash-trading confidence scores',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0]
)

# ============================================================================
# Chain Coverage Metrics
# ============================================================================

CHAIN_ADAPTER_STATUS = Gauge(
    'chain_adapter_status',
    'Chain adapter availability (1=up, 0=down)',
    ['chain_id', 'chain_type']
)

CHAIN_RPC_LATENCY = Histogram(
    'chain_rpc_latency_seconds',
    'RPC call latency per chain',
    ['chain_id', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

CHAIN_BLOCKS_PROCESSED = Counter(
    'chain_blocks_processed_total',
    'Total blocks processed per chain',
    ['chain_id', 'chain_type']
)

CHAIN_TX_PROCESSED = Counter(
    'chain_transactions_processed_total',
    'Total transactions processed',
    ['chain_id', 'tx_type']
)

CHAIN_ERRORS = Counter(
    'chain_adapter_errors_total',
    'Chain adapter errors',
    ['chain_id', 'error_type']
)

# ============================================================================
# Tornado Cash Demixing Metrics
# ============================================================================

TORNADO_DEMIX_ATTEMPTS = Counter(
    'tornado_demix_attempts_total',
    'Total Tornado Cash demixing attempts',
    ['pool_size', 'chain']
)

TORNADO_DEMIX_SUCCESS = Counter(
    'tornado_demix_success_total',
    'Successful Tornado Cash demixings',
    ['confidence_level', 'technique']
)

TORNADO_DEMIX_DURATION = Histogram(
    'tornado_demix_duration_seconds',
    'Tornado Cash demixing duration',
    ['pool_size'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800]
)

TORNADO_ANONYMITY_SET_SIZE = Gauge(
    'tornado_anonymity_set_size',
    'Current anonymity set size for analysis',
    ['pool']
)

# ============================================================================
# Entity Labels & Intelligence Metrics
# ============================================================================

ENTITY_LABELS_TOTAL = Gauge(
    'entity_labels_total',
    'Total entity labels in database',
    ['source', 'category']
)

ENTITY_ENRICHMENT_HITS = Counter(
    'entity_enrichment_hits_total',
    'Entity enrichment cache hits',
    ['source']
)

ENTITY_ENRICHMENT_MISSES = Counter(
    'entity_enrichment_misses_total',
    'Entity enrichment cache misses',
    ['source']
)

ENTITY_THREAT_INTEL_UPDATES = Counter(
    'entity_threat_intel_updates_total',
    'Threat intelligence updates applied',
    ['source', 'severity']
)

ENTITY_LABEL_CONFLICTS = Counter(
    'entity_label_conflicts_total',
    'Label conflicts detected',
    ['conflict_type']
)

# ============================================================================
# Performance & System Metrics
# ============================================================================

FORENSICS_MEMORY_USAGE = Gauge(
    'forensics_memory_usage_bytes',
    'Memory usage by forensics module',
    ['module']
)

FORENSICS_ACTIVE_INVESTIGATIONS = Gauge(
    'forensics_active_investigations',
    'Currently active investigations',
    ['type']
)

FORENSICS_API_LATENCY = Summary(
    'forensics_api_latency_seconds',
    'API endpoint latency',
    ['endpoint', 'method']
)

FORENSICS_CACHE_SIZE = Gauge(
    'forensics_cache_size_bytes',
    'Cache size in bytes',
    ['cache_type']
)

# ============================================================================
# ML Model Metrics
# ============================================================================

ML_MODEL_PREDICTIONS = Counter(
    'ml_model_predictions_total',
    'Total ML model predictions',
    ['model_name', 'model_version']
)

ML_MODEL_INFERENCE_TIME = Histogram(
    'ml_model_inference_seconds',
    'ML model inference time',
    ['model_name'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

ML_MODEL_ACCURACY = Gauge(
    'ml_model_accuracy',
    'ML model accuracy score',
    ['model_name', 'dataset']
)

ML_FEATURE_EXTRACTION_TIME = Histogram(
    'ml_feature_extraction_seconds',
    'Feature extraction time',
    ['feature_set'],
    buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0]
)

# ============================================================================
# Business & Compliance Metrics
# ============================================================================

COMPLIANCE_CHECKS_TOTAL = Counter(
    'compliance_checks_total',
    'Total compliance checks performed',
    ['check_type', 'result']
)

REGULATOR_REPORTS_SENT = Counter(
    'regulator_reports_sent_total',
    'Reports sent to regulators',
    ['regulator', 'report_type', 'status']
)

INVESTIGATION_DURATION = Histogram(
    'investigation_duration_hours',
    'Investigation duration in hours',
    buckets=[1, 4, 8, 24, 48, 72, 168, 336, 720]
)

EVIDENCE_ITEMS_COLLECTED = Counter(
    'evidence_items_collected_total',
    'Evidence items collected',
    ['evidence_type', 'chain']
)

# ============================================================================
# Decorator Functions for Easy Instrumentation
# ============================================================================

def track_kyt_screening(chain: str, screening_type: str = "pre"):
    """Decorator to track KYT screening metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                
                KYT_SCREENING_DURATION.labels(
                    chain=chain,
                    screening_type=screening_type
                ).observe(duration)
                
                # Track decision if in result
                if hasattr(result, 'decision'):
                    KYT_SCREENING_TOTAL.labels(
                        chain=chain,
                        decision=result.decision,
                        risk_level=getattr(result, 'risk_level', 'unknown')
                    ).inc()
                
                return result
            except Exception as e:
                logger.error(f"KYT screening error: {e}")
                raise
        return wrapper
    return decorator


def track_nft_detection(func: Callable) -> Callable:
    """Decorator to track NFT wash-trading detection"""
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        trades_count = len(args[0]) if args else 0
        
        bucket = "small" if trades_count < 10 else "medium" if trades_count < 100 else "large"
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            
            NFT_DETECTION_DURATION.labels(
                trade_count_bucket=bucket
            ).observe(duration)
            
            NFT_TRADES_ANALYZED.labels(
                marketplace="unknown",
                chain="unknown"
            ).inc(trades_count)
            
            # Track detected patterns
            if hasattr(result, '__iter__'):
                for finding in result:
                    if hasattr(finding, 'pattern_type'):
                        NFT_WASH_DETECTIONS.labels(
                            pattern_type=finding.pattern_type,
                            confidence_level="high" if finding.confidence > 0.8 else "medium"
                        ).inc()
            
            return result
        except Exception as e:
            logger.error(f"NFT detection error: {e}")
            raise
    return wrapper


def track_chain_operation(chain_id: str, operation: str):
    """Decorator to track chain adapter operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                
                CHAIN_RPC_LATENCY.labels(
                    chain_id=chain_id,
                    method=operation
                ).observe(duration)
                
                return result
            except Exception as e:
                CHAIN_ERRORS.labels(
                    chain_id=chain_id,
                    error_type=type(e).__name__
                ).inc()
                raise
        return wrapper
    return decorator


# ============================================================================
# System Info Metrics
# ============================================================================

FORENSICS_INFO = Info(
    'forensics_system',
    'Forensics system information'
)

# Set initial system info
FORENSICS_INFO.info({
    'version': '2.0.0',
    'chain_coverage': '35+',
    'features': 'kyt,sar,nft,demixing,ml',
    'deployment': 'production'
})
