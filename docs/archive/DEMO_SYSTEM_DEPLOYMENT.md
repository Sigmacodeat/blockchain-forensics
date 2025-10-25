# 🚀 Two-Tier Demo System - Deployment Instructions

## ✅ Pre-Deployment Checklist

**Status**: Alle Dateien erstellt und geprüft ✅

- [x] Backend-Service implementiert (`demo_service.py`)
- [x] API-Endpunkte erstellt (`demo.py`)
- [x] AI-Agent-Tools integriert (`tools.py`)
- [x] Frontend-Pages erstellt (Sandbox + Live)
- [x] Chatbot-Integration fertig (`ChatWidget.tsx`)
- [x] Routen registriert (`App.tsx`, `__init__.py`)
- [x] Migration SQL erstellt
- [x] CRON-Script erstellt (`demo_cleanup.py`)
- [x] Kubernetes CronJob Config erstellt
- [x] Test-Script erstellt
- [x] Dokumentation komplett

---

## 📋 Schritt-für-Schritt Deployment

### 1️⃣ Database Migration (Backend)

```bash
cd backend

# Option A: Direct SQL (wenn DB läuft)
psql $DATABASE_URL -f migrations/versions/007_add_demo_user_fields.sql

# Option B: Via Docker
docker-compose exec postgres psql -U postgres -d blockchain_forensics \
  -f /migrations/007_add_demo_user_fields.sql

# Option C: Via Alembic (wenn du Alembic nutzt)
alembic upgrade head
```

**Verify Migration:**
```bash
psql $DATABASE_URL -c "\d users" | grep demo
```

Sollte zeigen:
```
 is_demo              | boolean
 demo_type            | character varying(32)
 demo_expires_at      | timestamp without time zone
 demo_created_from_ip | character varying(64)
```

---

### 2️⃣ Backend-Service starten/neu starten

```bash
cd backend

# Development
uvicorn app.main:app --reload --port 8000

# Production (Docker)
docker-compose restart backend

# Production (Kubernetes)
kubectl rollout restart deployment/backend -n blockchain-forensics
```

**Verify Backend:**
```bash
curl http://localhost:8000/api/v1/demo/sandbox
```

Sollte JSON mit Mock-Daten zurückgeben.

---

### 3️⃣ CRON-Job einrichten

**Option A: System CRON (Linux/Mac)**

```bash
# Crontab öffnen
crontab -e

# Folgende Zeile hinzufügen (alle 5 Minuten):
*/5 * * * * cd /path/to/backend && /usr/bin/python3 scripts/demo_cleanup.py >> /var/log/demo_cleanup.log 2>&1
```

**Option B: Docker-Compose**

Füge zu `docker-compose.yml` hinzu:
```yaml
  demo-cleanup:
    build: ./backend
    command: >
      sh -c "while true; do 
        python scripts/demo_cleanup.py; 
        sleep 300; 
      done"
    depends_on:
      - postgres
      - redis
    env_file:
      - ./backend/.env
```

**Option C: Kubernetes CronJob**

```bash
kubectl apply -f infra/kubernetes/cronjobs/demo-cleanup.yaml
```

**Verify CRON:**
```bash
# System CRON
tail -f /var/log/demo_cleanup.log

# Kubernetes
kubectl logs -l component=demo-cleanup -n blockchain-forensics --tail=50
```

---

### 4️⃣ Frontend Build & Deploy

```bash
cd frontend

# Install dependencies (falls nicht geschehen)
npm install

# Development
npm run dev

# Production Build
npm run build

# Production Deploy (Vercel/Netlify/Docker)
# Vercel:
vercel --prod

# Oder Docker:
docker-compose restart frontend
```

**Verify Frontend:**

Öffne Browser:
- http://localhost:3000/en/demo/sandbox
- http://localhost:3000/en/demo/live

---

### 5️⃣ Environment Variables prüfen

**Backend (.env):**
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/blockchain_forensics
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key-here
OPENAI_API_KEY=sk-...  # Für AI-Agent
```

**Frontend (.env):**
```bash
VITE_API_URL=http://localhost:8000
VITE_CHAT_WS_URL=ws://localhost:8000/api/v1/ws/chat
```

---

### 6️⃣ Tests ausführen

```bash
# Test-Script ausführen
./scripts/test-demo-system.sh

# Oder manuell:

# 1. Backend API-Test
curl http://localhost:8000/api/v1/demo/sandbox

# 2. Live-Demo erstellen
curl -X POST http://localhost:8000/api/v1/demo/live \
  -H "Content-Type: application/json"

# 3. Frontend testen
open http://localhost:3000/en/demo/sandbox
open http://localhost:3000/en/demo/live
```

---

## 🔧 Post-Deployment Monitoring

### Metrics zu überwachen:

**1. Demo-Creation-Rate:**
```sql
SELECT 
  DATE(created_at) as date,
  COUNT(*) FILTER (WHERE demo_type = 'live') as live_demos
FROM users
WHERE is_demo = true 
  AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**2. Conversion-Rate:**
