# 📊 Monitoring Examples & Recipes

Praktische Beispiele für alltägliche Monitoring-Aufgaben

---

## 🔍 PromQL Queries

### API Performance

```promql
# Request Rate (Requests pro Sekunde)
sum(rate(chain_requests_total[5m])) by (op)

# Error Rate (Prozent)
sum(rate(chain_requests_total{status!="ok"}[5m])) / sum(rate(chain_requests_total[5m])) * 100

# P95 Latency für Trace Operations
histogram_quantile(0.95, sum by (le,op) (rate(trace_request_latency_seconds_bucket[5m])))

# Langsame Requests (>1s)
histogram_quantile(0.99, sum by (le) (rate(chain_request_latency_seconds_bucket[5m]))) > 1
```

### Database Health

```promql
# Neo4j Connection Status
neo4j_up

# Postgres Query Rate
rate(postgres_queries_total[5m])

# Redis Cache Hit Rate
sum(rate(jsonrpc_cache_hits_total[5m])) / 
(sum(rate(jsonrpc_cache_hits_total[5m])) + sum(rate(jsonrpc_cache_misses_total[5m])))

# Qdrant Collections
qdrant_collections_total
```

### AI & ML

```promql
# OpenAI Token Verbrauch (letzte Stunde)
sum(increase(openai_tokens_used_total[1h]))

# ML Risk Scoring Fehlerrate
rate(ml_risk_score_requests_total{status="error"}[5m]) / 
rate(ml_risk_score_requests_total[5m])

# AI Agent Request Distribution
sum by (operation) (rate(ai_agent_requests_total[5m]))
```

### Security

```promql
# Failed Login Attempts (letzte 5 Min)
sum(increase(auth_events_total{event="login_failed"}[5m]))

# Rate Limit Violations pro Endpoint
sum by (endpoint) (rate(rate_limit_exceeded_total[5m]))

# Aktive Sessions
auth_active_sessions
```

---

## 📈 Grafana Dashboards

### Custom Panels

#### 1. **Request Heatmap**

```json
{
  "type": "heatmap",
  "title": "Request Latency Heatmap",
  "targets": [
    {
      "expr": "sum by (le) (rate(chain_request_latency_seconds_bucket[5m]))",
      "format": "heatmap"
    }
  ]
}
```

#### 2. **Error Rate Gauge**

```json
{
  "type": "gauge",
  "title": "API Error Rate",
  "targets": [
    {
      "expr": "sum(rate(chain_requests_total{status!=\"ok\"}[5m])) / sum(rate(chain_requests_total[5m]))"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percentunit",
      "thresholds": {
        "steps": [
          { "color": "green", "value": 0 },
          { "color": "yellow", "value": 0.01 },
          { "color": "orange", "value": 0.05 },
          { "color": "red", "value": 0.1 }
        ]
      }
    }
  }
}
```

#### 3. **Top 5 Langsame Endpoints**

```promql
topk(5, 
  histogram_quantile(0.95, 
    sum by (le,op) (rate(trace_request_latency_seconds_bucket[5m]))
  )
)
```

---

## 🚨 Alert Examples

### Custom Alerts

#### High Memory Usage (Neo4j)

```yaml
- alert: Neo4jHighMemory
  expr: |
    (neo4j_memory_heap_used_bytes / neo4j_memory_heap_max_bytes) > 0.85
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Neo4j Memory Usage >85%"
    description: "Heap: {{ $value | humanizePercentage }}"
```

#### Trace Backlog

```yaml
- alert: TraceBacklogHigh
  expr: |
    sum(kafka_consumer_lag_messages{topic="trace.requests"}) > 1000
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Trace request backlog >1000"
    description: "{{ $value }} pending traces"
```

#### Blockchain RPC Down

```yaml
- alert: BlockchainRPCDown
  expr: |
    rate(chain_requests_total{status="error"}[5m]) > 0.5
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Blockchain RPC häufig fehlerhaft"
    description: "Prüfe ETHEREUM_RPC_URL und Rate Limits"
```

---

## 📊 Logging Examples

### Structured Logging in Code

```python
from app.utils.structured_logging import (
    get_logger,
    log_trace_event,
    log_performance,
    log_security_event
)

logger = get_logger(__name__)

# Trace Event
log_trace_event(
    logger,
    event="trace_completed",
    trace_id="abc-123",
    hops=5,
    high_risk_count=2,
    duration_ms=234.5
)

# Performance Logging
log_performance(
    logger,
    operation="neo4j_query",
    duration_ms=123.45,
    query="MATCH (n) RETURN count(n)",
    rows=50000
)

# Security Event
log_security_event(
    logger,
    event_type="unauthorized_access",
    user_id="user-123",
    ip_address="192.168.1.100",
    endpoint="/api/v1/admin/users"
)
```

### Log Queries (JSON Logs)

```bash
# Filter by Request ID
cat app.log | jq 'select(.request_id == "abc-123")'

# Find Slow Requests
cat app.log | jq 'select(.extra.performance.duration_ms > 1000)'

# Security Events
cat app.log | jq 'select(.extra.security != null)'

# Errors with Stack Traces
cat app.log | jq 'select(.level == "ERROR") | {message, exception}'
```

---

## 🔧 Troubleshooting Recipes

