# Installation & Setup Guide
## Blockchain Forensics Platform

## 🚀 Quick Start

### Voraussetzungen
- **Node.js:** 18+ (für Frontend)
- **Python:** 3.11+ (für Backend)
- **Docker & Docker Compose:** Für Infrastruktur
- **Git:** Für Version Control

---

## 📦 Installation

### 1. Repository klonen
```bash
git clone <repository-url>
cd blockchain-forensics
```

### 2. Backend Setup

#### a) Environment-Variablen
```bash
cp .env.example .env
```

Wichtige Settings in `.env`:
```env
# Database
POSTGRES_URL=postgresql://user:pass@localhost:5432/blockchain_forensics
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
REDIS_URL=redis://localhost:6379/0

# Blockchain RPCs
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
BITCOIN_RPC_URL=http://localhost:8332

# Email (Optional)
EMAIL_ENABLED=true
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# ML (Optional)
OPENAI_API_KEY=sk-...
```

#### b) Infrastruktur starten
```bash
cd backend
docker-compose up -d
```

Services:
- PostgreSQL (Port 5432)
- Neo4j (Port 7687, 7474)
- Redis (Port 6379)
- Kafka (Port 9092)
- Qdrant (Port 6333)

#### c) Dependencies installieren
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### d) Datenbank initialisieren
```bash
# Migrations
alembic upgrade head

# Optional: Demo-Daten
python -m app.cli seed-demo --addresses 100
```

#### e) Backend starten
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API:** `http://localhost:8000`  
**Docs:** `http://localhost:8000/docs`

---

### 3. Frontend Setup

#### a) Dependencies installieren
```bash
cd frontend
npm install

# Graph-Visualisierung
npm install vis-network vis-data

# UI-Komponenten
npm install @radix-ui/react-dialog @radix-ui/react-tabs @radix-ui/react-select
```

#### b) Environment-Variablen
```bash
cp .env.example .env.local
```

Inhalt von `.env.local`:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-google-oauth-id
```

#### c) Frontend starten
```bash
npm run dev
```

**App:** `http://localhost:3000`

---

## 🔧 Entwicklungs-Workflow

### Terminal-Setup (Empfohlen)
```bash
# Terminal 1: Infrastruktur
cd backend && docker-compose up

# Terminal 2: Backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 3: Frontend
cd frontend && npm run dev
```

### Hot-Reload
- **Backend:** Automatisch via `--reload`
- **Frontend:** Automatisch via Vite

---

## 🧪 Testing

### Backend-Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend-Tests
```bash
cd frontend
npm run test
npm run test:e2e  # Playwright
```

---

## 🐳 Docker-Produktion

### Komplette Umgebung
```bash
docker-compose -f docker-compose.prod.yml up -d
```

Services:
- `backend`: FastAPI (Port 8000)
- `frontend`: Nginx mit Static-Build (Port 3000)
- `postgres`, `neo4j`, `redis`, `kafka`

### Nur Backend
```bash
docker build -t forensics-backend -f backend/Dockerfile .
docker run -p 8000:8000 forensics-backend
```

---

## 📊 Monitoring

### Health-Checks
- **Backend:** `http://localhost:8000/health`
- **WebSocket:** `http://localhost:8000/api/v1/ws/health`
- **Neo4j:** `http://localhost:7474`
- **Kafka UI:** `http://localhost:9021` (falls Confluent)

### Logs
```bash
# Backend
tail -f backend/logs/app.log

# Docker
docker-compose logs -f backend
```

### Metrics (Optional)
- **Prometheus:** Port 9090
- **Grafana:** Port 3001
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

---

## 🔐 Security

### Produktions-Checklist
1. ✅ Ändere `SECRET_KEY` in `.env`
2. ✅ Setze `DEBUG=False`
3. ✅ Konfiguriere `CORS_ORIGINS` restriktiv
4. ✅ Aktiviere HTTPS (`FORCE_HTTPS_REDIRECT=True`)
5. ✅ Nutze Secrets-Management (AWS Secrets, Vault)
6. ✅ Firewall-Regeln für Ports
7. ✅ Backup-Strategie für Postgres/Neo4j

