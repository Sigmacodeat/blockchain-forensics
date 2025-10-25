# RFC: WP4 – VASP Screening & Travel Rule

## Ziel
Bewertung von Gegenparteien/VASPs (Jurisdiktion, Sanktions-/Risikoprofil) und Unterstützung von Travel-Rule-Nachrichten (Schemas, Send/Receive) für AML-Compliance.

## Scope
- VASP-Verzeichnis (Profile, Jurisdiktion, Trust/Compliance-Score)
- Screening-API (schnell, indexgestützt), Policy-Auswertung
- Travel-Rule (TRP) Mock-Schemas: Send/Receive, Validierung, Logging
- Admin-Management (VASP-Onboarding, Policy-Weights)

## Betroffene Komponenten
- Backend: `backend/app/compliance/vasp_service.py` (neu), `backend/app/api/v1/compliance.py` (Endpunkte), `backend/app/models/vasp.py` (neu)
- DB/Infra: `infra/postgres/init.sql` (vasps, vasp_contacts, vasp_policies)
- Security: `backend/app/auth/dependencies.py` für RBAC (Admin)
- Tests: `backend/tests/test_compliance_vasp.py`

## Datenmodelle (DB/Pydantic)
- Vasp(id, name, domain, jurisdiction, licenses JSON, sanctions JSON, trust_score, contacts JSON, last_reviewed_at)
- VaspPolicy(id, key, weight, threshold, updated_at)
- VaspScreeningLog(id, vasp_id, counterparty_address, chain, result JSON, created_at)
- TravelRuleMessage(id, direction[in|out], vasp_id, payload JSON, status, created_at)

## APIs
- `GET /api/v1/compliance/vasps?query=` (Suche)
- `POST /api/v1/compliance/vasps` (Create/Update)
- `POST /api/v1/compliance/screen-vasp` (Input: address/chain → Mapping + Score)
- `POST /api/v1/compliance/travel-rule/send` (payload validate + persist)
- `POST /api/v1/compliance/travel-rule/receive` (mock ingest + ack)

## Screening-Logik (MVP)
- Resolve: Address→Entity→Known VASP? (Labels/Provenance nutzen; Fallback: Heuristik)
- Score: Jurisdiktion, Sanktions-Risiko, historische Alerts, policy weights
- Output: `score`, `factors[]`, `policy_decision` (allow/review/block)

## Observability & SLO
- p95 Screening < 50ms; Cache/Indexing über Postgres GIN + Redis
- Metriken: screenings/min, decision distribution, false positives

## Sicherheit & Audit
- RBAC: Admin (write), Analyst/Auditor (read/screen)
- Audit: alle Travel-Rule Messages & Decisions persistiert

## Testplan
- Unit: Scoring-Funktionen, Policy-Weights, Payload-Validierung
- Integration: screen-vasp E2E, Travel-Rule send/receive Logs

## Risiken & Mitigation
- Unvollständige VASP-Daten: Admin-UI + Import (CSV) + Scheduled Reviews
- Mapping-Fehler: Confidence/Provenance in Output anzeigen

## Aufwand/Impact
- Aufwand: Medium
- Impact: Hoch (Compliance-Parität zu Elliptic/TRM/Chainalysis)
