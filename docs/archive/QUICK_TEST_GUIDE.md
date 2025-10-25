# 🧪 Quick Test Guide - System Validierung

## Alles testen in 10 Minuten!

### Pre-Requisites
- Backend läuft auf Port 8000
- Frontend läuft auf Port 5173
- User hat Plus Plan oder höher

---

## Test 1: Bitcoin Investigation (5 Min)

### **A) Frontend Test**

1. **Navigate zu:**
   ```
   http://localhost:5173/de/bitcoin-investigation
   ```

2. **Eingeben:**
   ```
   Adressen: 
   - bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh (Test-Adresse)
   - 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa (Genesis-Block)
   
   Start Date: 2020-01-01
   End Date: 2024-10-19
   
   Optionen: Alle aktiviert (Clustering, Mixer, Flow)
   Case ID: test-case-001
   ```

3. **Click "Start Investigation"**
   - ⏱️ Warten: 30-60 Sekunden
   - ✅ Erwartung: Investigation Results anzeigen

4. **Ergebnis prüfen:**
   ```
   ✅ Summary Cards: Transactions, Clusters, Mixers, Dormant Funds
   ✅ Exit Points Table (falls vorhanden)
   ✅ Dormant Funds Table (falls vorhanden)
   ✅ Recommendations Liste
   ✅ Evidence Report Buttons (PDF/JSON/CSV)
   ```

5. **Report Download testen:**
   ```
   Click: "PDF Report" → Öffnet HTML im Browser
   Click: "JSON Evidence" → Lädt JSON-File
   Click: "CSV Export" → Lädt CSV-File
   ```

**✅ Test 1 bestanden wenn:** Alle Reports downloaden erfolgreich!

---

### **B) Backend API Test (direkt)**

**Test Investigation Endpoint:**
```bash
curl -X POST http://localhost:8000/api/v1/bitcoin-investigation/investigate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "addresses": ["bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"],
    "start_date": "2020-01-01",
    "end_date": "2024-10-19",
    "include_clustering": true,
    "include_mixer_analysis": true,
    "include_flow_analysis": true,
    "case_id": "api-test-001"
  }'
```

**Erwartetes Response:**
```json
{
  "investigation_id": "btc-inv-abc123...",
  "status": "completed",
  "execution_time_seconds": 45.2,
  "transactions": {
    "total_count": 1247,
    "total_volume_btc": 123.45,
    "unique_addresses": 456
  },
  "clustering": {...},
  "mixer_analysis": {...},
  "flow_analysis": {...},
  "summary": "Investigation completed...",
  "recommendations": [...]
}
```

**✅ Test bestanden wenn:** Response enthält investigation_id!

---

**Test Report Download:**
```bash
# Speichere investigation_id aus vorherigem Request
INVESTIGATION_ID="btc-inv-abc123..."

# Test PDF/HTML Report
curl http://localhost:8000/api/v1/bitcoin-investigation/investigations/$INVESTIGATION_ID/report.html \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o report.html

# Test JSON Evidence
curl http://localhost:8000/api/v1/bitcoin-investigation/investigations/$INVESTIGATION_ID/report.json \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o evidence.json

# Test CSV Export
curl http://localhost:8000/api/v1/bitcoin-investigation/investigations/$INVESTIGATION_ID/report.csv \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o export.csv
```

**✅ Test bestanden wenn:** Alle 3 Files heruntergeladen!

---

## Test 2: Graph Investigator (3 Min)

### **A) Frontend Test**

1. **Navigate zu:**
   ```
   http://localhost:5173/de/investigator
   ```

2. **Adresse eingeben:**
   ```
   Address: 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
   (Vitalik Buterin's Address - Ethereum)
   
   Max Hops: 2
   Include Bridges: aktiviert
   ```

3. **Graph lädt:**
   - ⏱️ Warten: 2-5 Sekunden
   - ✅ Erwartung: Interaktiver Graph erscheint

4. **Interaktionen testen:**
   ```
   ✅ Click auf Node → Details anzeigen
   ✅ "Expand Neighbors" → Neue Nodes laden
   ✅ Zoom In/Out → Graph skaliert
   ✅ Pan (Drag) → Graph bewegt sich
   ✅ Timeline → Events anzeigen
   ```

5. **Export testen:**
   ```
   Click: "Export Graph" → PNG heruntergeladen
   Click: "Export Timeline CSV" → CSV heruntergeladen
   ```

**✅ Test 2 bestanden wenn:** Graph interaktiv und Export funktioniert!

---

