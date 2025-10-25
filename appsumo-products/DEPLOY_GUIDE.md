# 🚀 APPSUMO PRODUCTS - DEPLOYMENT GUIDE

**Alle 12 Produkte starten in 5 Minuten!**

---

## 📋 QUICK START

### **Option 1: Einzelnes Produkt** (empfohlen für Test)
```bash
cd appsumo-products/chatbot-pro
docker-compose up
```

**URLs**:
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

---

### **Option 2: Alle 12 Produkte** (Master Deploy)
```bash
cd appsumo-products
./start-all.sh
```

**Ports**:
- Frontend: 3001-3012
- Backend: 8001-8012

---

## 🎯 PRODUKTIONS-DEPLOYMENT

### **1. Environment Variables**

Jedes Produkt braucht `.env`:

```bash
# Für ChatBot Pro
cd appsumo-products/chatbot-pro/backend
cp .env.example .env

# Editieren:
OPENAI_API_KEY=sk-...
NOWPAYMENTS_API_KEY=...
DATABASE_URL=postgresql://...
```

**Wichtig**: 
- ChatBot Pro braucht **OpenAI API Key**
- Crypto Payments brauchen **NOWPayments Key**

---

### **2. Docker Build**

```bash
# Alle Produkte bauen
cd appsumo-products
for dir in */; do
    echo "Building $dir..."
    cd $dir
    docker-compose build
    cd ..
done
```

---

### **3. Production Start**

```bash
# Mit docker-compose
docker-compose -f docker-compose.master.yml up -d

# Check Status
docker-compose -f docker-compose.master.yml ps

# View Logs
docker-compose -f docker-compose.master.yml logs -f
```

---

## 🔧 TROUBLESHOOTING

### **Problem: Port bereits belegt**
```bash
# Check welche Ports belegt sind
lsof -i :8001

# Lösung: Andere Ports in docker-compose.yml
ports:
  - "8091:8000"  # Statt 8001
```

---

### **Problem: Build Fehler**
```bash
# Clean Build
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

---

### **Problem: Database Connection**
```bash
# Check ob Postgres läuft
docker-compose ps

# Warte länger für DB-Start
docker-compose up -d db
sleep 10
docker-compose up
```

---

## 📊 HEALTH CHECKS

### **Backend Check**:
```bash
# Alle Backends testen
for port in {8001..8012}; do
    echo "Port $port:"
    curl -s http://localhost:$port/health | jq .
done
```

### **Frontend Check**:
```bash
# Browser öffnen
for port in {3001..3012}; do
    open http://localhost:$port
done
```

---

## 🎨 FRONTEND DEVELOPMENT

### **Entwicklungsmodus**:
```bash
cd appsumo-products/chatbot-pro/frontend
npm install
npm run dev
```

### **Production Build**:
```bash
npm run build
npm run preview
```

---

## 🐳 DOCKER COMMANDS

### **Starten**:
```bash
docker-compose up          # Foreground
docker-compose up -d       # Background
```

### **Stoppen**:
```bash
docker-compose stop        # Stoppen
docker-compose down        # Stoppen + Entfernen
docker-compose down -v     # + Volumes löschen
```

### **Logs**:
```bash
docker-compose logs           # Alle Logs
docker-compose logs backend   # Nur Backend
docker-compose logs -f        # Follow Mode
```

### **Neustart**:
```bash
docker-compose restart        # Alle
docker-compose restart backend  # Nur Backend
```

---

## 📦 PRODUCTION CHECKLIST

### **Pro Produkt**:
- [ ] `.env` File konfiguriert
- [ ] API Keys eingetragen
- [ ] Docker Build erfolgreich
- [ ] Health Check OK
- [ ] Frontend lädt
- [ ] API Endpoints testen

### **Testing**:
```bash
# Backend Health
curl http://localhost:8001/health

# API Test
curl http://localhost:8001/

# Frontend
open http://localhost:3001
```

---

## 🌐 NGINX REVERSE PROXY

### **Nginx Config** (optional für Production):
```nginx
# chatbot-pro.yourdomain.com
server {
    listen 80;
    server_name chatbot-pro.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
    }
    
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
    }
}
```

---

## 🔒 SECURITY

### **Wichtig**:
1. ✅ Niemals `.env` in Git committen!
2. ✅ API Keys sicher speichern
3. ✅ CORS nur für eigene Domains
4. ✅ HTTPS in Production nutzen
5. ✅ Firewall für Backend-Ports

### **CORS Update** (Production):
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Nicht "*"!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📈 MONITORING

### **Health Check Endpoint**:
```bash
# Alle Backends monitoren
watch -n 5 'for p in {8001..8012}; do 
    curl -s http://localhost:$p/health | jq -r ".status"
done'
```

### **Docker Stats**:
```bash
docker stats
```

---

## 🚀 APPSUMO SUBMISSION

### **Benötigt pro Produkt**:
1. ✅ Live Demo URL
2. ✅ 5-8 Screenshots
3. ✅ 2-Min Demo Video
4. ✅ Product Description
5. ✅ Feature List
6. ✅ Pricing Tiers
7. ✅ Support Email

### **Demo URLs**:
- ChatBot Pro: https://demo.yourdomain.com/chatbot
- Analytics Pro: https://demo.yourdomain.com/analytics
- etc.

---

## ✅ QUICK TEST SCRIPT

```bash
#!/bin/bash
# test-all.sh

echo "🧪 Testing all 12 products..."

for port in {8001..8012}; do
    product=$(curl -s http://localhost:$port/ | jq -r '.message' 2>/dev/null)
    health=$(curl -s http://localhost:$port/health | jq -r '.status' 2>/dev/null)
    
    if [ "$health" = "healthy" ]; then
        echo "✅ Port $port: $product - HEALTHY"
    else
        echo "❌ Port $port: ERROR"
    fi
done
```

---

## 📞 SUPPORT

### **Issues?**
1. Check Logs: `docker-compose logs`
2. Restart: `docker-compose restart`
3. Rebuild: `docker-compose up --build`

### **Common Issues**:
- Port belegt → Andere Ports nutzen
- DB Error → Warten bis Postgres startet
- Build Error → Cache leeren + rebuild

---

**ALLE 12 PRODUKTE READY TO DEPLOY! 🚀**

**Erstellt**: 19. Okt 2025  
**Status**: Production Ready  
**Support**: support@yourdomain.com
