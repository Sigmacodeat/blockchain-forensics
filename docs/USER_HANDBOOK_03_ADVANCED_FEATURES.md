# 📘 Benutzerhandbuch Teil 3: Advanced Features

> **Pro-Tools für Power-User - Graph Explorer, Correlation, Wallet Scanner**

---

## 🕸️ 1. Graph Explorer (Investigator)

### Was ist der Graph Explorer?

**Visualisiere komplexe Netzwerke interaktiv - wie eine Google Maps für Blockchain-Transaktionen.**

### 🎯 Wann nutzen?

| Szenario | Warum Graph? |
|----------|-------------|
| **Komplexe Strukturen** | 100+ Adressen übersichtlich |
| **Pattern-Erkennung** | Cluster, Hubs visuell sehen |
| **Präsentationen** | Impressive visuals für Meetings |
| **Network-Analyse** | Wer ist zentral? Wer ist Intermediär? |

### 📖 Schritt-für-Schritt

#### 1. Graph öffnen
**3 Wege:**
- Dashboard → Graph Explorer
- Nach Trace → "🕸️ Open in Graph"
- URL: `/investigator?address=0x1234...`

#### 2. Graph verstehen

**Node-Typen:**
```
●  Source (Grün) - Startpunkt
●  Mixer (Rot) - Tornado Cash, etc.
●  Sanctioned (Schwarz) - OFAC, UN, EU
●  Exchange (Blau) - Binance, Coinbase
●  DeFi (Lila) - Uniswap, Aave
●  Unknown (Grau) - Normale Wallets
```

**Edge-Typen:**
```
──── Normal Transaction
═══ High-Value Transfer (>$100K)
···· Low-Value (Dust)
→→→ Bridge Transfer (Cross-Chain)
```

#### 3. Interaktive Features

**Zoom & Pan:**
- **Mausrad:** Zoom in/out
- **Drag:** Pan (verschieben)
- **Doppelklick:** Center auf Node

**Node-Actions:**
- **Click:** Details anzeigen
- **Right-Click:** Kontextmenü
- **Hover:** Quick-Info

**Layout-Optionen:**
```
┌─────────────────────────┐
│ Layout: [Force ▼]      │
│ • Force-Directed        │
│ • Hierarchical          │
│ • Circular              │
│ • Grid                  │
└─────────────────────────┘
```

#### 4. Filter & Suche

**Filter Panel:**
```
🎛️ FILTERS
☑ Show Mixers
☑ Show Sanctioned
☐ Show DeFi
☐ Hide Unknown (< $1K)

Risk Range: [70] ──●── [100]

Transaction Value:
Min: [$1,000]  Max: [$∞]
```

**Search:**
```
🔍 Search Address
[0x1234...] → Highlights Node
```

#### 5. Advanced Analysis

**Clustering:**
```
[🔵 Auto-Cluster]
→ Findet Wallet-Gruppen
→ Colored by cluster
→ Export cluster-list
```

**Shortest Path:**
```
From: [Source Node]
To: [Target Node]
[Find Path] → Zeigt direktesten Weg
```

**Centrality Analysis:**
```
[📊 Calculate Centrality]
→ Betweenness (wer ist Intermediär?)
→ Degree (wer hat meiste Connections?)
→ PageRank (wer ist wichtigste Node?)
```

### 💡 Pro-Tipps

**Pattern Recognition:**
- **Hub-and-Spoke:** Zentrale Node = Mixer/Exchange
- **Chain:** Sequentielle Transfers = Layering
- **Star:** Multiple Inputs → One Output = Collection

**Performance:**
```
<100 Nodes: Smooth
100-500 Nodes: Good
500-1000 Nodes: Filter empfohlen
>1000 Nodes: Use Clustering
```

**Export:**
- PNG/SVG: Für Reports
- JSON: Für weitere Analyse
- GraphML: Für Gephi/Cytoscape

---

## 🎯 2. Correlation Analysis

### Was ist Correlation?

**Finde versteckte Verbindungen zwischen scheinbar unabhängigen Wallets/Transaktionen.**

### 🎯 Use Cases

| Szenario | Was findest du? |
|----------|----------------|
| **Multi-Account Fraud** | Gleicher Besitzer, verschiedene Wallets |
| **Sybil Attacks** | Fake-Accounts Netzwerk |
| **Money Mule Networks** | Koordinierte Geldwäsche-Ringe |
| **Exchange Patterns** | Systematisches Wash-Trading |

### 📖 Correlation nutzen

#### 1. Analysis starten

**Navigation:** Dashboard → Correlation → New Analysis

**Input:**
```
┌────────────────────────────────────┐
│ 🎯 CORRELATION ANALYSIS            │
├────────────────────────────────────┤
│ Target Addresses (1-10):          │
│ • 0x1234...                        │
│ • 0x5678...                        │
│ • 0xAbCd...                        │
│ [+ Add Address]                    │
│                                      │
│ Analysis Type:                     │
│ ◉ Temporal (timing patterns)      │
│ ○ Behavioral (tx patterns)        │
│ ○ Network (shared connections)    │
│ ○ All (comprehensive)             │
│                                      │
│ Time Window:                       │
│ [Last 30 days ▼]                   │
│                                      │
│ [🚀 Start Analysis]                │
└────────────────────────────────────┘
```

