# 🧪 Manual Test Checklist - Lawyer Use Case

**Datum**: 20. Oktober 2025  
**Tester**: _____________  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

---

## ⚠️ WICHTIG: Das muss VOR Production-Launch getestet werden!

Diese Tests prüfen den **kritischen User-Flow** eines Anwalts:
1. Account erstellen
2. Bitcoin-Adresse tracen
3. Ergebnisse analysieren
4. Inline-Chat nutzen
5. Report exportieren

---

## 🚀 Pre-Test Setup

### 1. Backend starten
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Erwartung**: Backend läuft auf http://localhost:8000  
**Check**: `curl http://localhost:8000/health` → `{"status":"healthy"}`

✅ Backend läuft: [ ]

### 2. Frontend starten
```bash
cd frontend
npm run dev
```

**Erwartung**: Frontend läuft auf http://localhost:5173  
**Check**: Browser öffnen → http://localhost:5173

✅ Frontend läuft: [ ]

### 3. Services prüfen
```bash
docker-compose ps
```

**Erwartung**: Alle Services "healthy"
- postgres
- neo4j
- redis
- kafka (optional)

✅ Alle Services healthy: [ ]

---

## 📋 TEST 1: User Registration & Login

### Test 1.1: Signup
1. Öffne: http://localhost:5173/register
2. Fülle Formular aus:
   - Email: `lawyer-test@example.com`
   - Password: `SecurePass123!`
   - Name: `Test Lawyer`
3. Klicke "Sign Up"

**Erwartung**: 
- ✅ Erfolgsmeldung
- ✅ Redirect zu /login oder /dashboard
- ✅ Email-Verification (optional)

**Ergebnis**: [ ] PASS [ ] FAIL  
**Screenshot**: _____________  
**Notes**: _____________

### Test 1.2: Login
1. Öffne: http://localhost:5173/login
2. Login mit:
   - Email: `lawyer-test@example.com`
   - Password: `SecurePass123!`
3. Klicke "Login"

**Erwartung**:
- ✅ Erfolgreich eingeloggt
- ✅ Redirect zu /dashboard
- ✅ Username sichtbar im Header
- ✅ Logout-Button vorhanden

**Ergebnis**: [ ] PASS [ ] FAIL  
**Screenshot**: _____________

---

## 📋 TEST 2: Bitcoin Address Tracing

### Test 2.1: Navigation zu Trace-Page
1. Im Dashboard: Klicke "Trace" in Sidebar
2. Oder navigiere zu: http://localhost:5173/trace

**Erwartung**:
- ✅ Trace-Page lädt
- ✅ Input-Formular sichtbar
- ✅ Chain-Selector zeigt "Bitcoin"

**Ergebnis**: [ ] PASS [ ] FAIL

### Test 2.2: Bitcoin Trace starten
1. Gib ein: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` (Satoshi's Address)
2. Wähle Chain: `Bitcoin`
3. Max Depth: `2`
4. Max Transactions: `10`
5. Klicke "Start Trace"

**Erwartung**:
- ✅ Loading-Indicator erscheint
- ✅ Trace startet (WebSocket-Connection)
- ✅ Progress-Updates sichtbar
- ✅ Nach 5-30 Sekunden: Ergebnisse erscheinen

**Ergebnis**: [ ] PASS [ ] FAIL  
**Trace-ID**: _____________  
**Screenshot**: _____________

### Test 2.3: Trace-Ergebnisse prüfen
Nach dem Trace sollte sichtbar sein:
- ✅ Graph-Visualisierung (Nodes + Edges)
- ✅ Source-Address highlighted
- ✅ Connected Addresses
- ✅ Transaction-Details
- ✅ Risk-Score (wenn implementiert)
- ✅ Labels (Exchange, Mixer, etc.)

**Ergebnis**: [ ] PASS [ ] FAIL  
**Notes**: _____________

---

## 📋 TEST 3: Inline Chat Agent (KRITISCH!)

### Test 3.1: Chat öffnen
1. Im Dashboard: Suche Inline-Chat-Panel
2. Oder drücke: `Ctrl+K` (Command Palette)

**Erwartung**:
- ✅ Chat-Panel öffnet sich
- ✅ Input-Feld sichtbar
- ✅ "Forensik Control Center" Titel
- ✅ Quick-Action-Buttons vorhanden

**Ergebnis**: [ ] PASS [ ] FAIL

### Test 3.2: Natural Language Trace
Im Chat eingeben:
```
Trace Bitcoin address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa with max depth 3
```

**Erwartung**:
- ✅ Agent versteht Intent
- ✅ Agent startet Trace automatisch
- ✅ Live-Updates im Chat
- ✅ Link zu Trace-Results
- ✅ Oder: Auto-Navigation zu /trace

**Ergebnis**: [ ] PASS [ ] FAIL  
**Agent-Response**: _____________

### Test 3.3: Ask about Results
Im Chat eingeben:
```
What are the high-risk addresses in my last trace?
```

**Erwartung**:
- ✅ Agent analysiert Trace-Daten
- ✅ Listet high-risk addresses
- ✅ Erklärt Gründe (Mixer, Sanctions, etc.)
- ✅ Strukturierte Antwort

**Ergebnis**: [ ] PASS [ ] FAIL  
**Agent-Response**: _____________

### Test 3.4: Command Palette
1. Drücke `Ctrl+K`
2. Wähle Template: "High-Risk Trace"

**Erwartung**:
- ✅ Modal öffnet
- ✅ 6 Templates sichtbar
- ✅ Template-Click fügt Query ein
- ✅ Agent führt aus

**Ergebnis**: [ ] PASS [ ] FAIL

---

## 📋 TEST 4: Report Export (Lawyer Critical!)

### Test 4.1: CSV Export
1. Nach einem Trace: Klicke "Export CSV"
2. Datei sollte downloaden

**Erwartung**:
- ✅ CSV-File heruntergeladen
- ✅ Enthält: Addresses, Amounts, Timestamps
- ✅ Excel-kompatibel
- ✅ Encoding korrekt (UTF-8)

**Ergebnis**: [ ] PASS [ ] FAIL  
**File-Size**: _______ KB

### Test 4.2: PDF Export (wenn implementiert)
1. Klicke "Export PDF"
2. PDF sollte generieren

**Erwartung**:
- ✅ PDF generiert
- ✅ Professional Layout
- ✅ Logo + Header
- ✅ Alle Daten enthalten
- ✅ Druckbar

**Ergebnis**: [ ] PASS [ ] FAIL [ ] N/A

### Test 4.3: Evidence Export (Gerichtsverwertbar!)
1. Klicke "Export Evidence" (JSON)
2. JSON sollte downloaden

**Erwartung**:
- ✅ JSON-File mit SHA256-Hash
- ✅ Timestamp enthalten
- ✅ Signature (optional)
- ✅ Chain-of-Custody Infos

**Ergebnis**: [ ] PASS [ ] FAIL [ ] N/A

---

## 📋 TEST 5: Multi-Chain Support

### Test 5.1: Ethereum Trace
Wiederhole Test 2 mit Ethereum-Address:
```
0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

