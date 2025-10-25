# Blockchain Forensics Platform - Vollständige Dokumentation

## Übersicht

Eine umfassende Blockchain-Forensik-Plattform für die Analyse von Kryptowährungstransaktionen, Risikobewertung und Compliance-Überwachung.

## Architektur

### Backend (FastAPI + Python)
- **API Layer**: RESTful APIs für alle Funktionen
- **Service Layer**: Business Logic und Datenverarbeitung
- **Data Layer**: PostgreSQL, Neo4j, Redis, Qdrant
- **AI Layer**: Machine Learning und AI-Agents

### Frontend (React + TypeScript)
- **Dashboard**: Übersicht und Monitoring
- **Analytics**: Graph-Visualisierung und Berichte
- **Case Management**: Untersuchungsverfolgung
- **Alert System**: Echtzeit-Benachrichtigungen

## Hauptfunktionen

### 🔍 **Transaction Tracing**
- **40+ Blockchains**: EVM, UTXO, SVM, Cosmos, Polkadot, Privacy Chains
- **Cross-Chain-Bridge-Erkennung**: 11 Major Bridges (Wormhole, Stargate, etc.)
- **Taint Analysis**: FIFO, Proportional, Haircut Models
- **Rekursives N-Hop-Tracing**: Unbegrenzte Tiefe
- **Gerichtsverwertbar**: Timestamped Logs, <1% Fehlertoleranz

### ⚠️ **Alert Engine**
- Rule-basierte Alert-Generierung
- 6 konfigurierbare Alert-Typen
- Deduplication und Suppression
- Multi-Channel-Benachrichtigungen

### 📊 **Graph Analytics**
- Neo4j-basierte Graph-Datenbank
- Entity Relationship Mapping
- Clustering und Community Detection
- Visual Analytics Dashboard

### 🏛️ **Case Management**
- Vollständiges Untersuchungsmanagement
- Evidence Chain-of-Custody
- Audit Trail und Compliance
- Report Generation

### 💬 **Kommentar-System**
- Entity-spezifische Kommentare
- Thread-basierte Diskussionen
- Internal/External Kommentare
- Like und Mention System

### 👥 **User Management**
- **RBAC**: 4 Rollen (Admin, Analyst, Auditor, Viewer)
- **JWT-Authentifizierung**: Access + Refresh Tokens
- **Plan-based Access**: 6 Pläne (Community bis Enterprise)
- **Audit Logging**: 15+ Action Types in TimescaleDB
- **Session Management**: Secure Token Storage

### 🤖 **AI Agents**
- **LangChain-Orchestrierung**: Autonome Forensik-Workflows
- **12+ Tools**: Trace, Risk Score, Bridge Lookup, Threat Intel, etc.
- **RAG (Retrieval-Augmented Generation)**: Smart Contract Knowledge Base
- **Real-Time Streaming**: SSE-basierte Agent-Updates

### 🧬 **ML & Risk Scoring**
- **100+ Features**: Transaction, Network, Temporal, Entity, Risk
- **XGBoost Classifier**: Binary Risk Classification
- **SHAP Explainability**: Transparente ML-Decisions
- **Real-Time Inference**: <50ms Risk Score Calculation
- **Wallet Clustering**: 100+ Heuristics für Wallet-Gruppierung

### 🔒 **Compliance & Sanctions**
- **Multi-Sanctions**: OFAC, UN, EU, UK, CA, AU, CH, JP, SG (9 Jurisdictions)
- **O(1) Screening**: <1ms Address Lookup via PostgreSQL Index
- **Fuzzy Name Matching**: Levenshtein Distance für Namen
- **Batch Screening**: Bis 1000 Adressen parallel
- **Travel Rule**: FATF-compliant, IVMS101, OpenVASP/TRP

### 🕵️ **Threat Intelligence**
- **14 REST Endpoints**: Statistics, Enrich, Query, Community Reports
- **Dark Web Monitoring**: 4 Marketplaces, 3 Forums, IOC-Extraction
- **Intel Sharing Network**: Org-to-Org Intelligence (TRM Beacon-Style)
- **Community Intelligence**: Chainalysis Signals-Style Reporting
- **Address Enrichment**: Multi-Source Threat Scoring

### 📊 **Smart Contract Analysis**
- **Risk Scoring**: Security Audits, Proxy Patterns, Critical Functions
- **ABI Decoding**: Automatic Method & Event Decoding
- **Contract Intelligence**: Source Verification, Creator Tracking
- **Bytecode Analysis**: Similarity Detection, Pattern Matching

### 🔐 **Privacy Coin Analysis**
- **Tornado Cash Demixing**: 65-75% Success Rate
- **Ring Signature Analysis**: Monero Heuristics
- **Stealth Address Tracking**: Privacy Coin Flow Analysis
- **Mixer Detection**: Automatic Pattern Recognition

## API-Endpunkte

### Authentication
- `POST /api/v1/auth/login` - Benutzeranmeldung
- `POST /api/v1/auth/logout` - Abmeldung
- `GET /api/v1/users/me` - Aktueller Benutzer

