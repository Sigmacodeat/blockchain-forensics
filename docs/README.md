# Dokumentations-Index

**Blockchain Forensics Platform** - Vollständige Dokumentationsübersicht

## 📚 Core-Dokumentation (Root-Verzeichnis)

### Hauptdokumentation
- **[README.md](../README.md)** - Hauptübersicht, Features, Quick Start
- **[DOCUMENTATION.md](../DOCUMENTATION.md)** - Vollständige Plattform-Dokumentation
- **[INSTALLATION.md](../INSTALLATION.md)** - Detaillierte Installationsanleitung
- **[DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)** - Produktions-Deployment
- **[DEVELOPMENT.md](../DEVELOPMENT.md)** - Entwickler-Setup & Guidelines
- **[TESTING_GUIDE.md](../TESTING_GUIDE.md)** - Test-Strategien & Ausführung

## 🚀 Feature-Dokumentation

Detaillierte Dokumentationen zu spezifischen Features:

### AI & Intelligenz
- **[AI Agents](./features/ai-agents.md)** - LangChain-Orchestrierung, Tools, Workflows
- **[Risk Copilot](./features/risk-copilot.md)** - Real-Time Risk Scoring mit SSE
- **[Threat Intelligence](./features/threat-intelligence.md)** - Dark Web Monitoring, Intel Sharing

### Blockchain-Analyse
- **[Clustering](./features/clustering.md)** - Wallet-Clustering mit 100+ Heuristiken
- **[Smart Contracts](./features/smart-contracts.md)** - Contract-Analyse & Risk-Scoring
- **[Privacy Demixing](./features/privacy-demixing.md)** - Tornado Cash & Mixer-Analyse

### Compliance & Security
- **[Universal Screening](./features/screening.md)** - Multi-Sanctions (OFAC, UN, EU, UK, CA, AU, CH, JP, SG)
- **[Access Control](./features/access-control.md)** - Plan-basierte Features, RBAC

### System
- **[Monitoring](./features/monitoring.md)** - Prometheus, Grafana, Alerts
- **[Features Overview](./features/overview.md)** - State-of-the-Art Features Übersicht

## 💼 Business-Dokumentation

- **[Business Plan 2025](./business/BUSINESS_PLAN_2025.md)** - FFG Förderantrag, Work Packages, Budget
- **[Competitive Analysis 2025](./COMPETITIVE_ANALYSIS_2025.md)** - Wettbewerbsanalyse vs. Chainalysis, TRM Labs, Elliptic

## 📖 API-Dokumentation

### REST APIs
- **Swagger UI**: `http://localhost:8000/docs` (wenn Server läuft)
- **ReDoc**: `http://localhost:8000/redoc`

### Wichtige Endpoints
- **Authentication**: `/api/v1/auth/*`
- **Tracing**: `/api/v1/trace/*`
- **Cases**: `/api/v1/cases/*`
- **AI Agent**: `/api/v1/agent/*`
- **Analytics**: `/api/v1/analytics/*`
- **Threat Intel**: `/api/v1/threat-intel/*`
- **Risk Scoring**: `/api/v1/risk/*`

### WebSocket
- **Real-Time**: `ws://localhost:8000/api/v1/ws`
- **Alerts**: Room `alerts`
- **Bridge Events**: Room `bridge_events`

## 🔧 Zusätzliche Dokumentation

### Postman & Insomnia
- **[Postman Collection](./collections/Blockchain-Forensics.postman_collection.json)**
- **[Insomnia Collection](./collections/Blockchain-Forensics.insomnia.json)**

### SDK-Beispiele
- **[Python SDK](./examples/sdk/python/)** - Beispiele für Python-Integration
- **[Node.js SDK](./examples/sdk/nodejs/)** - Beispiele für Node.js-Integration

### RFCs (Request for Comments)
- **[WP1: KYT Transaction Monitoring](./rfc/WP1_KYT_Transaction_Monitoring_Engine.md)**
- **[WP2: Case Management](./rfc/WP2_Case_Management_and_Evidence.md)**
- **[WP15: Observability & SLOs](./rfc/WP15_Observability_and_SLOs.md)**

## 🎯 Schnellstart-Links

### Für Entwickler
1. [Installation](../INSTALLATION.md) - Setup in 5 Minuten
2. [Development](../DEVELOPMENT.md) - Dev-Environment einrichten
3. [Testing](../TESTING_GUIDE.md) - Tests ausführen

### Für Anwender
1. [README](../README.md#quick-start) - Quick Start Guide
2. [Features Overview](./features/overview.md) - Was kann die Plattform?
3. [Access Control](./features/access-control.md) - Welcher Plan hat welche Features?

### Für Business
1. [Business Plan](./business/BUSINESS_PLAN_2025.md) - Förderung & Roadmap
2. [Competitive Analysis](./COMPETITIVE_ANALYSIS_2025.md) - Marktposition

## 📊 Plattform-Statistiken

- **40+ Blockchains** unterstützt
- **100+ ML-Features** für Risk Scoring
- **14 Threat Intel Endpoints**
- **70+ API Endpoints**
- **43 Sprachen** (i18n)
- **95%+ Test Coverage**

## 🔗 Externe Links

- **GitHub**: (Wird nach Veröffentlichung hinzugefügt)
- **Website**: (Wird nach Deployment hinzugefügt)
- **Support**: (Wird konfiguriert)

---

**Zuletzt aktualisiert**: 18. Oktober 2025  
**Version**: 1.0.0  
**Status**: Production Ready ✅
