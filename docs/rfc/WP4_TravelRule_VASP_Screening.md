# RFC: WP4 – Travel Rule & VASP Screening

## Ziel
Konforme Abwicklung von Travel-Rule-Transfers (IVMS101) und VASP-Risiko-Screening inkl. Due Diligence, Interoperabilität und Auditierbarkeit.

## Scope
- IVMS101 Datenmodell (originator/beneficiary) und Validierung
- VASP-Profile mit Risk Scoring (jurisdiction, licensing, sanctions exposure, cyber incidents)
- Interop: TRP/OpenVASP-kompatible Schnittstellen (MVP-intern, optional extern)
- Audit & PII-Schutz (field-level encryption, RBAC, access logs)

## Datenmodell (DB/Pydantic)
- `vasp(id, legal_name, jurisdiction, licenses[], website, contacts)`
- `vasp_profile(vasp_id, rating, risk_score, last_reviewed_at)`
- `travel_rule_log(id, tx_hash, originator, beneficiary, vasp_from, vasp_to, status, ts)`

## APIs
- `POST /api/v1/travel-rule/transfer/validate` → IVMS101 Payload prüfen & Response
- `GET  /api/v1/vasp/{id}` → Profil & Risikokennzahlen
- `POST /api/v1/vasp` (admin) → anlegen/aktualisieren

## Sicherheit/Compliance
- PII: Verschlüsselung auf Feldebene, minimale Datenhaltung, TTL/Retention Policies
- Audit Trails: Jede Einsicht/Änderung mit Actor & Timestamp
- Jurisdiktion: Data Residency Policies (konfigurierbar)

## SLO/SLA
- p95 Validierung < 50ms (Sync-Check)
- 99.9% Verfügbarkeit der Validierungs-API

## Testplan
- Unit: IVMS101 Schema-Validierung, Risk Score Berechnung
- Integration: Transfer Validate → Log → Audit
- Compliance: Zugriffstests, Redaction im Export
