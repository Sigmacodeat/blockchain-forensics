# Development Guide

## Projektstruktur

```
blockchain-forensics/
├── backend/               # FastAPI Backend
│   ├── app/
│   │   ├── adapters/     # Chain-spezifische Adapter (Ethereum, etc.)
│   │   ├── ai_agents/    # LangChain AI Agents
│   │   ├── api/          # FastAPI Routes
│   │   │   └── v1/       # API v1 Endpoints
│   │   ├── db/           # Database Clients (Neo4j, Postgres, Redis, Qdrant)
│   │   ├── enrichment/   # Labels, ABI Decoder
│   │   ├── messaging/    # Kafka Clients
│   │   ├── ml/           # ML Models (XGBoost, Clustering)
│   │   ├── schemas/      # Pydantic Schemas
│   │   ├── tracing/      # Transaction Tracing Engine
│   │   ├── config.py     # Settings
│   │   └── main.py       # FastAPI Entry Point
│   ├── tests/            # Tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # React Frontend
│   ├── src/
│   │   ├── components/   # UI Components
│   │   ├── lib/          # API Client, Types
│   │   ├── pages/        # Page Components
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
├── infra/                # Infrastructure
│   └── postgres/
│       └── init.sql      # Database Schema
├── docker-compose.yml
└── README.md

## AI Agent Tools API (neu)

Die AI-Agent-Tools können jetzt direkt per REST aufgerufen werden (neben der autonomen Nutzung durch den Agenten). Endpunkte befinden sich in `backend/app/api/v1/agent.py`.

### Endpunkte

- `GET /api/v1/agent/risk/score?address=0x...`
  - Antwort: `{ address, risk_score, risk_level, factors, confidence }`

- `GET /api/v1/agent/bridge/lookup?chain=polygon&address=0x...&method_selector=0x...`
  - Antwort: Informationen zu Bridge-Contracts/Methoden oder Registry-Statistiken

- `POST /api/v1/agent/alerts/trigger`
  - Body: `{ "alert_type": "high_risk|sanctioned|large_transfer|mixer", "address?": "0x...", "tx_hash?": "0x...", "risk_score?": 0.8, "labels?": ["mixer"], "value_usd?": 100000 }`
  - Antwort: `{"submitted_event": {...}, "alerts_triggered": [...], "count": N }`

- `GET /api/v1/agent/rules`
  - Antwort: `{ rules: [{ rule_id, name, enabled }], total }`

- `POST /api/v1/agent/rules/simulate`
  - Body: `{ "address?": "0x...", "labels?": ["mixer"], "risk_score?": 0.8, "value_usd?": 100000, ... }`
  - Antwort: `{ event, triggered_count, alerts: [...] }`

- `POST /api/v1/agent/trace/policy-simulate`
  - Body: `{ "source_address": "0x...", "max_depth": 4, "max_nodes": 500, "min_taint_threshold": 0.01, "enable_native": true, "enable_token": true, "enable_bridge": true, "enable_utxo": true, "native_decay": 1.0, "token_decay": 1.0, "bridge_decay": 0.9, "utxo_decay": 1.0 }`
  - Antwort: `{ summary: { trace_id, completed, nodes, edges, execution_time_seconds, high_risk, sanctioned }, result: {...} }`

Hinweise:

- **Feature Flag**: `ENABLE_AI_AGENTS=true` erforderlich (siehe `backend/app/config.py`).
- **Auth/JWT**: Falls globale Auth aktiviert ist, sind Bearer-Tokens erforderlich.
- **Secrets**: `SECRET_KEY` muss gesetzt sein (lokal z.B. via Env-Var).

### RBAC & Rate Limits

- **RBAC (optional)**: Per Flag `ENABLE_AGENT_TOOL_RBAC=true` aktivierbar (siehe `backend/app/config.py`).
  - Rollen (siehe `app/auth/models.py`): `admin`, `analyst`, `auditor`, `viewer`.
  - Standard-Zugriff (wenn RBAC aktiv):
    - `risk-score`: admin, analyst, auditor
    - `bridge-lookup`: admin, analyst, auditor, viewer
    - `trigger-alert`: admin
    - `alert-rules`: admin, analyst, auditor, viewer
    - `simulate-alerts`: admin, analyst

- **Rate Limits** (siehe `app/middleware/rate_limit.py`):
  - `/api/v1/agent/tools/risk-score`: 60/min
  - `/api/v1/agent/tools/bridge-lookup`: 120/min
  - `/api/v1/agent/tools/trigger-alert`: 10/min
  - `/api/v1/agent/tools/alert-rules`: 120/min
  - `/api/v1/agent/tools/simulate-alerts`: 30/min
```

