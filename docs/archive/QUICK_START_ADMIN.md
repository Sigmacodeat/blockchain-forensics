# 🚀 QUICK START - Admin-Account erstellen

## ❌ PROBLEM: Login schlägt fehl (401 Unauthorized)

**Grund:** Der Admin-Account existiert noch nicht in der Datenbank!

---

## ✅ LÖSUNG: Database starten & Admin erstellen

### **Option 1: Mit Docker (Empfohlen)**

```bash
# 1. Docker Desktop starten
open -a Docker

# 2. Warten bis Docker läuft (ca. 10-20 Sekunden)

# 3. PostgreSQL & Redis starten
cd /Users/msc/CascadeProjects/blockchain-forensics
docker-compose up -d postgres redis

# 4. Warten bis DB bereit ist (ca. 5 Sekunden)
sleep 5

# 5. Admin-Account erstellen
cd backend
python create_admin.py

# 6. Backend starten
python -m uvicorn app.main:app --reload --port 8000
```

---

### **Option 2: Backend mit SQLite (Schnell-Test)**

Wenn Docker nicht verfügbar ist, Backend temporär mit SQLite:

```bash
# 1. Backend-Config für SQLite
cd /Users/msc/CascadeProjects/blockchain-forensics/backend
export USE_SQLITE=true
export DATABASE_URL="sqlite:///./test.db"

# 2. Database initialisieren
python -c "
from app.db.session import engine
from app.db.models import Base
Base.metadata.create_all(bind=engine)
print('✅ SQLite Database erstellt')
"

# 3. Admin-Account erstellen
python create_admin.py

# 4. Backend starten
python -m uvicorn app.main:app --reload --port 8000
```

---

### **Option 3: Manuell via pgAdmin/psql**

Wenn PostgreSQL bereits läuft:

```bash
# 1. Mit PostgreSQL verbinden
psql -U postgres -h localhost -d blockchain_forensics

# 2. SQL ausführen:
```

```sql
-- Admin-Account erstellen
INSERT INTO users (
  email, 
  username, 
  password_hash,
  role,
  plan,
  display_name,
  is_active,
  email_verified,
  created_at
) VALUES (
  'admin@blockchain-forensics.com',
  'admin',
  '$2b$12$.QcLzIArq6LOhkCD0VROTudd04DSOs.YKHr5R7LHMS8XAZWyluCTi', -- Admin2025!Secure
  'admin',
  'enterprise',
  'System Administrator',
  true,
  true,
  NOW()
);

-- Prüfen
SELECT id, email, role, plan FROM users WHERE email = 'admin@blockchain-forensics.com';
```

---

## 🔑 ADMIN-CREDENTIALS

Nach erfolgreicher Erstellung:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ADMIN LOGIN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

URL:      http://localhost:3000/login
E-Mail:   admin@blockchain-forensics.com
Passwort: Admin2025!Secure

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🧪 TESTEN

```bash
# 1. Backend prüfen
curl http://localhost:8000/api/v1/system/health

# 2. Login testen
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@blockchain-forensics.com",
    "password": "Admin2025!Secure"
  }'

# Erwartete Antwort:
# {
#   "access_token": "eyJ...",
#   "token_type": "bearer",
#   "user": {
#     "email": "admin@blockchain-forensics.com",
#     "role": "admin",
#     "plan": "enterprise"
#   }
# }
```

---

## 📋 CHECKLISTE

Vor dem Login sicherstellen:

```
✅ Docker Desktop läuft
✅ PostgreSQL Container läuft (docker-compose ps)
✅ Backend läuft auf Port 8000 (curl localhost:8000/health)
✅ Admin-Account erstellt (python create_admin.py)
✅ Frontend läuft auf Port 3000 (npm run dev)
```

---

## 🔧 TROUBLESHOOTING

### **"Connection refused" Fehler:**
```bash
# PostgreSQL läuft nicht
→ Lösung: docker-compose up -d postgres
```

### **"401 Unauthorized" beim Login:**
```bash
# Admin-Account existiert nicht
→ Lösung: python create_admin.py
```

### **"Database not found":**
```bash
# Database wurde nicht initialisiert
→ Lösung: 
docker-compose down -v
docker-compose up -d postgres
sleep 5
cd backend && alembic upgrade head
python create_admin.py
```

### **"Cannot connect to Docker daemon":**
```bash
# Docker Desktop läuft nicht
→ Lösung: open -a Docker
# Warten bis Docker-Icon oben rechts aktiv ist
```

---

## 🚀 SCHNELLSTART (All-in-One)

```bash
#!/bin/bash
# quick_start.sh

echo "🚀 Starting Blockchain Forensics Platform..."

# 1. Docker starten (falls nicht läuft)
if ! docker info > /dev/null 2>&1; then
    echo "⏳ Starting Docker..."
    open -a Docker
    sleep 20
fi

# 2. Database starten
echo "🐘 Starting PostgreSQL..."
cd /Users/msc/CascadeProjects/blockchain-forensics
docker-compose up -d postgres redis
sleep 5

# 3. Admin erstellen
echo "👤 Creating admin account..."
cd backend
python create_admin.py

# 4. Backend starten (Background)
echo "🔧 Starting backend..."
python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# 5. Frontend starten (Background)
echo "🎨 Starting frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Platform is starting!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌐 Frontend: http://localhost:3000"
echo "  🔧 Backend:  http://localhost:8000"
echo "  📚 API Docs: http://localhost:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔑 Admin Login:"
echo "   Email:    admin@blockchain-forensics.com"
echo "   Password: Admin2025!Secure"
echo ""
echo "Press Ctrl+C to stop all services"

# Warten auf Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; docker-compose down; exit" INT
wait
```

**Ausführbar machen:**
```bash
chmod +x quick_start.sh
./quick_start.sh
```

---

## 📚 WEITERE DOKUMENTATION

- `ADMIN_CREDENTIALS.md` - Alle Login-Daten & Test-Accounts
- `ADMIN_SEPARATION_COMPLETE.md` - Admin/User-Trennung
- `FINAL_SYSTEM_CHECK.md` - Production Verification

---

## ✅ ERFOLG!

Wenn alles funktioniert siehst du:

```
1. Login-Seite: http://localhost:3000/login
2. Email eingeben: admin@blockchain-forensics.com
3. Passwort eingeben: Admin2025!Secure
4. Login → Weiterleitung zu Dashboard Hub
5. Du siehst 4 Filter-Tabs (Alle, Forensik, Analytics, Admin)
6. Alle 16 Dashboards sind verfügbar
```

**VIEL ERFOLG! 🚀**