### SSL/TLS
```bash
# Certbot für Let's Encrypt
sudo certbot --nginx -d yourdomain.com
```

---

## 🗄️ Datenbank-Migrations

### Neue Migration erstellen
```bash
cd backend
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
```

### Rollback
```bash
alembic downgrade -1
```

---

## 🌐 Deployment

### AWS/Cloud
1. **Backend:** ECS/EKS mit Docker-Image
2. **Frontend:** S3 + CloudFront oder Vercel
3. **Databases:** RDS (Postgres), Managed Neo4j (Aura)
4. **Cache:** ElastiCache (Redis)

### Kubernetes (Optional)
```bash
kubectl apply -f k8s/
```

Manifests in `/k8s`:
- `backend-deployment.yaml`
- `frontend-deployment.yaml`
- `postgres-statefulset.yaml`
- `ingress.yaml`

---

## 📚 Weitere Ressourcen

### Dokumentation
- **API-Docs:** `http://localhost:8000/docs` (Swagger)
- **Frontend-Features:** `/FRONTEND_FEATURES.md`
- **Architecture:** `/docs/architecture.md`

### Troubleshooting
- **Port bereits belegt:** `lsof -i :8000` und `kill -9 <PID>`
- **Docker-Probleme:** `docker system prune -a`
- **Neo4j-Fehler:** `docker-compose restart neo4j`
- **npm-Fehler:** `rm -rf node_modules package-lock.json && npm install`

---

## 🎓 Development-Tipps

### VSCode-Extensions (Empfohlen)
- **Python:** ms-python.python
- **ESLint:** dbaeumer.vscode-eslint
- **Prettier:** esbenp.prettier-vscode
- **Docker:** ms-azuretools.vscode-docker

### Git-Hooks (Pre-Commit)
```bash
pip install pre-commit
pre-commit install
```

### Code-Formatierung
```bash
# Backend
black backend/app
isort backend/app

# Frontend
npm run format
npm run lint
```

---

## 🔄 Updates

### Dependencies aktualisieren
```bash
# Backend
pip list --outdated
pip install -U <package>

# Frontend
npm outdated
npm update
```

### Platform-Update
```bash
git pull origin main
docker-compose pull
docker-compose up -d --build
```

---

## 💾 Backup

### Manuelle Backups
```bash
# Postgres
docker exec -t postgres pg_dump -U user blockchain_forensics > backup.sql

# Neo4j
docker exec -t neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j.dump

# Redis (automatisch via RDB)
docker exec -t redis redis-cli BGSAVE
```

### Restore
```bash
# Postgres
docker exec -i postgres psql -U user blockchain_forensics < backup.sql

# Neo4j
docker exec -t neo4j neo4j-admin load --from=/backups/neo4j.dump --database=neo4j --force
```

---

## 🆘 Support

### Logs sammeln
```bash
# Diagnostic Bundle
./scripts/collect-logs.sh  # Erstellt logs.tar.gz
```

### Issues melden
- **GitHub:** Issues mit Logs + Schritte zur Reproduktion
- **Slack:** #dev-support Channel
- **Email:** support@blockchain-forensics.com

---

## ✅ Verification

Nach Installation alles testen:

```bash
# Backend Health
curl http://localhost:8000/health

# Frontend läuft
curl http://localhost:3000

# WebSocket funktioniert
wscat -c ws://localhost:8000/ws/alerts

# API-Trace
curl -X POST http://localhost:8000/api/v1/trace \
  -H "Content-Type: application/json" \
  -d '{"source_address":"0x123..."}'
```

**✅ Wenn alle Requests erfolgreich → Installation abgeschlossen!**

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2025-01-16  
**Autor:** Development Team