## Test 3: Integration Test (2 Min)

### **Von Investigation → Graph**

1. **Investigation durchführen** (siehe Test 1)
2. **In Results: Click "Open in Investigator"** bei Exit Point
3. **Graph öffnet** mit der Exit-Point-Adresse
4. **Graph zeigt** vollständige Verbindungen

**✅ Test 3 bestanden wenn:** Navigation funktioniert!

---

## Test 4: Report Quality Check (2 Min)

### **A) PDF/HTML Report prüfen**

1. **Öffne** heruntergeladene `report.html` im Browser
2. **Prüfe Inhalt:**
   ```
   ✅ Header mit Investigation ID
   ✅ Executive Summary
   ✅ Key Findings Table
   ✅ Investigated Addresses Table
   ✅ UTXO Clustering Results
   ✅ Mixer Analysis
   ✅ Exit Points Table
   ✅ Dormant Funds Table
   ✅ Recommendations
   ✅ Evidence Hash (SHA256)
   ✅ Footer mit Timestamp
   ```

3. **Print-Test:**
   ```
   Browser: Ctrl+P (Print)
   ✅ Layout sieht professionell aus
   ✅ Tables sind aligned
   ✅ Keine abgeschnittenen Texte
   ✅ Page Breaks korrekt
   ```

**✅ Test 4 bestanden wenn:** Report druckbar und professionell!

---

### **B) JSON Evidence prüfen**

1. **Öffne** `evidence.json`
2. **Prüfe Struktur:**
   ```json
   {
     "report_version": "1.0.0",
     "generated_at": "2024-10-19T...",
     "investigation": {...},
     "evidence_chain": {
       "timestamp": "2024-10-19T...",
       "hash": "abc123def456...",
       "algorithm": "SHA256"
     }
   }
   ```

3. **Hash Verification:**
   ```bash
   # Check hash manually (für forensische Zwecke)
   cat evidence.json | jq -S '.investigation' | sha256sum
   # Sollte matchen mit evidence_chain.hash
   ```

**✅ Test bestanden wenn:** Hash vorhanden und JSON valid!

---

### **C) CSV Export prüfen**

1. **Öffne** `export.csv` in Excel
2. **Prüfe Columns:**
   ```
   ✅ Transaction ID
   ✅ Timestamp
   ✅ From Address
   ✅ To Address
   ✅ Amount (BTC)
   ✅ Transaction Hash
   ✅ Labels
   ```

3. **Sortieren/Filtern testen:**
   ```
   ✅ Nach Amount sortieren
   ✅ Nach Timestamp filtern
   ✅ Excel Formeln funktionieren
   ```

**✅ Test bestanden wenn:** CSV in Excel nutzbar!

---

## Test 5: Performance Check (1 Min)

### **A) Investigation Speed**

**Test verschiedene Address-Counts:**
```
1 Address: < 30s ✅
5 Addresses: < 45s ✅
10 Addresses: < 60s ✅
```

### **B) Graph Load Speed**

**Test verschiedene Depths:**
```
Depth 1: < 2s ✅
Depth 2: < 5s ✅
Depth 3: < 10s ✅
```

### **C) Report Generation Speed**

**Test Report-Formate:**
```
HTML: < 1s ✅
JSON: < 500ms ✅
CSV: < 500ms ✅
```

**✅ Test 5 bestanden wenn:** Alle Zeiten unter Limits!

---

## Fehlerbehandlung Tests

### **A) Invalid Input**

**Test mit ungültigen Daten:**
```bash
# Leere Addresses
curl -X POST .../investigate -d '{"addresses": []}'
→ 400 Bad Request ✅

# Ungültige Bitcoin-Adresse
curl -X POST .../investigate -d '{"addresses": ["invalid"]}'
→ 400 Bad Request ✅

# Nicht existierende Investigation ID
curl .../investigations/fake-id/report.pdf
→ 404 Not Found ✅
```

**✅ Test bestanden wenn:** Korrekte Error-Responses!

---

### **B) Permission Tests**

**Test ohne Token:**
```bash
curl http://localhost:8000/api/v1/bitcoin-investigation/investigate
→ 401 Unauthorized ✅
```

**Test mit Community Plan (sollte blockieren):**
```bash
# User mit Community Plan
curl ... -H "Authorization: Bearer COMMUNITY_TOKEN"
→ 403 Forbidden (requiredPlan: pro) ✅
```

**✅ Test bestanden wenn:** Plan-Gates funktionieren!

---

## Checkliste - Alles Fertig?

