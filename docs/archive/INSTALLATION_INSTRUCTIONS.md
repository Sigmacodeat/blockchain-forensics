# 🚀 INSTALLATION & DEPLOYMENT ANWEISUNGEN

**Version**: 3.0.0 Premium  
**Datum**: 19. Oktober 2025  
**Status**: Production Ready

---

## 📦 FRONTEND DEPENDENCIES INSTALLIEREN

### **Chart.js für Advanced Analytics Dashboard:**

```bash
cd frontend

# Install Chart.js dependencies
npm install chart.js react-chartjs-2

# Or with yarn
yarn add chart.js react-chartjs-2
```

**Packages:**
- `chart.js@^4.4.0` - Chart Library
- `react-chartjs-2@^5.2.0` - React Wrapper für Chart.js

---

## 🔧 BACKEND SETUP

### **1. Environment Variables:**

Erstelle `.env` Datei im Backend-Ordner:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/blockchain_forensics
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256

# Feature Flags (Redis)
REDIS_FEATURE_FLAGS_PREFIX=feature_flag:

# Analytics
POSTHOG_API_KEY=optional
POSTHOG_HOST=https://app.posthog.com

# Email (Optional für Notifications)
EMAIL_ENABLED=true
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Crypto Payments (Optional)
NOWPAYMENTS_API_KEY=optional
NOWPAYMENTS_IPN_SECRET=optional

# Admin
ADMIN_EMAIL=admin@yourdomain.com
```

### **2. Python Dependencies:**

```bash
cd backend

# Install all dependencies
pip install -r requirements.txt

# Key packages for new features:
# - Redis (für Feature-Flags)
# - psycopg2-binary (für Advanced Analytics)
```

### **3. Database Migrations:**

```bash
# Run Alembic migrations
alembic upgrade head

# Create admin user
python scripts/create_admin.py
```

---

## 🎨 FRONTEND SETUP

### **1. Environment Variables:**

Erstelle `.env` im Frontend-Ordner:

```bash
VITE_API_URL=http://localhost:8000
VITE_ENABLE_ANALYTICS=true
VITE_POSTHOG_KEY=optional
```

### **2. Dependencies installieren:**

```bash
cd frontend

# Install all dependencies
npm install

# Or with yarn
yarn install
```

### **3. Build für Production:**

```bash
# Development
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

---

## 🚀 DEPLOYMENT

### **Option 1: Docker (Empfohlen)**

```bash
# Build und starte alle Services
docker-compose up -d

# Logs ansehen
docker-compose logs -f

# Stoppen
docker-compose down
```

### **Option 2: Manual Deployment**

**Backend:**
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Frontend:**
```bash
cd frontend
npm run build
# Serve dist/ mit Nginx oder Vercel
```

---

## ✅ HEALTH CHECKS

### **Backend Health:**
```bash
curl http://localhost:8000/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "services": {
    "postgresql": "healthy",
    "redis": "healthy",
    "neo4j": "healthy"
  }
}
```

### **Feature-Flags Health:**
```bash
curl http://localhost:8000/api/v1/feature-flags/ \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### **Analytics Health:**
```bash
curl http://localhost:8000/api/v1/analytics/premium/summary?days=30 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 🔐 SECURITY CHECKLIST

**Vor Production-Deployment:**

- [ ] `SECRET_KEY` geändert (min. 32 Zeichen)
- [ ] `DEBUG=False` in Backend
- [ ] HTTPS aktiviert
- [ ] CORS korrekt konfiguriert
- [ ] Rate-Limiting aktiv
- [ ] Firewall-Regeln gesetzt
- [ ] Backup-Strategy implementiert
- [ ] SSL-Zertifikate installiert
- [ ] Environment-Variables aus Code entfernt
- [ ] Admin-Credentials geändert

---

## 📊 MONITORING SETUP

### **1. Prometheus (Optional):**

```yaml
# docker-compose.yml erweitern:
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
```

### **2. Grafana (Optional):**

```yaml
grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

### **3. Logs:**

```bash
# Backend logs
tail -f backend/logs/app.log