```sql
WITH demos AS (
  SELECT DATE(created_at) as date, COUNT(*) as demo_count
  FROM users WHERE is_demo = true AND demo_type = 'live'
  AND created_at >= NOW() - INTERVAL '30 days'
  GROUP BY DATE(created_at)
),
signups AS (
  SELECT DATE(created_at) as date, COUNT(*) as signup_count
  FROM users WHERE is_demo = false
  AND created_at >= NOW() - INTERVAL '30 days'
  GROUP BY DATE(created_at)
)
SELECT 
  d.date,
  d.demo_count,
  COALESCE(s.signup_count, 0) as signups,
  ROUND(100.0 * s.signup_count / d.demo_count, 2) as conversion_rate
FROM demos d
LEFT JOIN signups s ON d.date = s.date
ORDER BY d.date DESC;
```

**3. Cleanup-Erfolg:**
```sql
SELECT COUNT(*) as active_expired_demos
FROM users
WHERE is_demo = true 
  AND demo_expires_at < NOW();
```

Sollte immer 0 oder nahe 0 sein.

**4. Rate-Limit Monitoring:**
```sql
SELECT 
  demo_created_from_ip,
  COUNT(*) as demo_count,
  MAX(created_at) as last_demo
FROM users
WHERE is_demo = true 
  AND demo_type = 'live'
  AND created_at >= NOW() - INTERVAL '1 day'
GROUP BY demo_created_from_ip
HAVING COUNT(*) >= 3
ORDER BY demo_count DESC;
```

---

## 🐛 Troubleshooting

### Problem: "Rate limit exceeded"

**Ursache**: IP hat 3 Demos in 24h erstellt

**Lösung**:
```sql
-- Check IP's demo history
SELECT * FROM users 
WHERE demo_created_from_ip = 'IP_ADDRESS' 
  AND created_at >= NOW() - INTERVAL '1 day';

-- Reset manually (only if legitimate)
DELETE FROM users 
WHERE demo_created_from_ip = 'IP_ADDRESS' 
  AND is_demo = true;
```

### Problem: Demo-User wird nicht gelöscht

**Ursache**: CRON läuft nicht oder DB-Connection fehlt

**Lösung**:
```bash
# Manual cleanup
python backend/scripts/demo_cleanup.py

# Check CRON logs
tail -f /var/log/demo_cleanup.log

# Kubernetes
kubectl logs -l component=demo-cleanup --tail=100
```

### Problem: Chatbot zeigt keine Demo-Buttons

**Ursache**: AI-Tools nicht registriert oder Marker fehlen

**Lösung**:
```bash
# Check tools registration
grep -A 5 "offer_sandbox_demo_tool\|offer_live_demo_tool" backend/app/ai_agents/tools.py

# Check in FORENSIC_TOOLS list
grep -B 5 -A 5 "FORENSIC_TOOLS = \[" backend/app/ai_agents/tools.py | grep demo
```

### Problem: Frontend-Routes 404

**Ursache**: Routes nicht registriert oder Build fehlt

**Lösung**:
```bash
# Check App.tsx
grep -A 2 "demo/sandbox\|demo/live" frontend/src/App.tsx

# Rebuild Frontend
cd frontend && npm run build
```

---

## 📊 Success Metrics (Nach 30 Tagen)

Erwartete Werte:

| Metric | Target | Formula |
|--------|--------|---------|
| **Demo-Requests** | 500-800/Monat | Sandbox + Live Views |
| **Sandbox → Live Rate** | 30%+ | Live-Demos / Sandbox-Views |
| **Demo → Signup Rate** | 50%+ | Signups / Live-Demos |
| **Mobile-Usage** | 40%+ | Mobile-Demos / Total-Demos |
| **Avg Demo Duration** | 15+ Min | AVG(demo_session_length) |
| **Rate-Limit Hit-Rate** | <5% | Rate-Limit-Errors / Total-Requests |

---

## 🚀 Launch Checklist

- [ ] ✅ Database-Migration erfolgreich
- [ ] ✅ Backend-Service läuft und antwortet
- [ ] ✅ CRON-Job für Cleanup aktiv (alle 5 Min)
- [ ] ✅ Frontend-Build deployed
- [ ] ✅ Routes erreichbar (/demo/sandbox, /demo/live)
- [ ] ✅ Chatbot zeigt Demo-Buttons
- [ ] ✅ Test-Demo erfolgreich erstellt
- [ ] ✅ Auto-Login funktioniert
- [ ] ✅ 30-Min-Timer läuft
- [ ] ✅ Rate-Limit greift nach 3 Versuchen
- [ ] ✅ Cleanup löscht expired Demos
- [ ] ✅ Monitoring/Logs aktiv
- [ ] ✅ Analytics-Events feuern

---

## 📞 Support

**Dokumentation**: 
- `/TWO_TIER_DEMO_SYSTEM_COMPLETE.md` - Vollständige Feature-Docs
- `/DEMO_SYSTEM_DEPLOYMENT.md` - Diese Datei

**Logs**:
- Backend: `docker-compose logs -f backend`
- Frontend: Browser DevTools Console
- CRON: `/var/log/demo_cleanup.log`
- Kubernetes: `kubectl logs -l app=blockchain-forensics -n blockchain-forensics`

**Health-Checks**:
```bash
# Backend Health
curl http://localhost:8000/health

# Demo System Health
curl http://localhost:8000/api/v1/demo/sandbox | jq .type

# Database Connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users WHERE is_demo = true;"
```

---

## 🎉 Status

**Implementation**: ✅ 100% Complete
**Testing**: ✅ Ready
**Deployment**: 🟡 Pending Manual Steps (Migration + CRON)
**Production-Ready**: ✅ YES

---

**Nach Deployment dieser Schritte ist das System LIVE!** 🚀
