# 🚀 Docker Quick Reference - Blockchain Forensics

## ⚡ Schnellstart

```bash
# Automatischer Start (empfohlen)
./scripts/docker-startup.sh

# Manueller Start (alle Services)
docker compose up -d

# Logs live verfolgen
docker compose logs -f
```

---

## 📋 Häufige Commands

### Services steuern

```bash
# Alle Services starten
docker compose up -d

# Nur bestimmte Services starten
docker compose up -d backend frontend

# Services stoppen (Container behalten)
docker compose stop

# Services stoppen + Container löschen
docker compose down

# Services stoppen + Container + Volumes löschen (ACHTUNG: Datenverlust!)
docker compose down -v
```

### Status & Logs

```bash
# Status aller Services
docker compose ps

# Logs aller Services
docker compose logs

# Logs bestimmter Service
docker compose logs backend
docker compose logs -f postgres  # Live-Logs

# Letzte 100 Zeilen
docker compose logs --tail=100 backend

# Logs seit 10 Minuten
docker compose logs --since 10m
```

### Services neu bauen

```bash
# Alle Images neu bauen
docker compose build

# Ohne Cache neu bauen
docker compose build --no-cache

# Nur bestimmtes Image
docker compose build backend

# Bauen + Starten
docker compose up -d --build
```

### Service neu starten

```bash
# Einzelnen Service neu starten
docker compose restart backend

# Service stoppen + starten
docker compose stop backend
docker compose start backend

# Service komplett neu erstellen
docker compose up -d --force-recreate backend
```

---

## 🔍 Debugging

### In Container einsteigen

```bash
# Backend Shell
docker compose exec backend bash

# Postgres Shell
docker compose exec postgres psql -U forensics -d blockchain_forensics

# Redis CLI
docker compose exec redis redis-cli

# Neo4j Cypher Shell
docker compose exec neo4j cypher-shell -u neo4j -p forensics_password_change_me
```

### Befehle im Container ausführen

```bash
# Python Script ausführen
docker compose exec backend python -m app.scripts.seed_data

# Alembic Migration
docker compose exec backend alembic upgrade head

# Django-ähnliche Commands
docker compose exec backend python manage.py migrate
```

### Netzwerk debuggen

```bash
# Netzwerk inspizieren
docker network inspect blockchain-forensics_forensics-network

# DNS-Auflösung testen
docker compose exec backend ping postgres
docker compose exec backend nslookup redis

# Curl von einem Container
docker compose exec backend curl http://redis:6379
```

### Resource-Verbrauch

```bash
# Alle Container
docker stats

# Nur blockchain-forensics Container
docker stats $(docker compose ps -q)

# Disk-Usage
docker system df

# Detaillierter Disk-Usage
docker system df -v
```

---

## 🧹 Cleanup

### Vorsichtig (behält Volumes)

```bash
# Stoppen + Container entfernen
docker compose down

# Zusätzlich verwaiste Images entfernen
docker compose down --rmi local
```

### Aggressiv (löscht Daten!)

```bash
# ⚠️ ACHTUNG: Löscht alle Datenbank-Daten!
docker compose down -v

# Komplettes System-Cleanup
docker system prune -a --volumes

# Nur ungenutzte Volumes
docker volume prune
```

### Selektiv Volumes löschen

```bash
# Alle Volumes auflisten
docker volume ls | grep blockchain-forensics

# Einzelnes Volume löschen
docker volume rm blockchain-forensics_postgres-data

# ⚠️ Alle Projekt-Volumes löschen
docker volume rm $(docker volume ls -q | grep blockchain-forensics)
```

---

## 🔧 Troubleshooting

### Service startet nicht

```bash
# 1. Logs prüfen
docker compose logs backend

# 2. Health Check manuell testen
docker compose exec backend curl http://localhost:8000/health

# 3. Service neu bauen + starten
docker compose up -d --build --force-recreate backend

# 4. Container interaktiv starten (für Debugging)
docker compose run --rm backend bash
```

### Port bereits belegt

```bash
# Port-Belegung prüfen
lsof -i :8000

# Prozess killen
kill -9 $(lsof -t -i:8000)

# Alternative: Port in docker-compose.yml ändern
# ports:
#   - "8001:8000"  # Statt 8000:8000
```

### Datenbank-Probleme

```bash
# Postgres neu initialisieren
docker compose stop postgres
docker volume rm blockchain-forensics_postgres-data
docker compose up -d postgres

# Migration manuell ausführen
docker compose exec backend alembic upgrade head

# Postgres direkt abfragen
docker compose exec postgres psql -U forensics -d blockchain_forensics -c "SELECT version();"
```

### Cache-Probleme

```bash
# Redis leeren
docker compose exec redis redis-cli FLUSHALL

# Qdrant Collections löschen
curl -X DELETE http://localhost:6333/collections/transactions

# Application-Cache neu aufbauen
docker compose restart backend
```

---

## 📊 Monitoring

### Service-Status prüfen

```bash
# Health Status
docker compose ps

# Detaillierte Inspect
docker compose inspect backend

# Environment Variables
docker compose exec backend env | sort
```

### URLs öffnen