### **Backend:**
- [ ] Bitcoin Investigation Service läuft
- [ ] Report Generator generiert PDFs
- [ ] Report Generator generiert JSONs
- [ ] Report Generator generiert CSVs
- [ ] API Endpoints antworten (200 OK)
- [ ] Investigations werden gespeichert
- [ ] SHA256 Hashes generiert

### **Frontend:**
- [ ] Bitcoin Investigation Page lädt
- [ ] Form validiert Input
- [ ] Results werden angezeigt
- [ ] Download-Buttons funktionieren
- [ ] Navigation zum Graph funktioniert
- [ ] Graph lädt und ist interaktiv

### **Integration:**
- [ ] Investigation → Graph Navigation
- [ ] Report Download aus Frontend
- [ ] Evidence Hash verifizierbar
- [ ] CSV Excel-kompatibel
- [ ] PDF druckbar

### **Qualität:**
- [ ] Reports sehen professionell aus
- [ ] Keine Fehler in Console
- [ ] Performance unter Limits
- [ ] Error-Handling funktioniert
- [ ] Plan-Gates aktiv

---

## 🎉 Success Criteria

**ALLES FUNKTIONIERT wenn:**

✅ **Investigation durchführbar** (30-60s)
✅ **Reports downloadbar** (PDF/JSON/CSV)
✅ **Graph interaktiv** (Zoom, Pan, Expand)
✅ **Evidence Hash generiert** (SHA256)
✅ **Court-Admissible Format** (professionelle PDFs)
✅ **Performance gut** (< 60s Investigations)
✅ **Error-Handling robust** (korrekte HTTP Codes)
✅ **Plan-Gates funktional** (Pro+ required)

---

## 🚨 Troubleshooting

### Problem: Investigation dauert zu lange (>2 Min)

**Ursache:** Zu viele Adressen oder sehr alte Adressen

**Lösung:**
- Reduziere Anzahl Adressen (<10)
- Verkürze Zeitraum (z.B. nur 2023-2024)
- Deaktiviere optionale Features (Mixer-Analysis)

---

### Problem: Report Download schlägt fehl

**Ursache:** Investigation nicht im Store

**Lösung:**
```bash
# Check ob Investigation gespeichert ist
curl http://localhost:8000/api/v1/bitcoin-investigation/investigations/{id}
```

---

### Problem: Graph lädt nicht

**Ursache:** Ungültige Adresse oder kein Plan

**Lösung:**
- Validiere Adresse (bc1q..., 1..., 3... für Bitcoin)
- Check User Plan (muss Pro+ sein)
- Check Browser Console für Errors

---

## 📊 Expected Results - Beispiel

### **Sample Investigation Result:**
```json
{
  "investigation_id": "btc-inv-1234567890",
  "status": "completed",
  "execution_time_seconds": 42.3,
  "transactions": {
    "total_count": 856,
    "total_volume_btc": 45.67,
    "unique_addresses": 123
  },
  "clustering": {
    "total_clusters": 5,
    "clustered_addresses": 34
  },
  "mixer_analysis": {
    "mixer_interactions": 2,
    "mixers_detected": ["wasabi", "samourai"]
  },
  "flow_analysis": {
    "exit_points": [
      {
        "address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
        "exit_type": "exchange",
        "total_outflow_btc": 25.4,
        "labels": ["Binance", "exchange"]
      }
    ],
    "dormant_funds": [
      {
        "address": "3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy",
        "balance_btc": 12.3,
        "dormant_days": 456
      }
    ],
    "total_exit_volume_btc": 25.4,
    "total_dormant_btc": 12.3
  },
  "summary": "Investigation of 2 Bitcoin addresses identified 856 transactions over 4 years...",
  "recommendations": [
    "Subpoena Binance for KYC data of exit address 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
    "Monitor dormant address 3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy for activity",
    "Follow up on Wasabi mixer interactions (2 detected)"
  ]
}
```

---

## ✅ Final Checklist

- [ ] Alle 5 Tests durchgeführt
- [ ] Alle Reports heruntergeladen
- [ ] PDF druckbar getestet
- [ ] Evidence Hash validiert
- [ ] Graph interaktiv bestätigt
- [ ] Performance akzeptabel
- [ ] Error-Handling funktioniert

**Wenn alle Checkboxen ✅ → SYSTEM IST PERFECT! 🎉**

---

**Viel Erfolg beim Testen!** 🚀

Die Plattform ist jetzt produktionsreif für echte Anwälte und Strafverfolgungsbehörden!