## Policy-gesteuertes Tracing (Kanal-Toggles & Decays)

Unterstützte Parameter in `TraceRequest` und `TraceRequestAPI` (`backend/app/tracing/models.py`, `backend/app/api/v1/trace.py`):

- `enable_native` (bool, default true): Native Coin-Flows berücksichtigen
- `enable_token` (bool, default true): Token/NFT-Flows berücksichtigen
- `enable_bridge` (bool, default true): Cross-Chain Expansion über BRIDGE_LINKs
- `enable_utxo` (bool, default true): UTXO-Flows berücksichtigen
- `native_decay` (0-1): Dämpfung für native Flows
- `token_decay` (0-1): Dämpfung für Token/NFT Flows
- `bridge_decay` (0-1): Dämpfung für Cross-Chain Hops
- `utxo_decay` (0-1): Dämpfung für UTXO Flows

Beispiel (Trace API):

```bash
curl -X POST http://localhost:8000/api/v1/trace/start \
  -H 'Content-Type: application/json' \
  -d '{
    "source_address": "0x123...",
    "direction": "forward",
    "max_depth": 4,
    "max_nodes": 500,
    "enable_token": false,
    "enable_bridge": true,
    "bridge_decay": 0.8
  }'
```

## Token- und NFT-Metadaten für Tainting

Der Tracer liest optionale Felder in `tx.metadata` (`backend/app/tracing/tracer.py`):

- `erc20_transfers`: Array von Transfers `{ token, from, to, amount }`
  - Verteilung proportional nach `amount` auf Empfänger
- `erc721_transfers`: Array von Transfers `{ token, from, to, tokenId }`
  - Gleichmäßige Verteilung auf alle ausgehenden Transfers von `from`
- `erc1155_transfers`: Array von Transfers `{ token, from, to, id, amount }`
  - Verteilung proportional nach `amount`

Erzeugte Kanten-Typen (`TraceEdge.event_type`): `token_transfer`, `nft_transfer`, `nft1155_transfer`, zusätzlich `bridge` und generische native/utxo.

## Observability & Dashboards

Prometheus-Metriken (`backend/app/metrics.py`):

- `trace_edges_created_total{event_type}`: Anzahl erzeugter Trace-Kanten pro Typ
- `trace_requests_total{op,status}` / `trace_request_latency_seconds_bucket{op}`: Request-Zähler/Latency
- `bridge_events_total{stage}`: Bridge-Events (detected/persisted/error)

Alerts (`monitoring/prometheus-alerts.yml`):

- `TraceEdgesCreatedZero`: Keine neuen Kanten in 10m
- `TraceEdgesBridgeMissing`: Keine Bridge-Kanten in 15m
- `TraceEdgesTypeSkew`: >90% Kanten ein einzelner Typ in 5m

Grafana (`monitoring/grafana-dashboard.json`):

- Row "Trace Edges" mit Panels:
  - Stat: `sum(rate(trace_edges_created_total[5m]))`
  - Timeseries nach `event_type`: `sum by (event_type) (rate(trace_edges_created_total[5m]))`

## Entwicklungs-Workflow

### Backend Development

```bash
cd backend
source venv/bin/activate

# Code-Formatierung
black app/ tests/

# Linting
flake8 app/ tests/

# Type-Checking
mypy app/

# Tests ausführen
pytest tests/ -v

# Coverage
pytest tests/ --cov=app --cov-report=html

# Backend starten mit Auto-Reload
uvicorn app.main:app --reload --log-level debug
```

### Frontend Development

```bash
cd frontend

# Formatierung & Linting
npm run lint

# Development Server
npm run dev

# Production Build
npm run build
```

### API Endpunkte

#### Tracing API
- `POST /api/v1/trace/start` - Trace starten
- `GET /api/v1/trace/{trace_id}` - Trace-Ergebnis abrufen
- `GET /api/v1/trace/{trace_id}/graph` - Graph-Daten
- `GET /api/v1/trace/{trace_id}/report` - Forensik-Report