# Feature-Flags logs
tail -f backend/logs/feature_flags.log

# Analytics logs
tail -f backend/logs/analytics.log
```

---

## 🎯 ERSTE SCHRITTE NACH INSTALLATION

### **1. Admin-Login:**
```
URL: http://localhost:3000/en/login
Email: admin@yourdomain.com
Password: [aus create_admin.py]
```

### **2. Feature-Flags erstellen:**
```
URL: http://localhost:3000/en/admin/feature-flags

Beispiel-Flag:
- Key: new_dashboard_ui
- Name: New Dashboard UI
- Description: Enable redesigned dashboard
- Status: disabled
```

### **3. Ersten Test durchführen:**
```
URL: http://localhost:3000/en/dashboard

1. Dashboard öffnen
2. AI-Chat öffnen
3. Trace durchführen: "Trace 0x123..."
4. Analytics ansehen: /admin/analytics-premium
```

---

## 🐛 TROUBLESHOOTING

### **Problem: Chart.js nicht gefunden**
```bash
cd frontend
npm install chart.js react-chartjs-2
npm run dev
```

### **Problem: Redis Connection Failed**
```bash
# Redis starten
docker run -d -p 6379:6379 redis:latest

# Oder mit Docker Compose
docker-compose up redis
```

### **Problem: Feature-Flags API 401**
```bash
# Admin-Token generieren
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@yourdomain.com","password":"admin123"}'

# Token in Request verwenden
curl http://localhost:8000/api/v1/feature-flags/ \
  -H "Authorization: Bearer $TOKEN"
```

### **Problem: Analytics Queries langsam**
```bash
# PostgreSQL Indices prüfen
psql -d blockchain_forensics -c "\d web_events"

# Fehlende Indices erstellen
psql -d blockchain_forensics -f backend/sql/analytics_indices.sql
```

---

## 📚 WEITERE DOKUMENTATION

- **API Docs**: http://localhost:8000/docs
- **Feature-Flags Guide**: PREMIUM_FEATURES_COMPLETE.md
- **Marketing Guide**: MARKETING_MATERIAL_COMPLETE.md
- **Social Media Kit**: SOCIAL_MEDIA_LAUNCH_KIT.md
- **SaaS Audit**: SAAS_FUNKTIONALITAET_100_PROZENT_AUDIT.md

---

## 🎉 LAUNCH CHECKLIST

**Vor öffentlichem Launch:**

- [ ] Installation getestet (frische VM)
- [ ] Alle Health-Checks grün
- [ ] Feature-Flags funktionieren
- [ ] Analytics Dashboard lädt
- [ ] Charts werden angezeigt
- [ ] Admin-UI funktioniert
- [ ] Security Audit durchgeführt
- [ ] Load-Testing durchgeführt
- [ ] Backup-Strategy implementiert
- [ ] Monitoring aktiv
- [ ] Error-Tracking (Sentry) aktiv
- [ ] SSL-Zertifikate installiert
- [ ] DNS konfiguriert
- [ ] CDN konfiguriert (optional)
- [ ] Marketing-Material bereit
- [ ] Product Hunt vorbereitet

---

## 🚀 PERFORMANCE OPTIMIERUNG

### **Frontend:**
```bash
# Build-Size analysieren
npm run build -- --analyze

# Lighthouse Score prüfen
npm install -g lighthouse
lighthouse http://localhost:3000 --view
```

### **Backend:**
```bash
# Load-Testing mit Locust
pip install locust
locust -f backend/tests/load_test.py
```

### **Database:**
```sql
-- Query Performance analysieren
EXPLAIN ANALYZE SELECT * FROM web_events WHERE ts >= NOW() - INTERVAL '30 days';

-- Vacuum & Analyze
VACUUM ANALYZE web_events;
```

---

## 📞 SUPPORT

**Bei Problemen:**
1. GitHub Issues: [Link]
2. Discord Community: [Link]
3. Email Support: support@yourdomain.com
4. Dokumentation: [Link]

---

**STATUS**: ✅ READY TO DEPLOY
**LETZTER CHECK**: 19. Oktober 2025
**VERSION**: 3.0.0 Premium
