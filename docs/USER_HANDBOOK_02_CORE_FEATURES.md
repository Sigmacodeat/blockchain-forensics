# 📘 Benutzerhandbuch Teil 2: Core Features

> **Meistere die Kernfunktionen - Transaction Tracing, Cases, Bridges**

---

## 🔍 1. Transaction Tracing

### Was ist Tracing?

**Verfolge Krypto-Geldflüsse durch die Blockchain wie ein Detektiv Geldspuren folgt.**

### 🎯 Häufige Use Cases

| Szenario | Ziel | Depth-Empfehlung |
|----------|------|------------------|
| 🦠 **Ransomware** | Lösegeld-Weg verfolgen | 3-5 |
| 💰 **Exchange-Hack** | Alle Hacker-Wallets finden | 4-6 |
| 🌪️ **Geldwäsche** | Mixer-Exit-Points | 5-7 |
| 🎣 **Betrug/Scam** | Wohin verschwanden Gelder? | 3-4 |
| 🏛️ **Asset Recovery** | Full-Audit für Gericht | 7+ |

### 📖 Schritt-für-Schritt

#### 1. Interface öffnen
**Navigation:** Dashboard → Transaction Tracing oder `/trace`

#### 2. Adresse eingeben
```
Source Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
Chain: Ethereum
```

**Supported Chains (35+):**
- **EVM:** Ethereum, Polygon, BSC, Arbitrum, Optimism, Base, Avalanche, zkSync...
- **UTXO:** Bitcoin, Litecoin, Bitcoin Cash, Zcash
- **Other:** Solana, Tron, Stellar, Ripple

#### 3. Parameter setzen

| Parameter | Wert | Bedeutung |
|-----------|------|-----------|
| **Depth** | 3-5 | Anzahl "Hops" |
| **Max Addresses** | 50-100 | Limit |
| **Direction** | Both | Ein- und ausgehend |
| **Min Value** | $100 | Filtert Dust |

**�� Pro-Tipp:** Start mit Depth 2 für Übersicht, dann selektiv tiefer!

#### 4. Ergebnisse verstehen

**Summary Card:**
```
📊 TRACE RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Addresses: 47
Total Transactions: 1,234
Total Volume: $2.4M USD

🚨 RISK SCORE: 78/100 (HIGH)
⚠️ 3 Sanctioned Addresses
🌪️ 2 Mixer Connections
💰 12 Exchange Deposits
```

**Risk Score Guide:**
- 🟢 **0-30** = Low (normale Wallets)
- 🟡 **31-60** = Medium (Vorsicht)
- 🟠 **61-80** = High (Analyse nötig)
- 🔴 **81-100** = Critical (Sanctions/Mixer)

**Address Types:**
- 🏦 = Exchange (Binance, Coinbase...)
- 🌪️ = Mixer (Tornado Cash...)
- 🚨 = Sanctioned (OFAC, UN, EU...)
- 🔷 = DeFi (Uniswap, Aave...)
- 👤 = Unknown Wallet

#### 5. Actions

| Button | Wann nutzen? |
|--------|--------------|
| 💾 **Save as Case** | Wichtige Findings |
| 📊 **Generate Report** | Für Behörden/Gericht |
| 🕸️ **Open in Graph** | Komplexe Strukturen |
| 🔗 **Check Bridges** | Multi-Chain-Verdacht |
| 🤖 **AI Analysis** | Schnelle Insights |

### 💡 Pro-Tipps

**Iteratives Tracing:**
```
1. Quick Scan: Depth 2 (Übersicht)
2. Deep Dive: Depth 5 für verdächtige Adressen
3. Final: Selective Deep-Traces
```

**Filter richtig nutzen:**
- AML: `☑ Sanctioned + Mixer`
- Asset Recovery: `☑ Exchanges`
- Scam: `☑ All Filters`

**Notes sofort hinzufügen:**
```
0x1234... - "Mixer-Exit, Hacker-Verdacht"
0x5678... - "Binance Deposit, KYC anfordern"
```

---

## 📁 2. Cases Management

### Was sind Cases?

**Deine digitalen Ermittlungsakten mit:**
- 🔍 Traces (mehrere Analysen)
- 📄 Evidence (tamper-proof)
- 📝 Timeline (automatisch)
- 👥 Team-Collaboration
- 🏷️ Tags & Organization

