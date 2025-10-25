# 🚀 Quick Start - Plattform sofort testen

**Zeit:** 5 Minuten  
**Ziel:** Alle Premium-Features mit Mock-Daten testen

---

## ⚡ Schnellstart in 3 Schritten

### **Schritt 1: Backend starten**

```bash
cd backend
source venv/bin/activate  # oder: venv\Scripts\activate (Windows)
python main.py
```

✅ Backend läuft auf: `http://localhost:8000`  
✅ API Docs: `http://localhost:8000/docs`

---

### **Schritt 2: Frontend starten**

```bash
cd frontend
npm run dev
```

✅ Frontend läuft auf: `http://localhost:5173`

---

### **Schritt 3: Test-Adresse eingeben**

#### **Dashboard öffnen:** `http://localhost:5173/dashboard`

#### **Transaction Tracing testen:**
1. Click "Transaction Tracing" Card
2. Adresse eingeben: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb`
3. Chain: `Ethereum`
4. Click "Start Trace"

**✅ Erwartetes Ergebnis:**
- Trace startet
- Risk Score: 92 (HIGH RISK)
- Labels: mixer, high-risk
- Graph wird aufgebaut

---

## 🎯 5 Must-Test Features (je 1 Minute)

### **1. Risk Assessment** ⏱️ 30 Sekunden

**URL:** `/trace?address=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb&chain=ethereum`

**Check:**
- ✅ Risk Copilot zeigt Score
- ✅ "CRITICAL RISK 92%" Badge
- ✅ Categories: Mixer, Sanctions
- ✅ Reasons werden angezeigt

---

### **2. Graph Explorer** ⏱️ 1 Minute

**URL:** `/investigator?address=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb&auto_trace=true`

**Check:**
- ✅ 3D Graph lädt automatisch
- ✅ Nodes sind farbig (Risk-basiert)
- ✅ Click auf Node → Sidebar öffnet
- ✅ Hover → Tooltip mit Details

---

### **3. Cases** ⏱️ 1 Minute

**URL:** `/cases`

**Check:**
- ✅ 32+ Cases werden angezeigt
- ✅ Filter funktioniert (Status, Risk)
- ✅ Click auf Case → Detail Page
- ✅ Evidence Items (5) vorhanden
- ✅ Export Buttons (CSV, PDF)

---

### **4. AI Chat** ⏱️ 1 Minute

**URL:** `/dashboard` → Chat Panel rechts unten

**Test-Commands:**
```
1. "Trace 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
   → AI erkennt Intent, schlägt Navigation vor

2. "Show high-risk cases"
   → AI listet Cases

3. Ctrl+K (Command Palette)
   → Template-Auswahl öffnet
```

---

### **5. Entity Labels** ⏱️ 30 Sekunden

**API Test:**
```bash
curl http://localhost:8000/api/v1/labels/enrich?address=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb&chain=ethereum
```

**Check:**
- ✅ Labels: ["mixer", "high-risk"]
- ✅ Risk Score: 92
- ✅ Sources: Community Reports

---

## 🧪 Test-Adressen Cheat-Sheet

**Copy-Paste Ready:**

```
High-Risk Mixer (Ethereum):
0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

Exchange (Bitcoin - Coinbase):
bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

Test Address mit Cases (Ethereum):
0xAbCDEF0000000000000000000000000000000123

Polygon L2:
0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0
```

---

## 📱 Mobile Testing

**URL:** `http://localhost:5173/dashboard`

**Device Emulation:**
1. Chrome DevTools → Toggle Device Toolbar (Ctrl+Shift+M)
2. Wähle: iPhone 14 Pro
3. Test: Sidebar Slide-out, Touch Gestures

---

## 🎨 UI Features Checklist

**Dashboard:**
- [ ] Quick Actions Cards reagieren auf Hover
- [ ] Live Metrics zeigen Trends (↗/↘)
- [ ] Glassmorphism Effects sichtbar
- [ ] Dark Mode funktioniert

**Trace Page:**
- [ ] Form Validation (ungültige Adresse)
- [ ] Live Progress Bar
- [ ] Risk Copilot zeigt Score
- [ ] Export Buttons vorhanden

**Graph:**
- [ ] 3D Visualization lädt
- [ ] Zoom/Pan funktioniert
- [ ] Sidebar öffnet bei Click
- [ ] Color-Coding nach Risk Level

---

## 🔥 Power-User Features

### **Command Palette** (Ctrl/Cmd+K)
```
1. Drücke: Ctrl+K (Windows) oder Cmd+K (Mac)
2. Wähle Template: "High-Risk Trace"
3. Input ist pre-filled
4. Enter → Trace startet
```

### **Keyboard Shortcuts**
```
Ctrl+K       → Command Palette
ESC          → Close Modal/Sidebar
/            → Focus Search
Ctrl+B       → Toggle Sidebar
```

### **API Testing (cURL)**

```bash
# 1. Risk Stream (SSE)
curl -N http://localhost:8000/api/v1/risk/stream?address=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb&chain=ethereum

# 2. Start Trace
curl -X POST http://localhost:8000/api/v1/trace \
  -H "Content-Type: application/json" \
  -d '{
    "source_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "chain": "ethereum",
    "max_depth": 5
  }'

# 3. List Cases
curl http://localhost:8000/api/v1/cases

# 4. Label Enrichment
curl http://localhost:8000/api/v1/labels/enrich?address=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb&chain=ethereum
```

---

## 🐛 Troubleshooting

### **Backend startet nicht**
```bash
# Check dependencies
pip install -r requirements.txt

# Check .env file
cp .env.example .env
```

### **Frontend startet nicht**
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install
```

### **Graph lädt nicht**
- Check Browser Console (F12)
- WebGL muss aktiviert sein
- Test in Chrome/Firefox (nicht IE)

### **Mock-Daten fehlen**
```bash
# Check files exist
ls data/cases/
ls backend/data/labels/
```

---

## ✅ Success Criteria

**Nach 5 Minuten solltest du gesehen haben:**

1. ✅ Transaction Trace gestartet
2. ✅ Risk Score 92 (HIGH RISK)
3. ✅ 3D Graph mit Nodes
4. ✅ 32+ Cases angezeigt
5. ✅ AI Chat antwortet auf Commands
6. ✅ Entity Labels gefunden (5,247)
7. ✅ Export funktioniert (CSV)

**Wenn JA → Plattform ist PRODUCTION READY!** 🎉

---

## 🚀 Next Level

**Für vollständige Tests siehe:**
→ `PREMIUM_PLATFORM_TEST_GUIDE.md` (komplett, 60+ Seiten)

**Für Production Deployment:**
1. RPC-Endpoints konfigurieren (Infura/Alchemy)
2. Redis starten (WebSocket Support)
3. PostgreSQL migrieren
4. Neo4j Graph DB starten
5. `.env` Production-Werte setzen

---

## 📞 Support

**Bei Fragen:**
- Docs: `/docs` (Swagger UI)
- Issues: GitHub Issues
- Chat: support@sigmacode.io

---

**Erstellt:** 19. Oktober 2025  
**Dauer:** ⚡ 5 Minuten zum Testen  
**Status:** ✅ Alle Features testbar mit Mock-Daten
