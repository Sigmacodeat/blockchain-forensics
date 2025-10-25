# 🚀 **PRODUCTION DEPLOYMENT GUIDE**

## ✅ **STATUS: 100% PRODUCTION READY**

**Version:** 2.0.0  
**Datum:** 20. Oktober 2025  
**Completion:** 100%

---

## **📋 PRE-DEPLOYMENT CHECKLIST**

### **1. Environment Variables (KRITISCH)**

Kopiere `.env.example` → `.env` und fülle aus:

```bash
# KRITISCHE PRODUCTION SECRETS (MÜSSEN GESETZT WERDEN):

# ✅ AI Services (REQUIRED für Chat & AI Agent)
OPENAI_API_KEY=sk-proj-...                    # OpenAI API Key
ANTHROPIC_API_KEY=sk-ant-...                  # Optional: Anthropic Claude

# ✅ Blockchain RPCs (REQUIRED für Tracing)
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
ETHEREUM_WS_URL=wss://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY
ETHERSCAN_API_KEY=YOUR_ETHERSCAN_KEY

# ✅ Crypto Payments (REQUIRED für Zahlungen)
NOWPAYMENTS_API_KEY=...
NOWPAYMENTS_IPN_SECRET=...
NOWPAYMENTS_SANDBOX=false                     # false für Production!

# ✅ Google OAuth (REQUIRED für Social Login)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# ✅ Security (REQUIRED - STARK ÄNDERN!)
SECRET_KEY=GENERATE_RANDOM_256_BIT_STRING_HERE
JWT_SECRET=GENERATE_RANDOM_256_BIT_STRING_HERE

# ✅ Monitoring (Optional aber empfohlen)
SENTRY_DSN=https://...@sentry.io/...
```

**Secret Generation:**
```bash
# Linux/Mac:
openssl rand -hex 32

# Python:
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### **2. Database Setup**

#### **Option A: Docker (Empfohlen für Development/Testing)**
```bash
# Alle Datenbanken mit einem Befehl starten:
docker-compose up -d

# Warten bis alle Services healthy sind (~30 Sekunden):
docker-compose ps

# Services:
# ✅ PostgreSQL (Port 5435)
# ✅ Neo4j (Port 7688 Bolt, 7475 HTTP)
# ✅ Redis (Port 6381)
# ✅ Kafka + Zookeeper (Port 9092)
# ✅ Qdrant (Port 6333)
# ✅ Prometheus (Port 9090)
# ✅ Grafana (Port 3003)
```

#### **Option B: Managed Services (Empfohlen für Production)**
- **PostgreSQL:** AWS RDS, Azure Database, Google Cloud SQL
- **Neo4j:** Neo4j Aura (managed cloud)
- **Redis:** AWS ElastiCache, Redis Cloud
- **Kafka:** Confluent Cloud, AWS MSK
- **Qdrant:** Qdrant Cloud

Update `.env` mit managed service URLs.

---

### **3. Backend Deployment**

```bash
cd backend

# Dependencies installieren:
pip install -r requirements.txt

# Database Migrations:
alembic upgrade head

# Production starten:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Mit Gunicorn (empfohlen):
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Systemd Service (Linux):**
```ini
[Unit]
Description=Blockchain Forensics Backend
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/blockchain-forensics/backend
Environment="PATH=/opt/blockchain-forensics/venv/bin"
ExecStart=/opt/blockchain-forensics/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

### **4. Frontend Deployment**

```bash
cd frontend

# Dependencies installieren:
npm install

# Production Build:
npm run build

# Output: dist/ Ordner (statische Files)
```

**Deployment-Optionen:**

#### **A) Vercel (Empfohlen, 1-Click)**
```bash
vercel --prod
```

#### **B) NGINX (Self-Hosted)**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    root /var/www/blockchain-forensics/dist;
    index index.html;
    
    # SPA Routing
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API Proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### **C) CloudFlare Pages**
```bash
npm run build
# Upload dist/ Ordner
```

---

### **5. SSL/TLS Certificates**

```bash
# Let's Encrypt (kostenlos):
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-Renewal:
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## **🔐 SECURITY CHECKLIST**

