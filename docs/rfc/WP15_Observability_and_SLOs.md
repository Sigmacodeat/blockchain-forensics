# RFC: WP15 – Observability & SLOs

## Ziel
Messbare Zuverlässigkeit und Performance für Streams, Rules, Alerts, Cases und ETL durch definierte SLOs, Prometheus-Metriken und Grafana-Dashboards.

## Geltungsbereich
- End-to-End Latenzen (Ingest → RuleEval → Alert Persist → WS)
- Throughput, Error Budgets, Kafka Lag, Worker Utilization
- Dashboards, Alerting-Regeln, Runbooks

## SLOs (Beispiele)
- **Rule Evaluation**: p95 < 100ms, p99 < 200ms
- **E2E Event→Alert**: p95 < 500ms
- **WS Publish→Client Receive**: p95 < 2s
- **Screening (VASP/OFAC/Labels Lookup)**: p95 < 50ms (cached/indexed)
- **ETL Label Update**: 99% Jobs < 2m pro Quelle
- **Availability**: API 99.9% (Rolling 30d)

## Metriken (Prometheus)
- Counter: `rule_eval_total{rule, outcome}`, `alerts_created_total{severity}`, `case_exports_total`, `etl_labels_batches_total{source}`
- Gauges: `kafka_consumer_lag{topic, group}`, `active_rules`, `open_alerts{severity}`, `cases_open`
- Histograms: `rule_eval_latency_seconds`, `alert_persist_latency_seconds`, `e2e_event_alert_latency_seconds`, `ws_publish_latency_seconds`, `screen_latency_seconds{op}`

## Implementierung
- `backend/app/metrics.py`: neue Metriken registrieren (Counter/Gauge/Histogram)
- Instrumentierungspunkte:
  - RuleEngine (Eval-Start/End, Outcome)
  - MonitorConsumer (Event→Persist Latenz)
  - Alerts API (CRUD/Statuswechsel)
  - Cases API (Export Dauer)
  - ETL Pipelines (Batch Dauer/Fehler)
- Export: `/metrics` (bestehend)

### AI Agent Observability (neu)
- Endpunkte: `GET /api/v1/agent/health`, `POST /api/v1/agent/heartbeat`
- Metriken: `TRACE_REQUESTS{op="agent_health|agent_heartbeat|investigate|analyze_address|trace_funds|generate_report",status}` und `TRACE_LATENCY{op}`
- Zweck: schnelle Diagnose (Enabled/Model/Tools-Count) und Heartbeat-Überwachung

#### Agent Tools & Policy Trace (neu)
- Endpunkte (Tools): `GET /api/v1/agent/rules`, `POST /api/v1/agent/rules/simulate`, `GET /api/v1/agent/risk/score`, `GET /api/v1/agent/bridge/lookup`, `POST /api/v1/agent/alerts/trigger`
- Endpunkt (Policy Trace): `POST /api/v1/agent/trace/policy-simulate`
- Metriken:
  - `TRACE_REQUESTS{op=~"agent_rules|agent_rules_simulate|agent_risk_score|agent_bridge_lookup|agent_trigger_alert|agent_trace_policy",status}`
  - `TRACE_LATENCY{op=~"agent_rules|agent_rules_simulate|agent_risk_score|agent_bridge_lookup|agent_trigger_alert|agent_trace_policy"}`
- Recording Rules (`monitoring/prometheus-recording-rules.yml`):
  - `agent_tools_error_rate_5m`, `agent_tools_latency_p95_5m`, `agent_tools_latency_p99_5m`
  - `agent_ops_error_rate_5m`, `agent_ops_latency_p95_5m`, `agent_ops_latency_p99_5m`
  - `agent_trace_policy_error_rate_5m`, `agent_trace_policy_latency_p95_5m`, `agent_trace_policy_latency_p99_5m`

##### SLOs (Vorschlag)
- Tools: p95 < 3s, p99 < 8s, Error-Rate < 2%
- Policy Trace: p95 < 5s, p99 < 8s, Error-Rate < 5%

##### Alerts (`monitoring/prometheus-alerts.yml`)
- Warnungen: Error-Rate > 10% (Tools), p95 > 3s (Tools), p95 > 5s (Policy Trace)
- Kritisch: Error-Rate > 20% (Tools/AgentOps), p99 > 8s (Tools/Policy Trace/AgentOps)

##### Grafana
- Dashboard: `monitoring/grafana-dashboard-agent.json`
- Panels:
  - Error-Rate (tools/ops/policy) via Recording Rules
  - Latenzen p95/p99 (tools/ops/policy) via Recording Rules

## Dashboards (Grafana)
- **KYT Overview**: Rule Eval p95/p99, Hit-Rate, Alerts/min, FP Quote, Top Rules
- **Streaming Health**: Kafka Lag (per Topic/Consumer), Produce/Consume Raten
- **Compliance**: Screening Latenzen, Decision Distribution (allow/review/block)
- **Cases & Evidence**: Exports, Dauer p95, Failures
- **ETL & Labels**: Batches, Dauer, DLQ Größe, Aktualität per Quelle

## Alerting (Prometheus Alerts)
- High Kafka Lag > threshold N min (per Topic)
- E2E Event→Alert p95 > 2s für 5 min
- WS Latenz p95 > 3s für 5 min
- Error Budget Burn (SLO Verletzung) – Multiwindow, Multi-burn-rate

## Runbooks
- Kafka Lag: Scale Consumers, prüfen DLQ, Backpressure
- Rule p95 Degradation: Hot rules identifizieren, Ausdruck vereinfachen/indizieren, Scale Worker
- ETL Failures: Quelle prüfen, Schema-Version, DLQ reprocess
 - Agent Tools Errors: LLM/API/DB/Neo4j/RPC prüfen; Backoff/Rate-Limits validieren; Notfalls Tools temporär deaktivieren
 - Policy Trace Latenz: `max_nodes`/`max_depth` reduzieren, `min_taint_threshold` erhöhen, Decays (`native/token/bridge/utxo`) anpassen, Indexe/Query-Plan prüfen

## Tests
- Unit: Metrik-Emission an Hotspots
- Integration: Synthetic Load + Metrikassertionen (Thresholds)
- E2E: Synthetic Stream Replay mit Latenz-Messung

## Risiken & Mitigation
- Metrik-Kardinalität: Label-Sets begrenzen (z.B. Rules nur Top-N)
- Dashboard-Sprawl: Standardisierte Panels/Folder

## Aufwand/Impact
- Aufwand: Small–Medium
- Impact: Mittel (erhöhte Betriebssicherheit, schnellere Incident-Response)