#### AI Agent API
- `POST /api/v1/agent/investigate` - AI-gestützte Untersuchung
- `POST /api/v1/agent/analyze-address` - Schnelle Adressanalyse
- `POST /api/v1/agent/trace-funds` - AI Funds Tracing
- `POST /api/v1/agent/generate-report` - Report-Generierung
- `GET /api/v1/agent/capabilities` - Agent-Capabilities

#### Enrichment API
- `POST /api/v1/enrich/labels` - Labels abrufen
- `POST /api/v1/enrich/abi-decode` - ABI dekodieren
- `POST /api/v1/enrich/risk-score` - ML Risk Score
- `GET /api/v1/enrich/sanctions-check` - OFAC Screening

### Database Queries

#### Neo4j (Graph Database)
```cypher
// Alle Traces anzeigen
MATCH (a:Address)-[t:TRANSACTION]->(b:Address)
RETURN a, t, b
LIMIT 100

// High-Risk Addresses
MATCH (a:Address)
WHERE a.risk_score > 0.7
RETURN a
```

#### TimescaleDB (Metrics)
```sql
-- Transactions in letzten 24h
SELECT COUNT(*) 
FROM transactions 
WHERE timestamp > NOW() - INTERVAL '24 hours';

-- Durchschnittlicher Risk Score
SELECT time_bucket('1 hour', timestamp) AS hour,
       AVG(risk_score) as avg_risk
FROM transactions
GROUP BY hour
ORDER BY hour DESC;
```

### ML Model Training

```bash
# XGBoost Risk Classifier Training
cd backend
python -c "
import xgboost as xgb
import pickle

model = xgb.XGBClassifier()
with open('models/risk_classifier.json', 'wb') as f:
    pickle.dump(model, f)
"
```

## Projektstatus

Alle priorisierten Funktionen sind implementiert und produktionsreif. Details siehe `COMPLETE_PROJECT_STATUS_2025.md`.

## Debugging

### Backend Logs
```bash
# Alle Container Logs
docker-compose logs -f

# Nur Backend
docker-compose logs -f backend

# Neo4j Logs
docker-compose logs -f neo4j
```

### Common Issues

**Neo4j Connection Failed:**
```bash
# Neo4j neu starten
docker-compose restart neo4j

# Status prüfen
docker-compose exec neo4j cypher-shell -u neo4j -p forensics_password_change_me "RETURN 1"
```

**Kafka Not Ready:**
```bash
# Warte bis Kafka läuft
docker-compose logs kafka | grep "started (kafka.server.KafkaServer)"

# Topics erstellen
docker-compose exec kafka kafka-topics --create --topic trace.requests --bootstrap-server localhost:9092
```

**Postgres Migration:**
```bash
# Manuell Schema erstellen
docker-compose exec postgres psql -U forensics -d blockchain_forensics -f /docker-entrypoint-initdb.d/init.sql
```

## Best Practices

### Code-Style
- **Python**: Black (Formatierung), Flake8 (Linting), MyPy (Type-Checking)
- **TypeScript**: ESLint, Prettier
- **Commits**: Conventional Commits (feat:, fix:, docs:, etc.)

### API Design
- RESTful Endpoints
- Pydantic für Validation
- Klare Error Messages (HTTPException mit detail)
- Swagger Docs unter `/docs`

### Testing
- Unit Tests für alle Business Logic
- Integration Tests für API
- Pytest mit Fixtures
- Coverage-Ziel: 80%+

### Security
- Nie API Keys im Code
- JWT für Auth
- CORS korrekt konfiguriert
- Input Validation (Pydantic)
- SQL Injection Prevention (SQLAlchemy)

## Nützliche Commands

```bash
# Alle Services stoppen
docker-compose down

# Volumes löschen (Clean Start)
docker-compose down -v

# Einzelnen Service neu bauen
docker-compose up -d --build backend

# In Container einloggen
docker-compose exec backend sh
docker-compose exec neo4j bash

# Postgres Shell
docker-compose exec postgres psql -U forensics -d blockchain_forensics
```

## Ressourcen

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LangChain Docs](https://python.langchain.com/)
- [Neo4j Graph Database](https://neo4j.com/docs/)
- [TimescaleDB](https://docs.timescale.com/)
- [React Query v5](https://tanstack.com/query/latest)
