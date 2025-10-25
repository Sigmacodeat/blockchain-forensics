# RFC: WP2 – Case Management & Evidence

## Ziel
Fallverwaltung mit Tasks/Notizen/Anhängen, gerichtsfester Evidence-Handling (Hashing/Manifest) und Export-Bundles.

## Scope
- Case-Entity, Items (note/task/evidence/link)
- Evidence-Hashing (SHA-256), `manifest.json` mit Pfaden+Hashes
- Export ZIP (PDF Reports, JSON, Manifest)
- RBAC & Audit Trail

## Betroffene Komponenten
- Backend: `backend/app/models/` (Cases, CaseItems, Evidence), `backend/app/api/v1/cases.py` (neu), `backend/app/reports/`, `backend/app/services/`
- Frontend: `frontend/src/pages/CasePage.tsx` (neu), `frontend/src/pages/TraceResultPage.tsx` (Verknüpfung), `frontend/src/components/TraceGraph.tsx` (Annotations→Case)
- DB/Infra: `infra/postgres/init.sql`
- Tests: `backend/tests/test_advanced_reports.py`, neu `backend/tests/test_cases_api.py`

## Datenmodelle (DB/Pydantic)
- Case(id, title, status, priority, owner, tags[], created_at, updated_at)
- CaseItem(id, case_id, type[note|task|evidence|link], content JSON/text, actor, created_at)
- Evidence(id, case_id, sha256, source_type[trace|report|file], uri/path, timestamp, signature optional)

## APIs
- `POST /api/v1/cases` | `GET /api/v1/cases?status=&owner=` | `GET /api/v1/cases/{id}`
- `POST /api/v1/cases/{id}/items` (note/task/evidence)
- `POST /api/v1/cases/{id}/export` → ZIP (PDF, JSON, `manifest.json`)

## Integrationen
- Reports: `backend/app/reports/pdf_generator.py`
- Traces/Graph: Verlinkung aus `TraceResultPage.tsx`, Speicherung als Evidence-Link

## Sicherheit
- RBAC: Viewer (read), Auditor (read/export), Analyst (create items), Admin (manage)
- Audit: Case/Item Änderungen in TimescaleDB

## Observability
- Metriken: Cases created, Exports, Evidence verifiziert, Export Dauer p95

## Testplan
- Unit: Hash/Manifest-Erzeugung, RBAC-Guards
- Integration: Case CRUD, Items, Export-Bundle-Verifikation (Hash-Match)

## Risiken & Mitigation
- Datenintegrität: Hash-Verifikation beim Export
- PII: Redaction im Export konfigurierbar

## Aufwand/Impact
- Aufwand: Medium
- Impact: Sehr hoch (gerichtsfeste Arbeitsweise, Team-Kollaboration)