#### 2. Ergebnisse interpretieren

**Correlation Score:**
```
┌────────────────────────────────────┐
│ 📊 CORRELATION RESULTS             │
├────────────────────────────────────┤
│ Addresses Analyzed: 3              │
│ Correlation Score: 87/100          │
│ Confidence: HIGH                   │
│                                      │
│ 🔗 SHARED PATTERNS                 │
│ • Same funding source (95% match) │
│ • Similar tx timing (±5 mins)     │
│ • Shared intermediaries (12)      │
│ • Gas price patterns (98% match)  │
│                                      │
│ 🚨 RISK INDICATORS                 │
│ • Coordinated activity detected    │
│ • Likely same controller           │
│ • Potential Sybil network          │
└────────────────────────────────────┘
```

**Score-Bedeutung:**
- **0-30:** Keine Korrelation
- **31-60:** Möglicherweise verbunden
- **61-80:** Wahrscheinlich verbunden
- **81-100:** Sehr wahrscheinlich gleicher Besitzer

#### 3. Detected Patterns

**Temporal Correlation:**
```
Timeline-View:
0x1234... ───●────────●─────●───
0x5678... ─────●────────●─────●─
0xAbCd... ───────●────────●─────●

→ Alle 3 Wallets aktiv innerhalb 5-Min-Fenster
→ 87% Timing-Overlap
→ Wahrscheinlich koordiniert
```

**Behavioral Patterns:**
```
Shared Behaviors:
• Gleiche Gas Price Strategy
• Ähnliche Tx-Amounts ($1,000 ±$10)
• Identische Nonce-Gaps
• Same Contract Interactions
```

**Network Patterns:**
```
Shared Connections:
• Common Funding: 0xSource...
• Shared Intermediary: 0xMixer...
• Same Exchange Deposits: Binance Wallet #7
```

#### 4. Actions

| Action | Wann nutzen? |
|--------|--------------|
| **💾 Save as Case** | High Correlation (>70) |
| **🏷️ Tag as Cluster** | Gleicher Besitzer vermutet |
| **📊 Generate Report** | Für Investigation-Team |
| **🔍 Extend Analysis** | Mehr Adressen hinzufügen |

### 💡 Pro-Tipps

**Best Practices:**
```
1. Start mit 2-3 verdächtigen Wallets
2. Use "All" Analysis für erste Übersicht
3. Wenn Score >70: Deep-Dive mit spezifischen Types
4. Cross-Check mit Graph Explorer
```

**False Positives vermeiden:**
```
❌ FALSCH: "Beide nutzen Binance" → Zu generisch
✅ RICHTIG: "Gleiche Funding-Source + Timing" → Stark
```

---

## 👁️ 3. Wallet Scanner

### Was ist der Wallet Scanner?

**Prüfe Seeds, Private Keys oder Adressen auf Risiken - OHNE sie der Blockchain zu exposen.**

### 🎯 Use Cases

| Szenario | Was machst du? |
|----------|----------------|
| **Due Diligence** | Kunde gibt Wallet an |
| **Asset Recovery** | Beschlagnahmte Seeds prüfen |
| **Compliance Check** | Internal Wallet Audit |
| **Security Audit** | Company Wallets scannen |

### 📖 Scanner nutzen

#### 1. Tab auswählen

**4 Modi:**

| Tab | Input | Output |
|-----|-------|--------|
| **Seed Phrase** | 12/24 Wörter | Alle derived Adressen |
| **Private Key** | Hex Private Key | 1 Adresse + Balances |
| **Addresses** | Liste von Adressen | Risk-Scores |
| **Bulk** | CSV-Upload | Batch-Report |

#### 2. Seed Phrase Scan

**Input:**
```
┌────────────────────────────────────┐
│ 🌱 SEED PHRASE SCANNER             │
├────────────────────────────────────┤
│ Enter Seed (12 or 24 words):      │
│ ┌──────────────────────────────┐  │
│ │ abandon abandon abandon ...  │  │
│ └──────────────────────────────┘  │
│                                      │
│ ⚙️ OPTIONS                         │
│ Chains: [Select Multiple ▼]       │
│ ☑ Ethereum                         │
│ ☑ Bitcoin                          │
│ ☑ Polygon                          │
│                                      │
│ Derivation Depth: [20]            │
│                                      │
│ [🔍 Scan]                          │
└────────────────────────────────────┘
```

**⚠️ Security:**
```
🔒 PRIVACY GUARANTEE
• Seeds/Keys NEVER logged
• NEVER sent to external APIs
• Memory wiped after scan
• Zero-Trust architecture
```

