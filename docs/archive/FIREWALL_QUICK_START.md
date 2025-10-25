# 🚀 FIREWALL DASHBOARD - QUICK START

## 📋 Schritt-für-Schritt Integration

### 1. Backend ist bereits fertig ✅

Das Backend läuft bereits! Keine zusätzlichen Schritte nötig.

**Verfügbare Endpoints:**
- `GET /api/v1/firewall/dashboard` - Dashboard Analytics
- `GET /api/v1/firewall/activities` - Activity Log
- `GET /api/v1/firewall/customers` - Customer Monitors
- `POST /api/v1/firewall/customers` - Add Customer
- `GET /api/v1/firewall/rules` - Firewall Rules
- `POST /api/v1/firewall/rules` - Add Rule
- `WS /api/v1/firewall/stream` - Real-Time Updates

### 2. Frontend Route hinzufügen

**Option A: Eigene Route (empfohlen für Banken)**
```typescript
// In frontend/src/App.tsx
import FirewallDashboard from './pages/FirewallDashboard';

// In Routes:
<Route path="/firewall" element={<FirewallDashboard />} />
```

**Option B: Als Tab im Main Dashboard**
```typescript
// In frontend/src/pages/MainDashboard.tsx
import CustomerMonitorManager from '@/components/firewall/CustomerMonitorManager';
import RuleEditor from '@/components/firewall/RuleEditor';

// Add Tab:
<Tab label="🛡️ Firewall">
  <div className="space-y-6">
    <CustomerMonitorManager />
    <RuleEditor />
  </div>
</Tab>
```

### 3. Navigation hinzufügen

```typescript
// In frontend/src/components/Layout.tsx (Sidebar)
const navItems = [
  // ... existing items
  {
    path: '/firewall',
    label: 'Firewall',
    icon: Shield,
    plan: 'plus'  // Requires Plus Plan
  }
];
```

### 4. Dependencies prüfen

```bash
cd frontend

# Chart.js für Dashboard-Charts
npm install chart.js react-chartjs-2

# Lucide Icons (bereits installiert)
# npm install lucide-react
```

### 5. Test: Customer Monitor anlegen

```bash
# Terminal 1: Backend starten
cd backend
uvicorn app.main:app --reload

# Terminal 2: API Test
curl -X POST http://localhost:8000/api/v1/firewall/customers \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test-Kunde ABC",
    "wallet_addresses": [
      "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "0x28C6c06298d514Db089934071355E5743bf21d60"
    ],
    "alert_on": ["critical", "high"],
    "notify_email": "compliance@bank.com"
  }'

# Response:
# {
#   "success": true,
#   "monitor_id": "mon_1729...",
#   "message": "Customer monitor created for Test-Kunde ABC",
#   "wallets_count": 2
# }
```

### 6. Test: Transaction scannen

```bash
# Scanne Transaction von überwachter Adresse
curl -X POST http://localhost:8000/api/v1/firewall/scan \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "ethereum",
    "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "to_address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
    "value": 1.5,
    "value_usd": 2500,
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
  }'

# → Backend loggt: "🚨 CUSTOMER ALERT: Test-Kunde ABC | ..."
# → Activity wird geloggt
# → Dashboard zeigt neue Activity
```

### 7. Frontend öffnen

```bash
cd frontend
npm run dev

# Öffne: http://localhost:3000/firewall
```

**Was du sehen solltest:**
1. 📊 Dashboard mit 4 KPI-Cards
2. 📈 Charts (leer, wenn keine Daten)
3. 👥 Customer Monitors (dein Test-Kunde)
4. 📜 Rules (noch leer)
5. 🔴 WebSocket-Verbindung (Check Console)

---

## 🎯 USE CASE: Bank überwacht Kunden

### Schritt 1: Customer hinzufügen
1. Öffne `/firewall`
2. Klicke "Add Customer"
3. Eingabe:
   - **Customer Name:** Bank-Kunde XYZ
   - **Wallet Addresses:** (eine pro Zeile)
     ```
     0x123...
     0x456...
     0x789...
     ```
   - **Alert On:** ☑️ Critical, ☑️ High
   - **Email:** compliance@bank.com
4. Click "Create Monitor"

### Schritt 2: Kunde macht Transaction
- Transaction wird automatisch gescannt (via Firewall-Integration)
- Falls HIGH/CRITICAL Threat → Alert!
- Dashboard updated automatisch

### Schritt 3: Compliance prüft
1. Dashboard zeigt Alert in "Recent Activities"
2. Click auf Activity → Details
3. Siehe: Customer Name, Threat Level, Evidence
4. Action: Kunde kontaktieren/blockieren

---

## ⚙️ KONFIGURATION

### Email-Benachrichtigungen (Optional)
```python
# backend/.env
EMAIL_ENABLED=true
EMAIL_FROM=firewall@yourbank.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
```