**Ergebnis**: [ ] PASS [ ] FAIL

### Test 5.2: Solana Trace (optional)
Wiederhole Test 2 mit Solana-Address:
```
7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
```

**Ergebnis**: [ ] PASS [ ] FAIL [ ] N/A

---

## 📋 TEST 6: Performance & UX

### Test 6.1: Loading Times
Messe mit Browser DevTools:
- Page Load: _______ ms (Target: <2000ms)
- API Response: _______ ms (Target: <500ms)
- Trace Start: _______ ms (Target: <1000ms)

**Ergebnis**: [ ] PASS [ ] FAIL

### Test 6.2: Mobile View
1. Browser DevTools → Mobile Emulation
2. Teste alle Screens

**Erwartung**:
- ✅ Responsive Layout
- ✅ Buttons klickbar
- ✅ Text lesbar
- ✅ Chat funktioniert

**Ergebnis**: [ ] PASS [ ] FAIL

### Test 6.3: Error Handling
1. Gib ungültige Bitcoin-Address ein
2. Gib leeres Formular ab
3. Logout während Trace

**Erwartung**:
- ✅ Error-Messages klar
- ✅ Keine Crashes
- ✅ Graceful Degradation

**Ergebnis**: [ ] PASS [ ] FAIL

---

## 📋 TEST 7: AI Agent Tools (Advanced)

### Test 7.1: Risk Scoring
Im Chat:
```
What's the risk score for address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa?
```

**Erwartung**: Agent gibt Risk-Score zurück

**Ergebnis**: [ ] PASS [ ] FAIL [ ] N/A

### Test 7.2: Sanctions Check
Im Chat:
```
Check if address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa is sanctioned
```

**Erwartung**: Agent prüft Sanctions-Listen

**Ergebnis**: [ ] PASS [ ] FAIL [ ] N/A

### Test 7.3: Mixer Detection
Im Chat:
```
Are there any mixer addresses in my last trace?
```

**Erwartung**: Agent erkennt Mixer (Tornado Cash, etc.)

**Ergebnis**: [ ] PASS [ ] FAIL [ ] N/A

---

## 📊 FINAL SUMMARY

**Total Tests**: 25  
**Passed**: _______  
**Failed**: _______  
**N/A**: _______

**Pass Rate**: _______% (Target: >90%)

---

## ✅ PRODUCTION-READY CRITERIA

Für Production Launch müssen bestehen:
- [ ] Test 1 (Registration): 100%
- [ ] Test 2 (Bitcoin Trace): 100%
- [ ] Test 3 (Inline Chat): 100%
- [ ] Test 4 (Report Export): >80%
- [ ] Test 5 (Multi-Chain): >70%
- [ ] Test 6 (Performance): >80%
- [ ] Test 7 (AI Tools): >50%

**OVERALL STATUS**: [ ] READY [ ] NOT READY

---

## 🐛 BUGS FOUND

| Bug ID | Description | Severity | Status |
|--------|-------------|----------|--------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## 📝 NOTES & RECOMMENDATIONS

_____________________________________________
_____________________________________________
_____________________________________________

---

**Tester Signature**: _____________  
**Date**: _____________  
**Approved by**: _____________
