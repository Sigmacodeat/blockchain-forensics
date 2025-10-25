# RFC: WP3 – Sanctions Multi-List & Alias Graph

## Ziel
Mehrquellen-Sanktionsscreening (OFAC, UN, EU, UK, nationale FIUs) mit Alias-/AKA-Graph, regelmäßigen Updates, Auditierbarkeit und performanter Screening-API.

## Scope
- Quellen-Lader: OFAC, UN, EU, UK (+ Erweiterungsschnittstelle)
- Normalisierung: Kanonisches Schema für `entity`, `alias`, `list_source`, Relationen
- Alias-/AKA-Graph: Zusammenführung von Schreibweisen, IDs, Adressen, Namen
- Screening-API: Low-latency Lookups, Fuzzy Matching-Policies, Thresholds
- Scheduler/Updater: periodische Fetches, Diffs, Historie, Audit
- Observability: Import-Stats, Coverage, Match-Raten, FP/FN-Quoten

## Datenmodell (DB/Pydantic)
- `sanctioned_entity(id, canonical_name, type, risk_level, first_seen, last_updated)`
- `sanctions_list_source(id, code[ofac|un|eu|uk|...], version, retrieved_at)`
- `entity_alias(id, entity_id, value, kind[name|aka|ens|address], source_id, confidence)`
- Relationen: `entity_alias_map(entity_id, alias_id)`, `entity_list(entity_id, list_source_id)`

## APIs
- `POST /api/v1/sanctions/screen` → {address|name|ens}, options: list filter, fuzzy threshold
- `GET  /api/v1/sanctions/stats` → Quellen, Versionen, Counts, recent updates
- `POST /api/v1/sanctions/reload` (admin)

## Performance/SLO
- p95 Lookup < 5ms (Index in Postgres), Batch 1000 items < 2s
- Update-Laufzeiten überwacht, Backoff bei Quellfehlern

## Sicherheit/Compliance
- Vollständiger Audit-Trail (Ingest → Normalisierung → Änderungen)
- Reproduzierbare Versionierung je Quelle (Hash/ETag)
- GDPR: keine unnötigen PII-Speicherungen; Redaction im Export

## Testplan
- Unit: Parser/Loader (je Quelle), Normalisierung, Fuzzy Matching
- Integration: End-to-end Import → Screen → Audit
- Load: Batch-Screening 1k/10k Items, p95 Targets

## Risiken & Mitigation
- Quelleninstabilität → Caching/Diffs/Fallbacks
- Fuzzy-Matching-Fehlalarme → konfigurierbare Schwellen, Explain-Output