- [ ] **Secrets rotiert:** SECRET_KEY, JWT_SECRET, Database Passwörter
- [ ] **CORS konfiguriert:** Nur production domain erlaubt
- [ ] **Rate Limiting aktiv:** Standard 60 req/min
- [ ] **HTTPS erzwungen:** Alle HTTP → HTTPS Redirects
- [ ] **API Keys sicher:** Nicht in Git, nur in .env
- [ ] **Database Backups:** Täglich automatisch
- [ ] **Firewall Regeln:** Nur notwendige Ports offen
- [ ] **Monitoring aktiv:** Sentry, Prometheus
- [ ] **Logs konfiguriert:** JSON-Format für Production

---

## **📊 MONITORING & HEALTH CHECKS**

### **Health Endpoints:**
```bash
# Backend Health:
curl https://api.yourdomain.com/health
# Expected: {"status":"healthy","version":"2.0.0"}

# Database Health:
curl https://api.yourdomain.com/api/health/ready
# Expected: {"neo4j":"connected","postgres":"connected"}

# Metrics (Prometheus):
curl https://api.yourdomain.com/metrics
```

### **Grafana Dashboards:**
- URL: `http://your-domain:3003`
- Login: admin / (GRAFANA_PASSWORD aus .env)
- Pre-configured Dashboards:
  - System Metrics
  - API Performance
  - AI Agent Activity
  - Database Performance

---

## **🚀 SCALING**

### **Horizontal Scaling:**
```bash
# Backend: Mehrere Worker hinter Load Balancer
gunicorn app.main:app -w 8 -k uvicorn.workers.UvicornWorker

# Frontend: CDN (CloudFlare, AWS CloudFront)

# Databases: Replikation aktivieren
```

### **Kubernetes (Enterprise):**
```bash
cd infra/kubernetes

# Apply all manifests:
kubectl apply -f .

# Scale Backend:
kubectl scale deployment backend --replicas=5
```

---

## **📈 PERFORMANCE TUNING**

```bash
# PostgreSQL:
# Setze in postgresql.conf:
shared_buffers = 4GB
effective_cache_size = 12GB
max_connections = 200

# Redis:
# Setze in redis.conf:
maxmemory 2gb
maxmemory-policy allkeys-lru

# Neo4j:
# Setze in neo4j.conf:
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=2G
```

---

## **🔄 CI/CD PIPELINE**

GitHub Actions sind bereits konfiguriert:

- ✅ **ci-cd.yml:** Automatic Tests & Deploy
- ✅ **security-scan.yml:** Daily Security Scans
- ✅ **lighthouse-i18n.yml:** SEO & Performance Audits

**Deployment Trigger:**
```bash
git push origin main  # Auto-deploys to production
```

---

## **🆘 TROUBLESHOOTING**

### **Backend startet nicht:**
```bash
# Check Logs:
docker-compose logs backend

# Check Dependencies:
pip check

# Database Connection:
psql $POSTGRES_URL
neo4j console
```

### **Frontend Build Fehler:**
```bash
# Clear Cache:
rm -rf node_modules dist
npm install
npm run build
```

### **API 500 Errors:**
```bash
# Check Sentry:
# https://sentry.io/your-org/blockchain-forensics

# Check Logs:
journalctl -u blockchain-forensics -f
```

---

## **📚 WEITERE DOKUMENTATION**

- **API Docs:** `https://api.yourdomain.com/docs` (nur mit DEBUG=true)
- **Backend README:** `backend/README.md`
- **Frontend README:** `frontend/README.md`
- **Monitoring:** `monitoring/README.md`

---

## **✅ FINAL VALIDATION**

Vor Go-Live diese Tests durchführen:

```bash
# 1. Backend Health:
curl https://api.yourdomain.com/health

# 2. Frontend erreichbar:
curl -I https://yourdomain.com

# 3. Authentication:
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# 4. AI Agent:
curl https://api.yourdomain.com/api/v1/agent/health

# 5. Database Connections:
curl https://api.yourdomain.com/api/health/detailed
```

---

## **🎉 GO LIVE!**

Alles grün? Glückwunsch! 🚀

**Support:** support@sigmacode.ai  
**Docs:** https://docs.sigmacode.ai  
**Status:** https://status.sigmacode.ai

---

**Version:** 2.0.0 - Production Ready  
**Last Updated:** 20. Oktober 2025
