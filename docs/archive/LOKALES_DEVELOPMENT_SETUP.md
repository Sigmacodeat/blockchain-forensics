# 🚀 Lokales Development Setup - Frontend & Backend

**Status:** ✅ Frontend und Backend aus Docker entfernt für bessere Entwicklung

## 📋 Übersicht

### ✅ Docker-Services (laufen weiterhin)
- **Datenbanken:** PostgreSQL (5435), Redis (6381), Neo4j (7475, 7688)
- **Message Broker:** Kafka (9092, 9093), Zookeeper (2181), Schema Registry (8081)
- **AI/ML:** Qdrant (6333), ML Service
- **Monitoring:** Prometheus (9090), Grafana (3003), Jaeger (16686, 14250)

### 🆕 Lokale Services (starten separat)
- **Backend:** uvicorn auf Port 8000
- **Frontend:** Vite auf Port 3000

---

## 🔧 Backend starten (uvicorn)

### Schritt 1: Backend-Verzeichnis
```bash
cd /Users/msc/CascadeProjects/blockchain-forensics/backend
```

### Schritt 2: Virtuelle Umgebung aktivieren
```bash
# Falls nicht vorhanden, erstellen:
python -m venv venv
source venv/bin/activate  # Mac/Linux
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt
```

### Schritt 3: Backend starten
```bash
# Mit Hot-Reload für Entwicklung
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
```

**Features:**
- ✅ **Hot-Reload:** Änderungen werden automatisch geladen
- ✅ **Debug-Logs:** `--log-level info` für detaillierte Logs
- ✅ **Alle Ports:** `0.0.0.0` bindet an alle Interfaces

---

## 🎨 Frontend starten (Vite)

### Schritt 1: Frontend-Verzeichnis
```bash
cd /Users/msc/CascadeProjects/blockchain-forensics/frontend
```

### Schritt 2: Dependencies installieren
```bash
npm install
```

### Schritt 3: Frontend starten
```bash
npm run dev -- --host 0.0.0.0 --port 3000
```

**Features:**
- ✅ **Hot Module Replacement (HMR):** Sofortige UI-Updates
- ✅ **Fast Refresh:** React-Komponenten werden instant neu geladen
- ✅ **Source Maps:** Bessere Debugging-Erfahrung

---

## 🌐 URLs nach Start

| Service | URL | Status |
|---------|-----|--------|
| **Frontend** | http://localhost:3000 | Lokales Vite |
| **Backend API** | http://localhost:8000 | Lokales uvicorn |
| **Grafana** | http://localhost:3003 | Docker |
| **Prometheus** | http://localhost:9090 | Docker |
| **Jaeger** | http://localhost:16686 | Docker |
| **Neo4j Browser** | http://localhost:7475 | Docker |

---

## 🔍 Debugging & Logs

### Backend-Logs sehen
```bash
# Terminal wo uvicorn läuft zeigt die Logs automatisch
# Oder in separatem Terminal:
cd backend && tail -f logs/app.log  # Falls Logging konfiguriert
```

### Frontend-Logs sehen
```bash
# Terminal wo Vite läuft zeigt die Logs automatisch
# Browser Console für Runtime-Fehler
```

### Docker-Logs prüfen
```bash
# Alle Docker-Services
docker compose logs -f

# Nur Datenbanken
docker compose logs -f postgres redis neo4j kafka

# Einzelner Service
docker compose logs -f prometheus
```

---

## 🔄 Hot-Reload testen

### Backend ändern:
1. **Datei ändern:** `backend/app/api/v1/trace.py`
2. **Speichern** → uvicorn lädt automatisch neu
3. **Test:** `curl http://localhost:8000/health`

### Frontend ändern:
1. **Datei ändern:** `frontend/src/components/TracePage.tsx`
2. **Speichern** → Vite lädt automatisch neu (HMR)
3. **Browser:** Seite lädt automatisch neu

---

## 🚨 Häufige Probleme & Lösungen

### Backend startet nicht:
```bash
# 1. Dependencies prüfen
pip list | grep fastapi

# 2. Port prüfen
lsof -i :8000  # Falls belegt: kill -9 <PID>

# 3. Logs zeigen Fehler
# Terminal wo uvicorn läuft zeigt alle Fehler
```

### Frontend startet nicht:
```bash
# 1. Node-Version prüfen
node --version  # Mindestens 18+

# 2. Dependencies prüfen
npm ls vite

# 3. Port prüfen
lsof -i :3000  # Falls belegt: kill -9 <PID>
```

### Docker-Services nicht erreichbar:
```bash
# 1. Status prüfen
docker compose ps

# 2. Logs prüfen
docker compose logs postgres

# 3. Container neu starten
docker compose restart postgres redis neo4j
```

---

## 🎯 Produktions-Setup

Für **Production** kannst du Frontend und Backend wieder in Docker bringen:

```bash
# docker-compose.yml editieren und Kommentare entfernen:
# - # backend: (entkommentieren)
# - # frontend: (entkommentieren)

# Dann:
docker compose up -d backend frontend
```

---

## 📊 Aktuelle Architektur

```
┌─────────────────────────────────────────────────────────┐
│                 forensics-network (Docker)               │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │Postgres │  │  Redis  │  │  Neo4j  │  │ Qdrant  │     │
│  │ (5435)  │  │ (6381)  │  │ (7475)  │  │ (6333)  │     │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
│         │          │          │          │              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │  Kafka  │  │Prometheus│  │ Grafana │  │ Jaeger  │     │
│  │ (9092)  │  │ (9090)  │  │ (3003)  │  │(16686)  │     │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
└─────────────────────────────────────────────────────────┘
         │          │          │          │
         ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────┐
│                 Lokale Entwicklung                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐               ┌─────────┐                  │
│  │ uvicorn │  ──────────►  │  Vite   │                  │
│  │ (8000)  │   Backend     │ (3000)  │   Frontend       │
│  └─────────┘               └─────────┘                  │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Status: PERFECT DEVELOPMENT SETUP

- ✅ **Docker:** Alle Services laufen stabil
- ✅ **Backend:** Lokales uvicorn mit Hot-Reload
- ✅ **Frontend:** Lokales Vite mit HMR
- ✅ **Monitoring:** Vollständig funktionsfähig
- ✅ **Entwicklung:** Maximale Produktivität

**Jetzt kannst du Code ändern und siehst sofort die Änderungen! 🚀**
