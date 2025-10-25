# 📊 Monitoring & Observability Guide

**Blockchain Forensics Platform** - Umfassende Monitoring-Dokumentation

---

## 📋 Übersicht

Die Plattform bietet vollständiges Monitoring für alle kritischen Services und Komponenten. Dieses Dokument beschreibt alle verfügbaren Metriken, Alerts, Dashboards und Health Checks.

### Monitoring-Stack

- **Prometheus**: Metrics Collection & Alerting
- **Grafana**: Visualization & Dashboards
- **FastAPI /metrics**: Prometheus-kompatible Metriken
- **Health Checks**: Kubernetes-ready Probes

---

## 🔍 Health Check Endpoints

### 1. **Basic Health Check** (`/health`)

**Endpoint**: `GET /health`  
**Zweck**: Schneller Liveness-Check

```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "Blockchain Forensics Platform"
}
```

---

### 2. **Legacy Probe** (`/api/healthz`)

**Endpoint**: `GET /api/healthz`  
**Zweck**: Liveness/Readiness mit Service-Status

**Response**:
```json
{
  "ok": true,
  "services": {
    "postgres": {"up": true},
    "neo4j": {"up": true},
    "redis": {"up": true}
  }
}
```

---

### 3. **Detailed Health Check** (`/api/health/detailed`) ⭐

**Endpoint**: `GET /api/health/detailed`  
**Zweck**: Umfassender Check mit Latenz-Messungen

**Features**:
- Latenz-Messung für jeden Service
- Degradation Detection (langsame Services)
- Zusätzliche Metriken (Node Counts, User Counts, etc.)
- Overall Status: `healthy` | `degraded` | `unhealthy`

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-10T20:00:00Z",
  "environment": "production",
  "checks_duration_ms": 45.23,
  "services": {
    "postgres": {
      "healthy": true,
      "latency_ms": 12.5,
      "users_count": 150,
      "error": null
    },
    "neo4j": {
      "healthy": true,
      "latency_ms": 23.1,
      "node_count": 50000,
      "error": null
    },
    "redis": {
      "healthy": true,
      "latency_ms": 5.2,
      "configured": true,
      "error": null
    },
    "qdrant": {
      "healthy": true,
      "latency_ms": 15.8,
      "collections_count": 3,
      "error": null
    },
    "blockchain_rpc": {
      "healthy": true,
      "latency_ms": 250.3,
      "chain": "ethereum",
      "latest_block": 18500000,
      "error": null
    }
  },
  "degraded_services": [],
  "failed_services": []
}
```

**Degradation Thresholds**:
- Postgres: > 100ms
- Neo4j: > 200ms

---

### 4. **Kubernetes Readiness Probe** (`/api/health/ready`)

**Endpoint**: `GET /api/health/ready`  
**Zweck**: K8s Readiness Probe (kritische Services müssen verfügbar sein)

**Kritische Services**: Postgres, Neo4j

**Success (200)**:
```json
{
  "ready": true,
  "checks": [
    {"postgres": true},
    {"neo4j": true}
  ]
}
```

**Failure (503)**:
```json
{
  "detail": "Neo4j not ready"
}
```

**Kubernetes Config**:
```yaml
readinessProbe:
  httpGet:
    path: /api/health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 3
```

---

### 5. **Kubernetes Liveness Probe** (`/api/health/live`)

**Endpoint**: `GET /api/health/live`  
**Zweck**: K8s Liveness Probe (erkennt Deadlocks)

**Response**:
```json
{
  "alive": true,
  "timestamp": 1704910800.123
}
```

**Kubernetes Config**:
```yaml
livenessProbe:
  httpGet:
    path: /api/health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 1
  failureThreshold: 3