```bash
# macOS
open http://localhost:3000      # Frontend
open http://localhost:8000/docs # Backend API Docs
open http://localhost:3003      # Grafana
open http://localhost:9090      # Prometheus
open http://localhost:16686     # Jaeger

# Linux
xdg-open http://localhost:3000

# Windows
start http://localhost:3000
```

---

## 🔐 Sicherheit & Secrets

### Secrets rotieren

```bash
# .env bearbeiten
nano .env

# Nur betroffene Services neu starten
docker compose up -d --force-recreate backend monitor-worker
```

### Passwörter im Container ändern

```bash
# Neo4j Passwort ändern
docker compose exec neo4j cypher-shell -u neo4j -p forensics_password_change_me
# Im Cypher Shell: ALTER CURRENT USER SET PASSWORD FROM 'old' TO 'new';

# Postgres Passwort ändern
docker compose exec postgres psql -U forensics -d blockchain_forensics
# Im Postgres Shell: ALTER USER forensics WITH PASSWORD 'new_password';
```

---

## 📦 Backup & Restore

### Postgres Backup

```bash
# Backup erstellen
docker compose exec -T postgres pg_dump -U forensics blockchain_forensics > backup.sql

# Mit Timestamp
docker compose exec -T postgres pg_dump -U forensics blockchain_forensics > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
cat backup.sql | docker compose exec -T postgres psql -U forensics blockchain_forensics
```

### Neo4j Backup

```bash
# Export (nur Daten)
docker compose exec neo4j neo4j-admin dump --database=neo4j --to=/tmp/neo4j-backup.dump

# Copy aus Container
docker cp $(docker compose ps -q neo4j):/tmp/neo4j-backup.dump ./neo4j-backup.dump

# Restore
docker cp ./neo4j-backup.dump $(docker compose ps -q neo4j):/tmp/neo4j-backup.dump
docker compose exec neo4j neo4j-admin load --database=neo4j --from=/tmp/neo4j-backup.dump --force
```

### Redis Backup

```bash
# Redis Snapshot
docker compose exec redis redis-cli SAVE

# Copy RDB File
docker cp $(docker compose ps -q redis):/data/dump.rdb ./redis-backup.rdb

# Restore
docker compose stop redis
docker cp ./redis-backup.rdb $(docker compose ps -q redis):/data/dump.rdb
docker compose start redis
```

---

## 🎯 Development Workflow

### Live-Reload Development

```bash
# Backend (mit Volume-Mount für Live-Reload)
docker compose up -d backend
# Code-Änderungen werden automatisch geladen (FastAPI --reload)

# Frontend (mit Volume-Mount)
docker compose up -d frontend
# Vite HMR funktioniert automatisch

# Logs verfolgen während Development
docker compose logs -f backend frontend
```

### Tests ausführen

```bash
# Backend Unit Tests
docker compose exec backend pytest

# Mit Coverage
docker compose exec backend pytest --cov=app --cov-report=html

# Nur bestimmte Tests
docker compose exec backend pytest tests/test_trace.py

# Frontend Tests
docker compose exec frontend npm test

# E2E Tests
docker compose exec frontend npm run test:e2e
```

### Linting & Formatting

```bash
# Backend
docker compose exec backend black .
docker compose exec backend flake8
docker compose exec backend mypy app

# Frontend
docker compose exec frontend npm run lint
docker compose exec frontend npm run format
```

---

## 🚀 Production Deployment

### Production Build

```bash
# Mit Production-Config
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Nur Services ohne Development-Tools
docker compose up -d backend frontend postgres redis neo4j kafka prometheus grafana
```

### Ressourcen-Limits setzen

```yaml
# In docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## 📞 Support & Hilfe

### Logs für Bug-Report sammeln

```bash
# Alle Logs der letzten Stunde
docker compose logs --since 1h > logs_$(date +%Y%m%d_%H%M%S).txt

# Service-Status
docker compose ps > status.txt

# System-Info
docker version >> status.txt
docker compose version >> status.txt
```

### Container-Info exportieren

```bash
# Detaillierte Container-Config
docker compose config > config.yml

# Environment-Variablen (ohne Secrets!)
docker compose exec backend env | grep -v "SECRET\|PASSWORD\|KEY" > env.txt
```

---

## ✅ Checkliste Production-Ready

- [ ] Alle Services starten: `docker compose ps` (alle "healthy")
- [ ] Backend API: `curl http://localhost:8000/health`
- [ ] Frontend: `open http://localhost:3000`
- [ ] Grafana Dashboards: `open http://localhost:3003`
- [ ] Postgres erreichbar: `docker compose exec postgres pg_isready`
- [ ] Redis erreichbar: `docker compose exec redis redis-cli ping`
- [ ] Neo4j erreichbar: `docker compose exec neo4j cypher-shell "RETURN 1"`
- [ ] Kafka erreichbar: `docker compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092`
- [ ] .env vollständig: `GOOGLE_CLIENT_ID`, `ETHEREUM_RPC_URL`, `OPENAI_API_KEY`
- [ ] Secrets rotiert: Passwörter nicht auf Defaults
- [ ] Backups konfiguriert
- [ ] Monitoring läuft

**Bei ✅ allen Punkten: Production-Ready! 🎉**