### Problem: Hohe Latenz

```bash
# 1. Check Health
curl http://localhost:8000/api/health/detailed | jq

# 2. Identify Slow Services
curl http://localhost:8000/api/health/detailed | jq '.services | to_entries | map({service: .key, latency: .value.latency_ms}) | sort_by(.latency) | reverse'

# 3. Check Prometheus
curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,sum(rate(trace_request_latency_seconds_bucket[5m]))by(le))' | jq

# 4. Neo4j Slow Queries
# In Neo4j Browser:
CALL dbms.listQueries() YIELD query, elapsedTimeMillis 
WHERE elapsedTimeMillis > 1000 
RETURN query, elapsedTimeMillis 
ORDER BY elapsedTimeMillis DESC
```

### Problem: Memory Leak

```bash
# 1. Check Prometheus Metrics
curl 'http://localhost:9090/api/v1/query?query=process_resident_memory_bytes' | jq

# 2. Docker Stats
docker stats backend

# 3. Python Memory Profile (in container)
docker exec -it backend python -m memory_profiler app/main.py
```

### Problem: High Error Rate

```bash
# 1. Error Distribution
curl 'http://localhost:9090/api/v1/query?query=sum(rate(chain_requests_total{status!="ok"}[5m]))by(status)' | jq

# 2. Recent Errors (Logs)
docker logs backend --tail 100 | grep ERROR

# 3. Alert Status
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state == "firing")'
```

---

## 📱 Monitoring Dashboard URLs

### Quick Access

```bash
# Health Check
open http://localhost:8000/api/health/detailed

# Metrics
open http://localhost:8000/metrics

# Prometheus
open http://localhost:9090

# Grafana
open http://localhost:3001  # admin/admin

# Neo4j Browser
open http://localhost:7475  # neo4j/forensics_password_change_me

# API Docs
open http://localhost:8000/docs
```

---

## 🎯 SLO Monitoring

### Service Level Objectives

```yaml
# availability.yml
slos:
  - name: api_availability
    target: 99.9%
    query: |
      sum(rate(chain_requests_total{status="ok"}[30d])) /
      sum(rate(chain_requests_total[30d]))
  
  - name: trace_latency_p95
    target: 2.0  # seconds
    query: |
      histogram_quantile(0.95, 
        sum(rate(trace_request_latency_seconds_bucket[30d])) by (le)
      )
  
  - name: error_budget
    target: 0.1%  # 0.1% error rate
    query: |
      sum(rate(chain_requests_total{status!="ok"}[30d])) /
      sum(rate(chain_requests_total[30d]))
```

### Burn Rate Alerts

```yaml
# Fast Burn (6x normal rate)
- alert: ErrorBudgetFastBurn
  expr: |
    sum(rate(chain_requests_total{status!="ok"}[1h])) /
    sum(rate(chain_requests_total[1h])) > 0.006
  for: 5m
  
# Slow Burn (3x normal rate)  
- alert: ErrorBudgetSlowBurn
  expr: |
    sum(rate(chain_requests_total{status!="ok"}[6h])) /
    sum(rate(chain_requests_total[6h])) > 0.003
  for: 30m
```

---

## 🔐 Security Monitoring

### Detect Suspicious Activity

```promql
# Brute Force Detection
sum(increase(auth_events_total{event="login_failed"}[5m])) by (user_id) > 10

# Unusual API Usage
sum(rate(chain_requests_total[5m])) by (user_id) > 100

# Failed Auth Spike
deriv(auth_events_total{event="login_failed"}[5m]) > 2
```

### Audit Log Queries

```bash
# Recent Admin Actions
curl http://localhost:8000/api/v1/audit?action_type=admin&limit=50 | jq

# User Activity Timeline
curl http://localhost:8000/api/v1/audit?user_id=user-123&limit=100 | jq
```

---

## 📊 Capacity Planning

### Growth Metrics

```promql
# Request Growth Rate (Month over Month)
(sum(rate(chain_requests_total[30d])) - 
 sum(rate(chain_requests_total[30d] offset 30d))) /
sum(rate(chain_requests_total[30d] offset 30d)) * 100

# Database Growth
increase(neo4j_graph_nodes_total[7d])
increase(postgres_table_size_bytes[7d])

# Storage Usage Projection (30 days)
predict_linear(postgres_table_size_bytes[7d], 30*24*3600)
```

---

## 🎨 Custom Grafana Variables

### Add Query Variables

```json
{
  "templating": {
    "list": [
      {
        "name": "environment",
        "type": "query",
        "query": "label_values(chain_requests_total, environment)",
        "multi": false
      },
      {
        "name": "time_range",
        "type": "interval",
        "options": ["5m", "15m", "1h", "6h", "24h"]
      }
    ]
  }
}
```

### Use in Panels

```promql
# Filter by environment variable
sum(rate(chain_requests_total{environment="$environment"}[5m]))
```

---

## 📖 Further Reading

- **Prometheus Best Practices**: https://prometheus.io/docs/practices/
- **Grafana Tutorials**: https://grafana.com/tutorials/
- **PromQL Cheat Sheet**: https://promlabs.com/promql-cheat-sheet/
- **SRE Monitoring**: https://sre.google/sre-book/monitoring-distributed-systems/

---

**Happy Monitoring! 📊**