### 🎯 Wann Case erstellen?

| Szenario | Empfehlung |
|----------|------------|
| Einzelne Tx | ⚠️ Optional |
| Ransomware | ✅ JA (mehrere Zahlungen) |
| Exchange-Hack | ✅ JA (Team-Arbeit) |
| Gerichtsfall | ✅ JA (Dokumentation) |
| Ad-hoc Check | ❌ Nein |

### 📖 Case erstellen

#### 1. New Case Dialog
**3 Wege:**
- Dashboard → Cases → "➕ New Case"
- Nach Trace → "💾 Save as Case"
- Keyboard: `Ctrl + Alt + C`

#### 2. Details eingeben
```
Title: Operation Darkweb - Binance Hack 2024
Description: $2.4M theft, Tornado Cash usage
Tags: #hack, #mixer, #urgent, #fbi
Priority: Critical
Team: You, john@fbi.gov, sarah@europol.eu
```

**💡 Naming Best Practices:**
- ✅ "Operation [Name] - [Type] [Year]"
- ❌ "Case 1", "Test"

**Tag-Struktur:**
```
Typ: #ransomware, #hack, #scam
Entity: #binance, #tornado-cash
Status: #urgent, #pending
Team: #fbi, #europol
```

#### 3. Case Dashboard

**Was siehst du?**
```
📊 CASE STATS
• Traces: 7
• Addresses: 143
• Evidence: 12 files
• Risk (Avg): 78/100

🔍 RECENT TRACES
[Trace List mit Actions]

📄 EVIDENCE
• report.pdf (SHA256: a3f7...)
• screenshot.png
[+ Upload]

📝 TIMELINE
• Jan 15, 10:00 - Case created
• Jan 15, 14:30 - Trace #7 completed
[+ Add Note]
```

### 🛠️ Evidence Management

**Upload-Typen:**
- PDF Reports (für Gericht)
- Screenshots (Blockchain Explorer)
- JSON Data (Raw Traces)
- Emails (Korrespondenz)

**Tamper-Proof Security:**
```json
{
  "filename": "evidence.pdf",
  "sha256": "a3f7c2e8...",
  "uploaded_at": "2024-01-15T14:30:00Z",
  "uploaded_by": "max@investigator.com",
  "signature": "-----BEGIN SIGNATURE-----..."
}
```

**💡 Warum SHA256?**
- Beweist: Datei wurde NICHT verändert
- Gerichtsfest: Chain-of-Custody

### 👥 Team Collaboration

**Permissions:**

| Role | Traces | Evidence | Settings |
|------|--------|----------|----------|
| **Owner** | ✅ All | ✅ All | ✅ All |
| **Editor** | ✅ Create | ✅ Upload | ❌ No |
| **Viewer** | ✅ View | ✅ Download | ❌ No |

**Activity Log:**
```
Jan 15, 10:00 - Max created case
Jan 15, 14:30 - John added evidence
Jan 16, 09:00 - Sarah viewed trace #3
```

### 📊 Reports & Export

**Report-Typen:**

| Format | Inhalt | Use Case |
|--------|--------|----------|
| **PDF** | Court-Ready Report | Gericht, Behörden |
| **CSV** | Address-Liste | Excel-Analyse |
| **JSON** | Raw Data | Technische Teams |
| **ZIP** | Evidence Package | Behördenübergabe |

**PDF-Struktur:**
```
═══════════════════════════════════════
 FORENSIC INVESTIGATION REPORT
 
 Case: Operation Darkweb
 Date: January 16, 2024
═══════════════════════════════════════

EXECUTIVE SUMMARY
$2.4M theft, Tornado Cash, 3 OFAC addresses

KEY FINDINGS
1. Initial Theft: 1,234.5 ETH
2. Mixer Activity: Tornado Cash
3. Sanctions: 3 OFAC-listed wallets

DETAILED ANALYSIS
[Traces, Evidence, Timeline]

CHAIN OF CUSTODY
SHA256-verified, RSA-signed
═══════════════════════════════════════
```

---

## 🔗 3. Bridge Transfers

### Was sind Bridges?

**Cross-Chain Transfers - Kriminelle nutzen sie um Spuren zu verwischen:**