### Cases
- `GET /api/v1/cases` - Fälle auflisten
- `POST /api/v1/cases` - Fall erstellen
- `GET /api/v1/cases/{id}` - Fall abrufen
- `POST /api/v1/cases/{id}/evidence` - Evidence hinzufügen

### Comments
- `GET /api/v1/comments` - Kommentare auflisten
- `POST /api/v1/comments` - Kommentar erstellen
- `GET /api/v1/comments/{id}/replies` - Antworten abrufen

### Alerts
- `GET /api/v1/alerts/recent` - Aktuelle Alerts
- `POST /api/v1/alerts/acknowledge/{id}` - Alert bestätigen
- `GET /api/v1/alerts/stats` - Alert-Statistiken

### Tracing
- `POST /api/v1/trace/start` - Trace starten
- `GET /api/v1/trace/status/{trace_id}` - Trace-Status
- `GET /api/v1/trace/result/{trace_id}` - Trace-Ergebnisse
- `POST /api/v1/trace/export` - Export (CSV/JSON/GraphML)

### Graph Analytics
- `GET /api/v1/graph/nodes` - Graph-Knoten
- `GET /api/v1/graph/paths` - Pfad-Analyse
- `POST /api/v1/graph/clustering` - Clustering (Louvain, Label Propagation)
- `GET /api/v1/graph-analytics/centrality` - PageRank, Betweenness
- `GET /api/v1/graph-analytics/patterns` - Circle, Layering, Smurfing

### AI Agent
- `POST /api/v1/agent/chat` - Chat mit Agent (SSE)
- `GET /api/v1/agent/capabilities` - Tool-Liste
- `POST /api/v1/agent/orchestrate` - Workflow starten

### Risk Scoring
- `GET /api/v1/risk/stream` - Real-Time Risk Score (SSE)
- `POST /api/v1/ml/train` - Model Training
- `GET /api/v1/ml/evaluate` - Model Evaluation
- `POST /api/v1/ml/explain` - SHAP Explainability

### Threat Intelligence
- `GET /api/v1/threat-intel/statistics` - Intel Statistics
- `POST /api/v1/threat-intel/enrich` - Address Enrichment
- `POST /api/v1/threat-intel/query` - Query Intel
- `POST /api/v1/threat-intel/community/report` - Community Report

### Sanctions & Compliance
- `POST /api/v1/sanctions/screen` - Screen Address/Name
- `POST /api/v1/sanctions/batch-screen` - Batch Screening
- `GET /api/v1/ofac/statistics` - OFAC Statistics
- `POST /api/v1/travel-rule/submit` - Travel Rule Submission

### Smart Contracts
- `POST /api/v1/contracts/analyze` - Contract Analysis
- `GET /api/v1/contracts/risk-score/{address}` - Risk Score
- `POST /api/v1/contracts/decode` - ABI Decoding

### Bridge Transfers
- `GET /api/v1/bridge/transfers` - Bridge Transfers
- `POST /api/v1/bridge/detect` - Bridge Detection
- `GET /api/v1/bridge/paths/{address}` - Cross-Chain Paths

### WebSocket
- `ws://localhost:8000/api/v1/ws` - WebSocket Connection
  - Room: `alerts` - Real-Time Alerts
  - Room: `high_risk` - High-Risk Transactions
  - Room: `bridge_events` - Bridge Events
  - Room: `enrichment` - Enrichment Updates

## Datenmodelle

### Case Model
```python
class Case(BaseModel):
    id: str
    title: str
    description: str
    status: CaseStatus  # open, investigating, closed
    priority: CasePriority  # low, medium, high, critical
    assigned_to: Optional[str]
    tags: List[str]
    related_addresses: List[str]
    created_at: datetime
```

### Alert Model
```python
class Alert(BaseModel):
    alert_id: str
    alert_type: AlertType  # high_risk_address, sanctioned_entity, etc.
    severity: AlertSeverity  # low, medium, high, critical
    title: str
    description: str
    address: Optional[str]
    tx_hash: Optional[str]
    acknowledged: bool
```

### Comment Model
```python
class Comment(BaseModel):
    id: str
    entity_type: str  # case, alert, address, etc.
    entity_id: str
    content: str
    author_id: str
    parent_id: Optional[str]  # Für Threading
    status: CommentStatus  # active, hidden, deleted
```

## Installation & Setup

### Voraussetzungen
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Schnellstart
```bash
# Repository klonen
git clone <repository-url>
cd blockchain-forensics

# Services starten
docker-compose up -d

# Frontend Development
cd frontend
npm install
npm run dev

# Backend läuft automatisch auf http://localhost:8000
# Frontend auf http://localhost:3002
```

### Umgebungsvariablen
```bash
# Backend (.env)
POSTGRES_URL=postgresql://user:pass@localhost:5432/forensics
NEO4J_URI=bolt://localhost:7687
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your-key

# Frontend (.env)
VITE_API_URL=http://localhost:8000
```

## Entwicklung

### Backend Development
```bash
cd backend
python -m pytest tests/ -v  # Tests ausführen
uvicorn app.main:app --reload  # Development Server
```