**Output:**
```
┌────────────────────────────────────┐
│ 📊 SCAN RESULTS                    │
├────────────────────────────────────┤
│ Addresses Found: 20                │
│ Total Balance: $45,670             │
│ Highest Risk: 78/100               │
│                                      │
│ 🔍 DETAILED ADDRESSES              │
│ ┌────────────────────────────────┐ │
│ │ m/44'/60'/0'/0/0 (ETH)         │ │
│ │ 0x1234...                      │ │
│ │ Balance: $12,500               │ │
│ │ Risk: 🟢 15/100                │ │
│ │ [Details] [Trace]              │ │
│ └────────────────────────────────┘ │
│ ┌────────────────────────────────┐ │
│ │ m/44'/60'/0'/0/5 (ETH)         │ │
│ │ 0x5678...                      │ │
│ │ Balance: $500                  │ │
│ │ Risk: 🔴 78/100                │ │
│ │ ⚠️ Mixer Activity Detected     │ │
│ │ [Details] [Trace]              │ │
│ └────────────────────────────────┘ │
│                                      │
│ [📄 Export CSV] [�� PDF Report]    │
└────────────────────────────────────┘
```

#### 3. Zero-Trust Address Scan

**Use Case:** Kunde gibt Liste von Adressen

**Input:**
```
Chain          Address
ethereum       0x1234...
bitcoin        bc1q...
polygon        0x5678...
solana         7EqQd...
```

**Output:** Für jede Adresse:
- Current Balance
- Transaction Count
- Risk Score
- Labels (Exchange, Mixer, etc.)
- Sanctions Status

#### 4. Bulk Scan (CSV)

**CSV-Format:**
```csv
chain,address
ethereum,0x1234...
bitcoin,bc1q...
polygon,0x5678...
```

**Live-Progress via WebSocket:**
```
🔄 Scanning...
✅ 1/100 - ethereum:0x1234... (Risk: 15)
✅ 2/100 - bitcoin:bc1q... (Risk: 8)
⚠️ 3/100 - polygon:0x5678... (Risk: 85 - MIXER!)
...
✅ 100/100 - Complete!
```

### 💡 Pro-Tipps

**Security Best Practices:**
```
1. Use offline machine für Seeds (wenn möglich)
2. Clear Browser nach Scan (Ctrl+Shift+Del)
3. Use Addresses-Tab wenn möglich (Zero-Trust)
4. NEVER scan Seeds auf Public WiFi
```

**Performance:**
```
Seed Scan (20 derivations): ~10s
Address Scan: <2s pro Adresse
Bulk Scan: ~2s pro Adresse
```

**Reports:**
- **CSV:** Für Excel-Analyse
- **PDF:** Gerichtsfest mit SHA256-Hashes
- **Evidence JSON:** Tamper-Proof für Behörden

---

## 🚨 4. Risk Copilot

### Was ist Risk Copilot?

**Live AI-Risiko-Bewertung für jede Adresse - wie ein Co-Pilot neben dir.**

### 🎯 Features

**Real-Time Scoring:**
```
┌────────────────────────────────────┐
│ 🚨 RISK COPILOT                    │
│ 0x742d35Cc6634C0532925a3b844Bc9e... │
├────────────────────────────────────┤
│ Risk Score: 78/100 🟠              │
│ Status: HIGH RISK                  │
│                                      │
│ 🏷️ TOP CATEGORIES                  │
│ • Mixer Activity (95)              │
│ • Sanctions Contact (85)           │
│                                      │
│ 💡 KEY REASONS                      │
│ • Used Tornado Cash (3x)           │
│ • Sent to OFAC-listed wallet       │
│ • High-value transactions          │
│                                      │
│ ⚠️ RISK FACTORS                    │
│ • Frequent mixer usage             │
│ • No KYC trail                     │
│ • Suspicious timing patterns       │
└────────────────────────────────────┘
```

### 📖 Wo verfügbar?

**3 Integrationen:**

1. **Trace Page:** Für Source-Address (full-view)
2. **Investigator:** Neben jeder Node (compact)
3. **Address Details:** Header (badge)

### 💡 Variants

| Variant | Wo? | Info-Level |
|---------|-----|------------|
| **Badge** | Address-Liste | Score + Icon |
| **Compact** | Graph Nodes | Score + Top-2 Categories |
| **Full** | Trace-Page | Complete Details |

### 🛠️ Features

**Live-Updates:**
- SSE-Streaming (Sub-Second)
- Auto-Refresh on Changes
- Disconnect-Detection

**Adaptive Colors:**
- 🟢 Green (0-30): Safe
- 🟡 Yellow (31-60): Caution
- 🟠 Orange (61-80): High Risk
- 🔴 Red (81-100): Critical

**Actions:**
```
[📊 Full Analysis] → Detailed Report
[🔍 Trace] → Start Trace
[💾 Save] → Add to Case
```

---

**➡️ Weiter zu [Teil 4: AI & Intelligence](USER_HANDBOOK_04_AI_INTELLIGENCE.md)**