```

---

## 📈 Prometheus Metriken

### Metrics Endpoint

**URL**: `GET /metrics`

Alle Metriken im Prometheus-Format.

### Kategorien

#### **1. API Request Metrics**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `chain_requests_total` | Counter | `op`, `status` | Chain-API Requests |
| `label_requests_total` | Counter | `op`, `status` | Label-API Requests |
| `compliance_requests_total` | Counter | `op`, `status` | Compliance Requests |
| `trace_requests_total` | Counter | `op`, `status` | Trace Requests |
| `chain_request_latency_seconds` | Histogram | `op` | Chain Latenz |
| `label_request_latency_seconds` | Histogram | - | Label Latenz |
| `trace_request_latency_seconds` | Histogram | `op` | Trace Latenz |

**Example**:
```
chain_requests_total{op="get_transaction",status="ok"} 15234
chain_request_latency_seconds_bucket{op="get_transaction",le="0.5"} 12000
```

---

#### **2. Database Metrics**

| Metric | Type | Description |
|--------|------|-------------|
| `postgres_up` | Gauge | Postgres Health (0/1) |
| `redis_up` | Gauge | Redis Health (0/1) |
| `neo4j_up` | Gauge | Neo4j Health (0/1) |
| `neo4j_graph_nodes_total` | Gauge | Total Graph Nodes |
| `neo4j_graph_relationships_total` | Gauge | Total Relationships |
| `neo4j_active_queries` | Gauge | Active Queries |
| `neo4j_query_latency_seconds` | Histogram | Query Latenz |
| `neo4j_transactions_total` | Counter | Neo4j Transactions |
| `qdrant_up` | Gauge | Qdrant Health (0/1) |
| `qdrant_collections_total` | Gauge | Vector Collections |
| `qdrant_collection_vectors_count` | Gauge | Total Vectors |
| `qdrant_search_requests_total` | Counter | Search Requests |
| `qdrant_search_latency_seconds` | Histogram | Search Latenz |

---

#### **3. AI & ML Metrics**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `ai_agent_requests_total` | Counter | `operation` | AI Agent Calls |
| `openai_api_calls_total` | Counter | `model`, `status` | OpenAI API Calls |
| `openai_tokens_used_total` | Counter | `model` | Token Usage |
| `ml_risk_score_requests_total` | Counter | `status` | Risk Scoring |
| `ml_clustering_operations_total` | Counter | - | Clustering Ops |

**Token Usage Tracking**:
```
openai_tokens_used_total{model="gpt-4"} 1250000
```

---

#### **4. WebSocket Metrics**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `websocket_connections_active` | Gauge | - | Active Connections |
| `websocket_connections_total` | Counter | - | Total Connections |
| `websocket_disconnections_total` | Counter | - | Disconnections |
| `websocket_messages_sent_total` | Counter | `type` | Sent Messages |
| `websocket_messages_received_total` | Counter | `type` | Received Messages |

---

#### **5. Authentication Metrics**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `auth_events_total` | Counter | `event` | Auth Events (login, logout, etc.) |
| `auth_active_sessions` | Gauge | - | Active Sessions |
| `auth_token_refreshes_total` | Counter | - | Token Refreshes |
| `rate_limit_exceeded_total` | Counter | `endpoint` | Rate Limit Violations |

**Events**: `login_success`, `login_failed`, `logout`, `register`, `password_reset`

---

#### **6. Export & Reports**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `export_requests_total` | Counter | `format` | Export Requests (csv, json, pdf) |
| `report_generation_latency_seconds` | Histogram | `type` | Report Gen Time |
| `export_size_bytes` | Histogram | - | Export File Sizes |
| `email_sent_total` | Counter | `status` | Email Delivery |

---

#### **7. Kafka Metrics**

| Metric | Type | Description |
|--------|------|-------------|
| `kafka_producer_errors_total` | Counter | Producer Errors |
| `kafka_consumer_errors_total` | Counter | Consumer Errors |
| `kafka_dlq_messages_total` | Counter | Dead Letter Queue |
| `kafka_consumer_commits_total` | Counter | Consumer Commits |

---

#### **8. Infrastructure**

| Metric | Type | Description |
|--------|------|-------------|
| `jsonrpc_cache_hits_total` | Counter | RPC Cache Hits |
| `jsonrpc_cache_misses_total` | Counter | RPC Cache Misses |

**Cache Hit Ratio**:
```promql
sum(rate(jsonrpc_cache_hits_total[5m])) / 
(sum(rate(jsonrpc_cache_hits_total[5m])) + sum(rate(jsonrpc_cache_misses_total[5m])))
```

---

## 🚨 Prometheus Alerts

### Alert Groups

Die Alerts sind in **8 Gruppen** organisiert:

1. **Error Rates** (6 Alerts)
2. **Latency** (2 Alerts)
3. **Databases** (6 Alerts)
4. **AI/ML** (3 Alerts)
5. **WebSocket** (2 Alerts)
6. **Auth** (3 Alerts)
7. **Exports** (2 Alerts)

### Kritische Alerts

#### **PostgresDown**
```yaml
expr: postgres_up == 0
for: 2m
severity: critical
```
**Action**: Datenbank sofort prüfen, Verbindung wiederherstellen

#### **Neo4jDown**
```yaml
expr: neo4j_up == 0
for: 2m
severity: critical
```
**Action**: Neo4j Container/Service prüfen

#### **HighFailedLoginRate**
```yaml
expr: rate(auth_events_total{event="login_failed"}[5m]) > 1
for: 5m
severity: warning
```
**Action**: Möglicher Brute-Force-Angriff, IP-Adressen prüfen

---

## 📊 Grafana Dashboards

### Dashboard: "Complete System Metrics"

**Zugriff**: http://localhost:3000 (Grafana)  
**Import**: `/monitoring/grafana-dashboard.json`

### Panels (9 Rows)

1. **Requests Counters**: Total Requests (Chain, Label, Compliance)
2. **Latency Histograms**: p50/p90/p99 für alle APIs
3. **Request Rates & Status**: Breakdown nach Operation
4. **Error Rates**: Fehlerraten mit Thresholds
5. **Infra**: Postgres, Redis, Cache Hit Ratio
6. **Trace**: Trace-spezifische Metriken
7. **Kafka**: Producer/Consumer Errors, DLQ
8. **Neo4j**: Query Latency, Active Queries, Node Counts
9. **Qdrant**: Vector Search Performance
10. **AI Agent & ML**: OpenAI Calls, Token Usage, Risk Scoring
11. **WebSocket**: Active Connections, Message Rates
12. **Auth**: Login Events, Sessions, Rate Limits
13. **Exports**: Report Generation, Email Delivery

---

## 🔧 Setup

### 1. Prometheus Config

Erstelle `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/alerts.yml