### Frontend Development
```bash
cd frontend
npm run dev  # Development Server
npm run build  # Production Build
npm run test  # Tests ausführen
```

### Datenbankschema Updates
```bash
cd backend
alembic revision --autogenerate -m "Update schema"
alembic upgrade head
```

## Sicherheit

### Authentication
- JWT-basierte Authentifizierung
- Password Hashing mit PBKDF2
- Session Management mit Redis

### Authorization
- Role-basierte Zugriffskontrolle (RBAC)
- Admin, Investigator, Analyst, Viewer Rollen
- Granulare Berechtigungen pro Ressource

### Compliance
- Audit Logging für alle Aktionen
- Evidence Chain-of-Custody
- eIDAS-kompatible Signaturen
- GDPR-konforme Datenverarbeitung

## Monitoring & Observability

### Metriken
- Prometheus-Metriken für alle Services
- Grafana-Dashboards für Visualisierung
- Alert-basierte Überwachung

### Logging
- Strukturierte Logs mit JSON-Format
- Log Aggregation mit ELK Stack
- Audit Trail für Compliance

### Health Checks
- `/health` - System Health
- `/api/health/detailed` - Detaillierte Checks
- Datenbank-Konnektivitätstests

## Performance

### Optimierungen
- Connection Pooling für alle Datenbanken
- Redis-Caching für häufige Queries
- Async Processing für I/O-intensive Operationen
- Graph Query Optimization

### Skalierbarkeit
- Horizontale Skalierung mit Docker
- Load Balancing für API-Services
- Event-driven Architecture mit Kafka

## Tests

### Test-Coverage
- Unit Tests für alle Modelle
- Integration Tests für APIs
- E2E Tests für kritische Workflows
- Performance Tests für Skalierbarkeit

### Test-Ausführung
```bash
# Alle Tests
pytest tests/ -v --cov=app

# Nur API Tests
pytest tests/test_api_endpoints.py -v

# Performance Tests
pytest tests/test_performance.py -v
```

## Deployment

### Production Setup
```bash
# Mit Produktionskonfiguration
docker-compose -f docker-compose.prod.yml up -d

# Migrationen anwenden
docker-compose exec backend alembic upgrade head

# SSL/TLS aktivieren
# Load Balancer konfigurieren
```

### Monitoring Stack
- Prometheus für Metriken
- Grafana für Dashboards
- AlertManager für Benachrichtigungen
- Loki für Log Aggregation

## API Dokumentation

### Swagger UI
- `/docs` - Interaktive API-Dokumentation
- Automatische OpenAPI-Spezifikation
- Request/Response-Beispiele

### Postman Collection
- Vollständige API-Collection verfügbar
- Umgebungsvariablen für verschiedene Deployments
- Automatisierte Tests

## Support & Wartung

### Backup-Strategie
- Tägliche Datenbank-Backups
- Point-in-Time Recovery für PostgreSQL
- Graph-Datenbank-Snapshots

### Updates
- Rolling Updates ohne Downtime
- Datenbank-Migrationen mit Zero-Downtime
- Feature Flags für neue Funktionen

### Troubleshooting
- Umfassende Logging für Debugging
- Health Check Endpunkte für Monitoring
- Admin-Panel für Systemdiagnose

## 📚 Weitere Dokumentation

### Feature-Dokumentation
- **[AI Agents](./docs/features/ai-agents.md)** - LangChain, Tools, Workflows
- **[Risk Copilot](./docs/features/risk-copilot.md)** - Real-Time Risk Scoring
- **[Threat Intelligence](./docs/features/threat-intelligence.md)** - Dark Web, Intel Sharing
- **[Clustering](./docs/features/clustering.md)** - Wallet-Clustering Heuristiken
- **[Smart Contracts](./docs/features/smart-contracts.md)** - Contract Analysis
- **[Privacy Demixing](./docs/features/privacy-demixing.md)** - Tornado Cash, Mixer Analysis
- **[Screening](./docs/features/screening.md)** - Multi-Sanctions Screening
- **[Access Control](./docs/features/access-control.md)** - Plan-basierte Features
- **[Monitoring](./docs/features/monitoring.md)** - Prometheus, Grafana, Alerts
- **[Features Overview](./docs/features/overview.md)** - Alle Features im Überblick

### Business-Dokumentation
- **[Business Plan 2025](./docs/business/BUSINESS_PLAN_2025.md)** - FFG Förderantrag
- **[Competitive Analysis](./docs/COMPETITIVE_ANALYSIS_2025.md)** - vs. Chainalysis, TRM Labs

### Setup-Dokumentation
- **[Installation](./INSTALLATION.md)** - Detaillierte Installation
- **[Deployment](./DEPLOYMENT_GUIDE.md)** - Production Deployment
- **[Development](./DEVELOPMENT.md)** - Development Setup
- **[Testing](./TESTING_GUIDE.md)** - Test Execution

---

**Version**: 1.0.0  
**Letzte Aktualisierung**: 18. Oktober 2025  
**Status**: Production Ready ✅  
**Chains**: 40+  
**Test Coverage**: 95%+  
**Sprachen**: 43 (i18n)
