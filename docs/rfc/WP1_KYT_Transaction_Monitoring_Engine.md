# RFC: WP1 – KYT/Transaction Monitoring Engine

## Ziel
Kontinuierliches, regelbasiertes Screening von Transaktionen/Adressen mit Echtzeit-Alerts, Triage und SLA – vergleichbar mit Chainalysis KYT / Elliptic Navigator / TRM Compliance.

## Scope
- Regel-DSL (JSON-basiert) für address/tx/chain Scopes
- Echtzeit-Kafka-Consumer, Evaluierung, Alert-Persistenz
- Alert-Lifecycle (open/assign/snooze/close), Triage-Queues
- API: Rules, Alerts, Notes; Idempotenz & SLA
- Observability (Prometheus/Grafana): Latenzen, Hit-Rate, FP-Quote

## Betroffene Komponenten
- `backend/app/compliance/` (neu): `rule_engine.py`, `models.py`, `services.py`
- `backend/app/streaming/`: `monitor_consumer.py` (neu)
- `backend/app/api/v1/`: `compliance.py` (rules), `alerts.py` (alerts)
- `backend/app/db/postgres_client.py`, `infra/postgres/init.sql` (Tables)
- `backend/app/messaging/` (Kafka Producer/Consumer)
- `backend/app/metrics.py`, `monitoring/grafana-dashboard.json`

## Datenmodell (DB/Pydantic)
- Rule(id, name, version, enabled, expression, severity, scope, created_at, updated_at)
- Alert(id, rule_id, entity_type, entity_id, chain, severity, status, assignee, first_seen_at, last_seen_at, hits, context JSON, sla_due_at)
- AlertEvent(id, alert_id, type, payload JSON, created_at, actor)

## APIs
- `GET /api/v1/monitor/rules`
- `POST /api/v1/monitor/rules` (create/update)
- `PATCH /api/v1/monitor/rules/{id}/toggle`
- `POST /api/v1/monitor/rules/validate` (Dry-Run)
- `GET /api/v1/alerts`
- `PATCH /api/v1/alerts/{id}` (status/assignee/snooze)
- `POST /api/v1/alerts/{id}/notes`

## Regel-DSL (MVP)
- Operatoren: `any`, `all`, `not`, Vergleich (`>`, `>=`, `<`, `<=`, `==`)
- Felder: `tx.value_usd`, `entity.risk_score`, `indirect_exposure.hops`, `ofac_match`, `counterparty.vasp_trust`
- Beispiel:
```json
{
  "all": [
    {"indirect_exposure": {"source": "sanctioned", "hops": { ">=": 2 }}},
    {"risk_score": { ">=": 0.8 }},
    {"tx.value_usd": { ">=": 10000 }}
  ],
  "not": {"counterparty.vasp_trust": {"<": 0.4}}
}
```

## Streaming & Topics
- Eingehend: `ingest.events`
- Intern: `monitor.events`
- Ausgehend: `alerts` → WebSocket Bridge (`backend/app/websockets/`)

## Observability (SLO/SLA)
- p95 Rule-Evaluierung < 100ms, p99 < 200ms
- End-to-End Event→Alert persistiert p95 < 500ms
- Dashboards: Alert Throughput, Rule Hit-Rate, FP-Quote, Kafka Lag

## Sicherheit & Idempotenz
- Idempotency-Key: `alert:{entity}:{rule}:window` via Redis TTL
- RBAC: Rules (Admin), Alerts (Analyst/Auditor/Admin)
- Audit: `AlertEvent` für jede Statusänderung

## Testplan
- Unit: DSL Parser/Evaluator, Idempotenz, SLA Timer
- Integration: Kafka→Evaluator→DB→API→WS End-to-End
- Load: 1000 TPS synthetische Events (p95 Targets)

## Risiken & Mitigation
- FP-Quote: Simulation/Shadow Mode vor Go-Live
- Backpressure: Kafka-Lag Monitoring, Worker-Scaling

## Aufwand/Impact
- Aufwand: Large
- Impact: Sehr hoch (Marktangleichung an KYT)
