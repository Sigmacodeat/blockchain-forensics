# RFC: WP5 – Label Coverage Expansion & Data Provenance

## Ziel
Breite, qualitätsgesicherte Label-Abdeckung (DeFi, NFT, Bridges, Mixer, Scam-Cluster, Services/VASPs) mit klarer Herkunft (`source`), Vertrauensmaß (`confidence`) und Aktualität – als Fundament für Investigations, KYT und Compliance.

## Scope
- ETL-Pipeline(n) für externe/Interne Label-Quellen (CSV/JSON/API)
- Deduplizierung & Entity-Fusion (Canonical Entity Graph)
- Provenance-Felder in allen Label-Antworten (Quelle, Methode, Timestamp)
- Scheduled Updates & Backfills; Delta-Updates; Retry/Dead-letter
- API-Erweiterungen für Labels/Entities mit Filter/Suche/Confidence

## Betroffene Komponenten
- Backend: `backend/app/enrichment/labels_service.py` (Erweiterung), `backend/app/normalizer/` (Semantik), `backend/app/db/` (Persistenz/Indices)
- Streaming: `backend/app/ingest/` (ETL Jobs), `backend/app/streaming/` (optionale Events `labels.updated`)
- APIs: `backend/app/api/v1/labels.py`, `backend/app/api/v1/enrichment.py`
- DB/Infra: `infra/postgres/init.sql` (Tables/Indices/Mat. Views)
- Tests: `backend/tests/test_labels_service.py`, `backend/tests/test_labels_api.py`

## Datenmodelle (DB/Pydantic)
- `label_sources`(id, name, type[defi|nft|bridge|mixer|scam|vasp|exchange|dex|lender], provenance_uri, license, refresh_interval, enabled)
- `entity_labels`(id, entity_key, entity_type[address|contract|collection|service], label, category, source_id, confidence float, first_seen_at, last_seen_at, metadata JSON)
- `entities`(entity_key, canonical_id, type, attrs JSON, updated_at)  // optional Canonical Graph Mapping
- Mat. Views: `mv_entity_label_latest` (letzter Stand pro entity+category), `mv_defi_top` etc.

## ETL & Prozesse
- Loader: CSV/JSON/API Fetcher, Validierung/Schema-Mapping
- Dedupe: (entity_key, label, source) unique; Merge auf `canonical_id`
- Scheduler: Cron (e.g. APScheduler/Celery) – täglich/6h je nach Quelle
- DLQ/Retry: fehlerhafte Batches in `labels_dlq` mit Fehlerursache

## API-Design
- `GET /api/v1/labels/{entity}` → `labels[]` mit `source`, `confidence`, `last_updated`, `category`
- `GET /api/v1/labels/search?category=&q=&min_confidence=`
- `GET /api/v1/entities/{id}` → konsolidiertes Entity-Profil (Labels, Links, Provenance)
- `POST /api/v1/labels/bulk` (analyst-curated adds) mit Review-Flag

## Provenance & Qualität
- Jedes Label: `source` (Provider/URI), `method` (heuristic/manual/api), `confidence` (0..1), `timestamp`
- Review-Workflow: analyst-curated Labels mit `review_status` (pending/approved/rejected)

## Observability & SLO
- Ingestion-Dauer p95 < 2m pro Quelle (Batch)
- API-Lookup p95 < 10ms (Index + Redis Cache)
- Metriken: Labels total, per category/source, Update-Latenz, DLQ size

## Sicherheit & Governance
- Lizenz/ToS-Tracking je Quelle; Redaction-Policies
- Feature Flags: Quelle aktiv/deaktivierbar

## Testplan
- Unit: Mapping/Validation, Dedupe, Confidence-Handling
- Integration: Quelle→ETL→DB→API Ausgabe mit Provenance
- Backfill: historischer Import simuliert, Latest-View korrekt

## Risiken & Mitigation
- Datenqualität: Confidence/Provenance verpflichtend; Review-Flags
- Drift/Schemabrüche: Versionierte Mappings, Contract Tests je Quelle

## Aufwand/Impact
- Aufwand: Medium
- Impact: Sehr hoch (Qualität/Nützlichkeit sämtlicher Analysen und KYT)