### Webhook-Integration (Optional)
```python
# In backend/app/services/ai_firewall_core.py
# Zeile 950-954: Uncomment webhook code

import httpx
if monitor.notify_webhook:
    async with httpx.AsyncClient() as client:
        await client.post(monitor.notify_webhook, json={
            "customer": monitor.customer_name,
            "wallet": tx.from_address,
            "threat_level": detection.threat_level.value,
            "timestamp": datetime.now().isoformat()
        })
```

---

## 🐛 TROUBLESHOOTING

### Problem: WebSocket verbindet nicht
```javascript
// Check Frontend Console:
// Error: WebSocket connection failed

// Fix: Update WebSocket URL
const wsUrl = `ws://localhost:8000/api/v1/firewall/stream?user_id=${userId}`;
// → Change to your backend URL
```

### Problem: Charts zeigen nicht
```bash
# Install Chart.js
npm install chart.js react-chartjs-2

# Import in FirewallDashboard.tsx ist bereits vorhanden
```

### Problem: "401 Unauthorized"
```javascript
// Check Token in localStorage
localStorage.getItem('token')
// → Should return JWT token

// If null: Login first
```

### Problem: No Activities shown
```bash
# Scan ein paar Test-Transaktionen:
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/firewall/scan \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "chain": "ethereum",
      "from_address": "0x123...",
      "to_address": "0x456...",
      "value": 1.0,
      "value_usd": 1500,
      "wallet_address": "0x123..."
    }'
done
```

---

## 📊 DEMO-DATEN FÜR PRÄSENTATION

```bash
# Script: demo_firewall_data.sh
#!/bin/bash

TOKEN="YOUR_TOKEN"
API="http://localhost:8000/api/v1"

# 1. Add 3 Customer Monitors
curl -X POST $API/firewall/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "Premium Customer A", "wallet_addresses": ["0x123..."], "alert_on": ["critical", "high"]}'

curl -X POST $API/firewall/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "Corporate Client B", "wallet_addresses": ["0x456..."], "alert_on": ["critical"]}'

curl -X POST $API/firewall/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "High-Risk Customer C", "wallet_addresses": ["0x789..."], "alert_on": ["critical", "high", "medium"]}'

# 2. Add 5 Firewall Rules
curl -X POST $API/firewall/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rule_type": "address", "condition": {"address": "0xBadScammer..."}, "action": "block", "priority": 900, "description": "Known scammer wallet"}'

curl -X POST $API/firewall/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rule_type": "contract", "condition": {"contract": "0xMixer..."}, "action": "warn", "priority": 700, "description": "Mixer contract interaction"}'

# 3. Scan 20 Test-Transactions
for i in {1..20}; do
  THREAT_LEVEL=$((RANDOM % 5))  # Random 0-4
  VALUE=$((RANDOM % 10000 + 100))
  
  curl -X POST $API/firewall/scan \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"chain\": \"ethereum\",
      \"from_address\": \"0x123...\",
      \"to_address\": \"0x$(openssl rand -hex 20)\",
      \"value\": $(echo "scale=4; $VALUE/1000" | bc),
      \"value_usd\": $VALUE,
      \"wallet_address\": \"0x123...\"
    }"
  
  sleep 0.5
done

echo "✅ Demo data created!"
```

Mache Script ausführbar:
```bash
chmod +x demo_firewall_data.sh
./demo_firewall_data.sh
```

---

## ✅ CHECKLISTE

- [ ] Backend läuft (`uvicorn app.main:app --reload`)
- [ ] Frontend läuft (`npm run dev`)
- [ ] Chart.js installiert (`npm install chart.js react-chartjs-2`)
- [ ] Route zu `/firewall` hinzugefügt
- [ ] Navigation updated (Sidebar Link)
- [ ] Test-Customer angelegt (via API)
- [ ] Test-Transaction gescannt
- [ ] Dashboard zeigt Daten
- [ ] WebSocket verbindet (Check Console: "🔌 Firewall WebSocket connected")

---

## 🎉 FERTIG!

**Du hast jetzt:**
✅ Interaktives Firewall Dashboard  
✅ Customer Monitoring für Banken  
✅ Rule Management System  
✅ Real-Time Updates  
✅ Activity Log  
✅ Charts & Analytics  

**Next Level:**
- Email/Webhook Alerts aktivieren
- PostgreSQL für Persistence
- Mehr Rules hinzufügen
- Export-Features (CSV/PDF)

---

## 📞 SUPPORT

**Fragen?** Check:
1. Browser Console (F12) → WebSocket errors?
2. Backend Logs → `uvicorn` output
3. Network Tab → API calls successful?
4. Code-Kommentare in Components

**Common Issues:**
- CORS: Backend `.env` → `CORS_ORIGINS=http://localhost:3000`
- Auth: Token expired? Re-login
- WebSocket: URL falsch? Check `FirewallDashboard.tsx` Line 92

---

**HAPPY MONITORING! 🛡️**
