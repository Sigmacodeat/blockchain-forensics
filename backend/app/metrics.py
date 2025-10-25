"""
Prometheus metrics definitions
"""
from prometheus_client import Counter, Histogram, Gauge

# Ensure metrics are only registered once even if this module is imported multiple times
if not globals().get("_METRICS_INITIALIZED", False):
    _METRICS_INITIALIZED = True

    # Chain metrics
    CHAIN_REQUESTS = Counter(
        "chain_requests_total",
        "Total number of chain utility requests",
        labelnames=("chain", "op", "status"),
    )

    # Trace graph construction metrics
    TRACE_EDGES_CREATED = Counter(
        "trace_edges_created_total",
        "Number of edges created during tracing",
        labelnames=("event_type",),
    )

    CHAIN_LATENCY = Histogram(
        "chain_request_latency_seconds",
        "Latency of chain utility requests",
        labelnames=("chain", "op"),
        buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
    )

    LABEL_REQUESTS = Counter(
        "label_requests_total",
        "Total number of label API requests",
        labelnames=("op", "status"),
    )

    LABEL_LATENCY = Histogram(
        "label_request_latency_seconds",
        "Latency of label API requests",
        labelnames=("op",),
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2),
    )

    COMPLIANCE_REQUESTS = Counter(
        "compliance_requests_total",
        "Total number of compliance API requests",
        labelnames=("op", "status"),
    )

    COMPLIANCE_LATENCY = Histogram(
        "compliance_request_latency_seconds",
        "Latency of compliance API requests",
        labelnames=("op",),
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2),
    )

    # Sanctions indexing metrics (multi-source)
    SANCTIONS_ENTRIES_TOTAL = Counter(
        "sanctions_entries_total",
        "Total number of sanctions entries fetched per source",
        labelnames=("source",),
    )

    SANCTIONS_ADDRESSES_TOTAL = Counter(
        "sanctions_addresses_total",
        "Total number of unique crypto addresses found per source",
        labelnames=("source",),
    )

    SANCTIONS_UPDATE_TIMESTAMP = Gauge(
        "sanctions_update_timestamp",
        "Unix timestamp of the last sanctions update per source",
        labelnames=("source",),
    )

    SANCTIONS_ENTRIES_STORED = Counter(
        "sanctions_entries_stored_total",
        "Total number of sanctions entries successfully stored",
    )

    SANCTIONS_FETCH_TOTAL = Counter(
        "sanctions_fetch_total",
        "Total number of sanctions fetches per source",
        labelnames=("source",),
    )

    SANCTIONS_FETCH_DURATION = Histogram(
        "sanctions_fetch_duration_seconds",
        "Time taken to fetch sanctions data per source",
        labelnames=("source",),
        buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60),
    )

    SANCTIONS_ENTRIES_PARSED = Counter(
        "sanctions_entries_parsed_total",
        "Total number of sanctions entries parsed per source",
        labelnames=("source",),
    )

    SANCTIONS_UPDATE_ERRORS = Counter(
        "sanctions_update_errors_total",
        "Total number of sanctions update errors per source and type",
        labelnames=("source", "error_type"),
    )
    POSTGRES_UP = Gauge(
        "postgres_up",
        "Postgres connectivity gauge (1 up, 0 down)",
    )

    REDIS_UP = Gauge(
        "redis_up",
        "Redis connectivity gauge (1 up, 0 down)",
    )

    EVIDENCE_VAULT_UP = Gauge(
        "evidence_vault_up",
        "Evidence Vault health (1 ok, 0 error)",
    )

    # Worker metrics (generic across all workers)
    WORKER_STATUS = Gauge(
        "worker_status",
        "Worker status gauge (1 running/ok, 0 degraded/stopped)",
        labelnames=("worker_name",),
    )

    WORKER_PROCESSED_TOTAL = Counter(
        "worker_processed_total",
        "Total number of items processed by a worker",
        labelnames=("worker_name",),
    )

    WORKER_ERRORS_TOTAL = Counter(
        "worker_errors_total",
        "Total number of errors encountered by a worker",
        labelnames=("worker_name",),
    )

    WORKER_LAST_HEARTBEAT = Gauge(
        "worker_last_heartbeat_timestamp",
        "Unix timestamp of the last observed worker heartbeat",
        labelnames=("worker_name",),
    )

    # JSON-RPC Cache metrics
    JSONRPC_CACHE_HITS = Counter(
        "jsonrpc_cache_hits_total",
        "Total JSON-RPC cache hits",
        labelnames=("layer",),  # layer: redis|memory
    )

    JSONRPC_CACHE_MISSES = Counter(
        "jsonrpc_cache_misses_total",
        "Total JSON-RPC cache misses",
        labelnames=("layer",),
    )

    # Forensics / Trace metrics
    TRACE_REQUESTS = Counter(
        "trace_requests_total",
        "Total number of forensics trace requests",
        labelnames=("op", "status"),
    )

    TRACE_LATENCY = Histogram(
        "trace_request_latency_seconds",
        "Latency of forensics trace requests",
        labelnames=("op",),
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
    )

    # Bridge & Risk metrics
    BRIDGE_EVENTS = Counter(
        "bridge_events_total",
        "Number of detected/persisted bridge events",
        labelnames=("stage",),  # stage: detected|persisted|error
    )

    RISK_SCORE = Histogram(
        "risk_score_value",
        "Distribution of risk scores (0-100)",
        buckets=(0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100),
    )

    # DEX swaps detected
    DEX_SWAPS_TOTAL = Counter(
        "dex_swaps_total",
        "Total number of detected DEX swap events",
    )

    # Solana JSON-RPC reliability metrics
    SOLANA_RPC_RETRIES = Counter(
        "solana_rpc_retries_total",
        "Number of retry attempts for Solana JSON-RPC",
        labelnames=("method",),
    )

    SOLANA_RPC_ERRORS = Counter(
        "solana_rpc_errors_total",
        "Number of Solana JSON-RPC errors after retries",
        labelnames=("method",),
    )

    # Kafka metrics
    KAFKA_PRODUCER_ERRORS = Counter(
        "kafka_producer_errors_total",
        "Number of errors encountered by Kafka producer",
    )

    KAFKA_CONSUMER_ERRORS = Counter(
        "kafka_consumer_errors_total",
        "Number of errors encountered by Kafka consumer",
    )

    KAFKA_COMMITS_TOTAL = Counter(
        "kafka_commits_total",
        "Total number of Kafka message commits",
        labelnames=("topic",),
    )

    KAFKA_DLQ_MESSAGES = Counter(
        "kafka_dlq_messages_total",
        "Number of messages redirected to DLQ",
    )

    # DLQ Replayer metrics
    DLQ_REPLAY_TOTAL = Counter(
        "dlq_replay_total",
        "Total DLQ messages replayed",
        labelnames=("worker",),
    )

    DLQ_REPLAY_ERRORS = Counter(
        "dlq_replay_errors_total",
        "DLQ replay errors",
        labelnames=("worker",),
    )

    KAFKA_EVENTS_FAILED = Counter(
        "kafka_events_failed_total",
        "Number of failed event publications",
        labelnames=("topic",),
    )

    KAFKA_PUBLISH_DURATION = Histogram(
        "kafka_publish_duration_seconds",
        "Time taken to publish events to Kafka",
        labelnames=("topic",),
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1),
    )

    KAFKA_EVENTS_CONSUMED = Counter(
        "kafka_events_consumed_total",
        "Number of events consumed from Kafka",
        labelnames=("topic",),
    )

    KAFKA_EVENTS_PUBLISHED = Counter(
        "kafka_events_published_total",
        "Number of events published to Kafka",
        labelnames=("topic",),
    )

    KAFKA_PROCESSING_DURATION = Histogram(
        "kafka_processing_duration_seconds",
        "Time taken to process consumed events",
        labelnames=("topic",),
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
    )

    KAFKA_CONSUMER_LAG = Gauge(
        "kafka_consumer_lag",
        "Current consumer lag (high watermark - current offset)",
        labelnames=("topic", "partition"),
    )

    # Consumer status per group
    KAFKA_CONSUMER_STATUS = Gauge(
        "kafka_consumer_status",
        "Kafka consumer status (1 running/ok, 0 degraded/stopped)",
        labelnames=("group_id",),
    )

    # ==========================
    # KYT / Monitoring metrics
    # ==========================

    RULE_EVAL_TOTAL = Counter(
        "rule_eval_total",
        "Total number of rule evaluations",
        labelnames=("rule", "outcome"),  # outcome: hit|miss|error
    )

    # ==========================
    # NewsCase (Public Watcher) metrics
    # ==========================
    NEWSCASE_EVENTS_TOTAL = Counter(
        "newscase_events_total",
        "Number of NewsCase events broadcast",
        labelnames=("type",),  # type: snapshot|status|tx|kyt|error
    )

    NEWSCASE_SUBSCRIPTIONS = Gauge(
        "newscase_subscriptions_total",
        "Current number of active NewsCase WS subscriptions",
    )

    NEWSCASE_WATCHERS = Gauge(
        "newscase_watchers_total",
        "Current number of active NewsCase watchers",
    )

    # ==========================
    # Intel / Webhook metrics
    # ==========================
    INTEL_WEBHOOK_INGEST_TOTAL = Counter(
        "intel_webhook_ingest_total",
        "Inbound threat intel webhook ingests",
        labelnames=("source", "status"),
    )

    RULE_EVAL_LATENCY = Histogram(
        "rule_eval_latency_seconds",
        "Latency of single rule evaluation",
        labelnames=("rule",),
        buckets=(0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25),
    )

    E2E_EVENT_ALERT_LATENCY = Histogram(
        "e2e_event_alert_latency_seconds",
        "End-to-end latency from event receipt to alert persist",
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2),
    )

    ALERTS_CREATED_TOTAL = Counter(
        "alerts_created_total",
        "Number of created alerts by severity",
        labelnames=("severity",),
    )

    ALERTS_SUPPRESSED_TOTAL = Counter(
        "alerts_suppressed_total",
        "Number of alerts suppressed due to deduplication",
        labelnames=("alert_type", "reason"),
    )

    # Audit metrics
    AUDIT_EVENTS_TOTAL = Counter(
        "audit_events_total",
        "Total number of audit events",
        labelnames=("event_type", "severity"),
    )

    # Neue Alert Engine Metrics für Batch-Verarbeitung
    EVENTS_BUFFERED = Gauge(
        "events_buffered",
        "Number of events currently in the buffer",
    )

    EVENTS_PROCESSED_BATCH = Counter(
        "events_processed_batch_total",
        "Number of events processed in batches",
        labelnames=("batch_size",),
    )

    BATCH_PROCESSING_LATENCY = Histogram(
        "batch_processing_latency_seconds",
        "Latency of batch processing operations",
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
    )

    ALERT_ENGINE_QUEUE_SIZE = Gauge(
        "alert_engine_queue_size",
        "Current size of the alert engine processing queue",
    )

    WEBHOOK_NOTIFICATIONS_SENT = Counter(
        "webhook_notifications_sent_total",
        "Number of webhook notifications sent",
        labelnames=("status",),
    )

    WEBHOOK_NOTIFICATION_LATENCY = Histogram(
        "webhook_notification_latency_seconds",
        "Latency of webhook notification delivery",
        buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10),
    )

    ENTITY_EVENT_LIMITS_HIT = Counter(
        "entity_event_limits_hit_total",
        "Number of times entity event limits were hit",
        labelnames=("entity_id",),
    )

    # Erweiterte Alert-Regeln Metriken
    ADVANCED_ALERTS_CREATED_TOTAL = Counter(
        'advanced_alerts_created_total',
        'Total number of advanced alerts created',
        ['alert_type', 'severity', 'correlation']
    )

    ADVANCED_ALERTS_SUPPRESSED_TOTAL = Counter(
        'advanced_alerts_suppressed_total',
        'Total number of advanced alerts suppressed',
        ['alert_type', 'suppression_reason']
    )

    CORRELATION_ALERTS_CREATED_TOTAL = Counter(
        'correlation_alerts_created_total',
        'Total number of correlation alerts created',
        ['correlation_rule', 'severity']
    )

    MONEY_LAUNDERING_PATTERNS_DETECTED = Counter(
        'money_laundering_patterns_detected',
        'Total number of money laundering patterns detected',
        ['pattern_type', 'severity']
    )

    # VASP Risk Scoring metrics
    VASP_RISK_SCORED_TOTAL = Counter(
        'vasp_risk_scored_total',
        'Total number of VASP risk scorings performed',
        ['vasp_id', 'risk_level', 'compliance_status']
    )

    VASP_RISK_SCORE_DISTRIBUTION = Histogram(
        'vasp_risk_score_distribution',
        'Distribution of VASP risk scores (0-1 range)',
        buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
    )

    VASP_RISK_LAST_SCORE = Gauge(
        'vasp_risk_last_score',
        'Last recorded VASP risk score',
        ['vasp_id']
    )

    SMART_CONTRACT_EXPLOITS_DETECTED = Counter(
        'smart_contract_exploits_detected',
        'Total number of smart contract exploits detected',
        ['exploit_type', 'severity']
    )

    FLASH_LOAN_ATTACKS_DETECTED = Counter(
        'flash_loan_attacks_detected',
        'Total number of flash loan attacks detected',
        ['attack_type', 'severity']
    )

    WHALE_MOVEMENTS_DETECTED = Counter(
        'whale_movements_detected',
        'Total number of whale movements detected',
        ['whale_type', 'severity']
    )

    RUG_PULLS_DETECTED = Counter(
        'rug_pulls_detected',
        'Total number of rug pulls detected',
        ['token_type', 'severity']
    )

    PONZI_SCHEMES_DETECTED = Counter(
        'ponzi_schemes_detected',
        'Total number of ponzi schemes detected',
        ['scheme_type', 'severity']
    )

    ANOMALY_DETECTIONS_TOTAL = Counter(
        'anomaly_detections_total',
        'Total number of anomalies detected',
        ['model_type', 'severity']
    )

    INSIDER_TRADING_DETECTIONS_TOTAL = Counter(
        'insider_trading_detections_total',
        'Total number of insider trading detections',
        ['trading_type', 'severity']
    )

    DARK_WEB_CONNECTIONS_DETECTED = Counter(
        'dark_web_connections_detected',
        'Total number of dark web connections detected',
        ['connection_type', 'severity']
    )

    CROSS_CHAIN_ARBITRAGE_DETECTED = Counter(
        'cross_chain_arbitrage_detected',
        'Total number of cross-chain arbitrage detected',
        ['arbitrage_type', 'severity']
    )

    # Suppression Metriken für erweiterte Regeln
    SUPPRESSION_EFFECTIVENESS = Gauge(
        'suppression_effectiveness',
        'Effectiveness of suppression rules',
        ['suppression_type']
    )

    ENTITY_SUPPRESSION_HITS = Counter(
        'entity_suppression_hits',
        'Number of times entity suppression was triggered',
        ['entity_type', 'suppression_rule']
    )

    GLOBAL_RATE_LIMIT_HITS = Counter(
        'global_rate_limit_hits',
        'Number of times global rate limiting was triggered',
        ['rate_limit_type']
    )

    CORRELATION_SUCCESS_RATE = Gauge(
        'correlation_success_rate',
        'Success rate of correlation rules'
    )

    # ==========================
    # Connection Pool Metrics
    # ==========================

    DB_CONNECTION_POOL_SIZE = Gauge(
        "db_connection_pool_size",
        "Current size of the database connection pool",
    )

    DB_CONNECTION_POOL_ACTIVE = Gauge(
        "db_connection_pool_active",
        "Number of active connections in the pool",
    )

    DB_CONNECTION_POOL_IDLE = Gauge(
        "db_connection_pool_idle",
        "Number of idle connections in the pool",
    )

    DB_CONNECTION_POOL_WAITING = Gauge(
        "db_connection_pool_waiting",
        "Number of requests waiting for a connection",
    )

    DB_CONNECTION_CREATE_TIME = Histogram(
        "db_connection_create_time_seconds",
        "Time taken to create a new database connection",
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1),
    )

    DB_CONNECTION_REUSE_TIME = Histogram(
        "db_connection_reuse_time_seconds",
        "Time taken to reuse an existing connection from the pool",
        buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05),
    )

    # Note: sanctions metrics already defined above

    # ==========================
    # Alert Batching Metrics
    # ==========================

    ALERT_BATCH_SIZE = Histogram(
        "alert_batch_size",
        "Size of alert batches processed",
        buckets=(1, 5, 10, 25, 50, 100, 250, 500),
    )

    ALERT_BATCH_PROCESSING_TIME = Histogram(
        "alert_batch_processing_time_seconds",
        "Time taken to process an alert batch",
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
    )

    ALERT_BATCHES_CREATED = Counter(
        "alert_batches_created_total",
        "Total number of alert batches created",
    )

    ALERT_BATCHES_PROCESSED = Counter(
        "alert_batches_processed_total",
        "Total number of alert batches processed",
    )

    # ==========================
    # WebSocket Connection Metrics
    # ==========================

    WEBSOCKET_CONNECTIONS_TOTAL = Counter(
        "websocket_connections_total",
        "Total number of WebSocket connections established",
        labelnames=("endpoint", "auth_method"),  # endpoint: alerts|room|trace|general|collab, auth_method: jwt|api_key|none
    )

    WEBSOCKET_CONNECTIONS_ACTIVE = Gauge(
        "websocket_connections_active",
        "Current number of active WebSocket connections",
        labelnames=("endpoint",),
    )

    WEBSOCKET_CONNECTION_DURATION = Histogram(
        "websocket_connection_duration_seconds",
        "Duration of WebSocket connections",
        labelnames=("endpoint", "auth_method"),
        buckets=(1, 5, 10, 30, 60, 300, 600, 1800, 3600),  # 1s to 1h
    )

    WEBSOCKET_AUTH_FAILURES = Counter(
        "websocket_auth_failures_total",
        "Total number of WebSocket authentication failures",
        labelnames=("endpoint", "reason"),  # reason: invalid_token|plan_insufficient|missing_auth|api_key_invalid
    )

    WEBSOCKET_MESSAGES_RECEIVED = Counter(
        "websocket_messages_received_total",
        "Total number of WebSocket messages received",
        labelnames=("endpoint", "message_type"),
    )

    WEBSOCKET_MESSAGES_SENT = Counter(
        "websocket_messages_sent_total",
        "Total number of WebSocket messages sent",
        labelnames=("endpoint", "message_type"),
    )

    WEBSOCKET_CONNECTION_ERRORS = Counter(
        "websocket_connection_errors_total",
        "Total number of WebSocket connection errors",
        labelnames=("endpoint", "error_type"),  # error_type: timeout|disconnect|protocol_error
    )