```
Ethereum (stolen) 
    ↓ Polygon Bridge
Polygon (new address)
    ↓ BSC Bridge  
BSC (cash out)
```

### 🎯 Warum wichtig?

**Problem:** Normale Traces stoppen an Chain-Grenzen!

**Lösung:** Bridge Detection findet Cross-Chain-Links automatisch.

### 📖 Bridge Detection nutzen

#### 1. Zugriff
**2 Wege:**
- Nach Trace → "�� Check Bridges"
- Dashboard → Bridge Transfers → Enter Address

#### 2. Ergebnisse

**Detected Bridges:**
```
🔗 BRIDGE TRANSFERS FOUND

Bridge #1: Polygon PoS Bridge
• Source (Ethereum): 0x1234...
• Dest (Polygon): 0x5678...
• Amount: $500K
• Time: 2024-01-15 10:30
• Confidence: 95%

Bridge #2: Arbitrum Bridge
• Source (Ethereum): 0xAbCd...
• Dest (Arbitrum): 0xDeF0...
• Amount: $300K
• Time: 2024-01-15 12:00
• Confidence: 88%
```

**Supported Bridges (20+):**
- Polygon PoS Bridge
- Arbitrum Bridge
- Optimism Gateway
- Base Bridge
- Avalanche Bridge
- Multichain (Anyswap)
- Synapse Protocol
- Stargate
- Wormhole

#### 3. Continue Tracing

**Workflow:**
```
1. Trace auf Ethereum → Bridge gefunden
2. "Continue on Polygon" klicken
3. Automatisches Trace auf Polygon
4. Repeat bis Cash-Out gefunden
```

### 💡 Pro-Tipps

**Multi-Chain Strategy:**
```
1. Start-Chain: Full Trace (Depth 5)
2. Find Bridges: Auto-Detection
3. Follow Chain: Continue Trace
4. Document: Save all in Case
```

**Confidence Score:**
- 90-100% = Sehr sicher
- 80-90% = Wahrscheinlich
- 70-80% = Möglich (manuell prüfen)

---

## 🔍 4. Address Details

### Deep-Dive in einzelne Adressen

**Zugriff:**
- Nach Trace → Klick auf Adresse
- Dashboard → Address Lookup
- URL: `/address/0x1234...`

### 📊 Was siehst du?

**Address Profile:**
```
┌─────────────────────────────────────────┐
│ 🏦 BINANCE DEPOSIT WALLET               │
│ 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb│
├─────────────────────────────────────────┤
│ Risk Score: 🟢 15/100 (LOW)             │
│ Type: Exchange Deposit                  │
│ Labels: Binance, Exchange, Known Entity │
│                                           │
│ 💰 BALANCE                               │
│ ETH: 123.45 ($246,900)                  │
│ USDT: 50,000                            │
│ USDC: 25,000                            │
│                                           │
│ 📊 STATISTICS                            │
│ • Total Transactions: 1,234             │
│ • Total Volume: $12.4M                  │
│ • First Seen: Jan 1, 2023               │
│ • Last Active: 2 hours ago              │
│                                           │
│ 🔗 CONNECTIONS                           │
│ • Sent to: 47 addresses                 │
│ • Received from: 89 addresses           │
│ • Mixer Contact: NO                     │
│ • Sanctioned Contact: NO                │
└─────────────────────────────────────────┘
```

### 🛠️ Available Actions

| Action | Beschreibung |
|--------|--------------|
| **🔍 Trace** | Start Trace von dieser Adresse |
| **📊 Risk Analysis** | Detailliertes Risk-Scoring |
| **🚨 Check Sanctions** | Alle 9 Listen prüfen |
| **🔗 Find Bridges** | Cross-Chain-Links |
| **💾 Add to Case** | Zu bestehendem Case |
| **🏷️ Add Label** | Eigenes Label |

### 💡 Use Cases

**Due Diligence:**
```
1. Kunde gibt Wallet an
2. Address Details öffnen
3. Check Risk Score
4. Check Sanctions
5. Generate Report
```

**Verdachtsprüfung:**
```
1. Verdächtige Adresse
2. Full Transaction History
3. Check alle Connections
4. Identify Patterns
5. Save as Case
```

---

**➡️ Weiter zu [Teil 3: Advanced Features](USER_HANDBOOK_03_ADVANCED_FEATURES.md)**
