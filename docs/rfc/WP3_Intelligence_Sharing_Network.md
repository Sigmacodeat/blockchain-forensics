# RFC: WP3 – Intelligence-Sharing Network (Beacon-ähnlich)

## Ziel
Verifizierte Organisationen (LE, VASPs, Compliance-Teams) teilen Flags/Tipps/Reports zu Adressen/Entitäten in nahezu Echtzeit – inkl. Provenance, Sichtbarkeits-Policies und Auditierbarkeit.

## Scope
- Organisations-/Mitglieder-Modelle, Trust-Level
- ShareEvents (flag/report/tip) mit Visibility (whitelist), Provenance, Redaction
- WS/SSE-Stream für Echtzeit-Konsum; REST-Query/Replay
- RBAC, Rate-Limits, Consent/Retention/Revocation Policies

## Betroffene Komponenten
- Backend: `backend/app/websockets/`, `backend/app/api/v1/alerts.py`, `backend/app/api/v1/sharing.py` (neu), `backend/app/security/`, `backend/app/models/`
- Streaming: Kafka Topics `share.events`, Bridge zur WS-Schicht
- DB/Infra: `infra/postgres/init.sql`
- Tests: `backend/tests/test_intel_sharing_api.py`, WS-Integrationstests

## Datenmodelle
- Organization(id, name, domain, trust_level, created_at)
- Member(id, org_id, user_id, role, created_at)
- ShareEvent(id, org_id, type, entity_type, entity_id, payload JSON, visibility JSON, provenance JSON, created_at)

## APIs
- `POST /api/v1/sharing/flags` (create)
- `GET /api/v1/sharing/stream` (WS/SSE, Filter: entity, type, orgs)
- `GET /api/v1/sharing/search?entity=&type=&since=`
- Admin: `POST /api/v1/sharing/orgs` (Onboarding), `POST /api/v1/sharing/members`

## Policies & Sicherheit
- Verifizierungs-Flow (Domain, ToS, DPA)
- Visibility: Whitelist/Org-groups; Redaction von PII
- Rate-Limits pro Org
- Audit-Logs aller ShareEvents

## Observability
- Metriken: Events/min, Stream Latenz, Dropped (policy/limit), Replay Hits

## Testplan
- Unit: Visibility-Filter, Provenance-Serialisierung, Redaction
- Integration: Publish→Kafka→WS Receive, Replay via REST
- Load: 100 EPS, Latenz p95 < 2s

## Risiken & Mitigation
- Datenmissbrauch: Trust-Level, Revocation, Abuse-Detection
- Rechtliches: Terms/Consent, Retention-Policies

## Aufwand/Impact
- Aufwand: Large
- Impact: Sehr hoch (Differenzierung vs. Markt, Parität zu TRM Beacon)
