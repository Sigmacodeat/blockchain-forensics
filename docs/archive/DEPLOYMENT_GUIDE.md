# 🚀 Blockchain Forensics Platform - Deployment Guide

**Version**: 1.0.0  
**Letzte Aktualisierung**: 11.10.2025

---

## 📋 Inhaltsverzeichnis

1. [Systemanforderungen](#systemanforderungen)
2. [Installation](#installation)
3. [Konfiguration](#konfiguration)
4. [Services starten](#services-starten)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Production Best Practices](#production-best-practices)

---

## 🖥️ Systemanforderungen

### Minimum (Development)
- **CPU**: 4 Cores
- **RAM**: 16 GB
- **Disk**: 50 GB SSD
- **OS**: Ubuntu 22.04 LTS / macOS 12+ / Windows 11 WSL2

### Empfohlen (Production)
- **CPU**: 16 Cores
- **RAM**: 64 GB
- **Disk**: 500 GB NVMe SSD
- **OS**: Ubuntu 22.04 LTS
- **Network**: 1 Gbps

### Software Dependencies
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Python**: 3.11+
- **Node.js**: 18+
- **Git**: 2.40+

---

## 📦 Installation

### 1. Repository klonen
```bash
git clone https://github.com/your-org/blockchain-forensics.git
cd blockchain-forensics
```

### 2. Environment Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend
```bash
cd frontend
npm install
```

### 3. Datenbanken mit Docker Compose starten
```bash
cd infra
docker-compose up -d
```

**Services:**
- Neo4j: `http://localhost:7474` (User: neo4j, Pass: siehe .env)
- TimescaleDB: `localhost:5432`
- Redis: `localhost:6379`
- Qdrant: `http://localhost:6333`
- Kafka: `localhost:9092`

### 4. Datenbanken initialisieren

#### Postgres/TimescaleDB
```bash
cd backend
psql -h localhost -U postgres -f infra/postgres/init.sql
```

#### Neo4j
```cypher
// Im Neo4j Browser (http://localhost:7474)
CREATE CONSTRAINT address_unique IF NOT EXISTS FOR (a:Address) REQUIRE a.address IS UNIQUE;
CREATE INDEX address_index IF NOT EXISTS FOR (a:Address) ON (a.address);
CREATE INDEX trace_index IF NOT EXISTS FOR (t:Trace) ON (t.trace_id);
```

---

## ⚙️ Konfiguration

### Backend (.env)
Kopiere `.env.example` zu `.env`:

```bash
cd backend
cp .env.example .env
```

**Wichtige Variablen:**
```bash
# Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=forensics

REDIS_HOST=localhost
REDIS_PORT=6379

# Blockchain RPC
ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_EVENTS=ingest.events
KAFKA_TOPIC_TRACE_REQUESTS=trace.requests
KAFKA_TOPIC_ENRICH_REQUESTS=enrich.requests
KAFKA_TOPIC_ALERTS=alerts.events

# AI Agents (optional)
OPENAI_API_KEY=your_openai_key
ENABLE_AI_AGENTS=true

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
SECRET_KEY=generate_with_openssl_rand_base64_32
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# OFAC Auto-Update
OFAC_UPDATE_INTERVAL_HOURS=24

# Workers
ENABLE_WORKERS=true
```

### Frontend (.env)
```bash
cd frontend
cp .env.example .env
```

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

---

## 🚀 Services starten

### Option 1: Development (Manuell)

#### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm run dev
```

#### Workers (separates Terminal)
```bash
cd backend
./start_workers.sh
```

### Option 2: Production (systemd)

#### Backend Service
```bash
sudo nano /etc/systemd/system/forensics-api.service
```

```ini
[Unit]
Description=Blockchain Forensics API
After=network.target docker.service

[Service]
Type=simple
User=forensics
WorkingDirectory=/opt/blockchain-forensics/backend
Environment="PATH=/opt/blockchain-forensics/backend/venv/bin"
ExecStart=/opt/blockchain-forensics/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Workers Service
```bash
sudo nano /etc/systemd/system/forensics-workers.service
```

```ini
[Unit]
Description=Blockchain Forensics Workers
After=network.target docker.service kafka.service

[Service]
Type=simple
User=forensics
WorkingDirectory=/opt/blockchain-forensics/backend
Environment="PATH=/opt/blockchain-forensics/backend/venv/bin"
ExecStart=/opt/blockchain-forensics/backend/start_workers.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Services aktivieren
```bash
sudo systemctl daemon-reload
sudo systemctl enable forensics-api
sudo systemctl enable forensics-workers
sudo systemctl start forensics-api
sudo systemctl start forensics-workers
```

### Option 3: Docker (Complete Stack)

```bash
# Build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Logs
docker-compose logs -f api workers
```

---

## 📊 Monitoring

### Health Checks

#### Backend API
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "neo4j": "connected",
  "postgres": "connected",
  "redis": "connected"
}
```

#### Workers Status
```bash
# Check processes
ps aux | grep "trace_consumer\|enrichment_consumer\|alert_consumer"

# Check Kafka consumer groups
docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list
```

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

### Grafana Dashboard
1. Open: `http://localhost:3001`
2. Login: admin/admin
3. Import Dashboard: `monitoring/grafana-dashboard.json`

---

## 🐛 Troubleshooting

### Backend startet nicht
```bash
# Check logs
tail -f backend/logs/app.log

# Test database connections
cd backend
python -c "from app.db.neo4j_client import neo4j_client; import asyncio; asyncio.run(neo4j_client.health())"
```

### Workers konsumieren nicht
```bash
# Check Kafka topics
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list

# Check consumer lag
docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group trace-consumer
```

### Neo4j GDS Plugin fehlt
```bash
# Download GDS plugin
cd infra/neo4j/plugins
wget https://github.com/neo4j/graph-data-science/releases/download/2.5.0/neo4j-graph-data-science-2.5.0.jar

# Restart Neo4j
docker-compose restart neo4j
```

### Frontend API Fehler
```bash
# Check CORS settings in backend .env
CORS_ORIGINS=http://localhost:3000

# Check API is reachable
curl http://localhost:8000/api/v1/health
```

---

## 🔒 Production Best Practices

### Security

1. **SSL/TLS aktivieren**
```bash
# Nginx reverse proxy
sudo apt install nginx certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

2. **API Rate Limiting**
```python
# app/config.py - bereits konfiguriert
RATE_LIMIT_PER_MINUTE = 60
```

### Database Migrations

1. **Alembic Setup**
```bash
# Initialize (once per project)
cd backend
python -m alembic init alembic

# Update alembic.ini with correct database URL
# (already configured: postgresql://forensics:forensics_pass@localhost:5435/blockchain_forensics)

# Generate initial migration (captures current schema)
python -m alembic revision --autogenerate -m "initial_schema"

# Create specific migrations for new tables
python -m alembic revision -m "add_alert_annotations"
# Edit the migration file to add CREATE TABLE statements
```

2. **Production Deployment**
```bash
# Run pending migrations
python -m alembic upgrade head

# Verify migration status
python -m alembic current
python -m alembic history
```

3. **Rollback (if needed)**
```bash
# Rollback one migration
python -m alembic downgrade -1

# Rollback to specific revision
python -m alembic downgrade <revision_id>
```

4. **CI/CD Integration**
```yaml
# In .github/workflows/deploy.yml
- name: Run Database Migrations
  run: |
    cd backend
    python -m alembic upgrade head
```

**Note**: The `alert_annotations` table migration is already prepared as `5070e8da0ae6_add_alert_annotations.py` in `backend/alembic/versions/`.

1. **Database Tuning**
```sql
-- TimescaleDB
ALTER TABLE transactions SET (timescaledb.compress);
SELECT add_compression_policy('transactions', INTERVAL '7 days');

-- Neo4j (neo4j.conf)
dbms.memory.heap.initial_size=4G
dbms.memory.heap.max_size=8G
dbms.memory.pagecache.size=4G
```

2. **Caching**
- Redis TTL optimieren
- Browser Caching für Frontend Assets

3. **Horizontal Scaling**
- Multi-Worker Deployment mit Load Balancer
- Kafka Partitioning für parallele Verarbeitung

### Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)

# Neo4j
docker exec neo4j neo4j-admin dump --to=/backups/neo4j-$DATE.dump

# Postgres
docker exec postgres pg_dump -U postgres forensics > backups/postgres-$DATE.sql

# Upload to S3
aws s3 cp backups/ s3://your-bucket/backups/ --recursive
```

### Monitoring & Alerts

1. **Setup Prometheus Alerts**
```yaml
# monitoring/prometheus-alerts.yml - bereits konfiguriert
- alert: HighErrorRate
  expr: rate(http_requests_total{status="500"}[5m]) > 0.1
  for: 5m
  annotations:
    summary: "High error rate detected"
```

2. **Log Aggregation**
- ELK Stack oder Loki für zentrale Logs
- Structured Logging bereits implementiert

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Alle Tests passed (`pytest`, `npm test`)
- [ ] Environment Variables konfiguriert
- [ ] Datenbanken initialisiert
- [ ] SSL Zertifikate installiert
- [ ] Backup-Strategie definiert

### Deployment
- [ ] Code auf Server deployed
- [ ] Services gestartet (API + Workers)
- [ ] Health Checks erfolgreich
- [ ] Monitoring aktiv

### Post-Deployment
- [ ] OFAC Update läuft (`check /api/v1/admin/ofac-status`)
- [ ] Workers konsumieren Messages
- [ ] Frontend erreichbar
- [ ] End-to-End Test durchgeführt

---

## 📞 Support

**Dokumentation**: Siehe `README.md`, `DEVELOPMENT.md`, `GRAPH_ANALYTICS_COMPLETE.md`

**Logs**:
- Backend: `backend/logs/app.log`
- Workers: `backend/logs/workers.log`
- Nginx: `/var/log/nginx/`

**Health Status**: `http://localhost:8000/health`

---

**Version**: 1.0.0  
**Platform**: Blockchain Forensics Platform  
**Deployment Ready**: ✅ Production Grade