scrape_configs:
  - job_name: 'blockchain-forensics'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### 2. Alerts laden

```bash
# Kopiere Alerts
cp monitoring/prometheus-alerts.yml /etc/prometheus/alerts.yml

# Prometheus reload
curl -X POST http://localhost:9090/-/reload
```

### 3. Grafana Dashboard Import

1. Öffne Grafana: http://localhost:3000
2. Navigate zu **Dashboards → Import**
3. Upload: `monitoring/grafana-dashboard.json`
4. Wähle Prometheus Data Source

---

## 📱 Alert Manager

### Email-Benachrichtigungen

```yaml
# alertmanager.yml
route:
  receiver: 'email'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'email'
    email_configs:
      - to: 'ops@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@example.com'
        auth_password: 'xxx'
```

### Slack-Integration

```yaml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/xxx'
        channel: '#alerts'
        title: '{{ .CommonAnnotations.summary }}'
```

---

## 🎯 Best Practices

### 1. **Alert Fatigue vermeiden**

- Nur kritische Alerts als `critical`
- Warnings für degraded Performance
- Info für Trends

### 2. **Dashboard-Organisation**

- Kritische Metriken oben
- Gruppierung nach Service
- Verwende Templates für Multi-Instance

### 3. **Retention Policy**

```yaml
# prometheus.yml
storage:
  tsdb:
    retention.time: 30d
    retention.size: 50GB
```

### 4. **Health Check Timeouts**

- Liveness: 1s Timeout
- Readiness: 2s Timeout
- Detailed: 5s Timeout

---

## 🛠️ Troubleshooting

### Metrics nicht sichtbar

```bash
# Prüfe /metrics Endpoint
curl http://localhost:8000/metrics

# Prüfe Prometheus Targets
open http://localhost:9090/targets
```

### Hohe Latenz

1. Prüfe `/api/health/detailed` für Service-Latenz
2. Checke Prometheus Latency Histograms
3. Query Slow Queries in Neo4j

### Alerts feuern nicht

```bash
# Prüfe Alert Rules
curl http://localhost:9090/api/v1/rules

# Prüfe Alert Status
curl http://localhost:9090/api/v1/alerts
```

---

## 📚 Weitere Ressourcen

- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **FastAPI Metrics**: https://github.com/stephenhillier/starlette_exporter

---

## 🎉 Quick Start

```bash
# 1. Start Infrastructure
docker-compose up -d prometheus grafana

# 2. Verify Metrics
curl http://localhost:8000/metrics

# 3. Open Grafana
open http://localhost:3000  # admin/admin

# 4. Import Dashboard
# Import monitoring/grafana-dashboard.json

# 5. Check Health
curl http://localhost:8000/api/health/detailed | jq
```

---

**Status**: ✅ **Production-Ready Monitoring**  
**Last Updated**: 2025-01-10  
**Version**: 2.0
