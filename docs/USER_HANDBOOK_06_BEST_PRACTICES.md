# 📘 Benutzerhandbuch Teil 6: Best Practices

> **Praxis-Guide - Use Cases, Tipps, Troubleshooting**

---

## 📚 1. Häufige Use Cases

### 🦠 Use Case 1: Ransomware-Ermittlung

**Szenario:** Unternehmen zahlt $500K Bitcoin-Lösegeld, Spur verfolgen.

**Workflow:**
```
1️⃣ INITIAL TRACE
   • Copy Bitcoin-Adresse aus Ransom-Note
   • Dashboard → Transaction Tracing
   • Chain: Bitcoin, Depth: 5
   • ✅ Filter: Mixers, Exchanges
   
2️⃣ PATTERN RECOGNITION
   • Trace zeigt: 3 Hops → Mixer (Blender.io)
   • Save as Case: "Ransomware-2024-001"
   • Tag: #ransomware #lockbit #urgent
   
3️⃣ MIXER ANALYSIS
   • AI Agent: "Analyze Mixer exits"
   • Findet: 47 Exit-Addresses
   • 12 davon → Binance Deposits
   
4️⃣ EXCHANGE LIAISON
   • Generate Court-Ready PDF
   • Contact Binance Legal mit Report
   • Request KYC freeze
   
5️⃣ MONITORING
   • Setup Alert: Wenn Funds move
   • Dark Web: Monitor Ransom-Group
   • Regular Updates im Case
```

**Ergebnis:**
- ✅ 7 von 12 Binance-Accounts frozen
- ✅ $380K recovered
- ✅ LEA Coordination via Case-Sharing

**Tools genutzt:**
- Transaction Tracing
- Cases Management
- AI Agent
- Dark Web Monitoring
- Alerts

---

### 💰 Use Case 2: Exchange-Hack Investigation

**Szenario:** $2.4M gestohlen von Exchange, Täter identifizieren.

**Workflow:**
```
1️⃣ INITIAL ANALYSIS
   • Theft-Address: 0x742d...
   • Transaction Tracing: Depth 7
   • Graph Explorer: Visualize Network
   
2️⃣ CLUSTERING
   • Graph → Auto-Cluster
   • Findet: 8 Wallets gleicher Controller
   • Correlation Analysis: 94% Score
   
3️⃣ MULTI-CHAIN TRACKING
   • Detect: Polygon Bridge used
   • Continue Trace on Polygon
   • Detect: Arbitrum Bridge
   • Continue Trace on Arbitrum
   
4️⃣ MIXER DEMIXING
   • Tornado Cash detected
   • Advanced: Demixing Analysis
   • Findet: Likely Exit-Addresses (65% confidence)
   
5️⃣ SANCTIONS CHECK
   • Multi-Sanctions: All 9 Lists
   • Match: 1 OFAC Address
   • ✅ Critical Finding!
   
6️⃣ EVIDENCE PACKAGE
   • Export: Court-Ready PDF
   • Export: CSV (all addresses)
   • Export: Evidence ZIP (with SHA256)
   • Share mit Law Enforcement
```

**Timeline:**
- Day 1: Theft detected, trace started
- Day 2: Bridges followed, mixer found
- Day 3: OFAC match, LEA contacted
- Week 2: 3 suspects identified via KYC
- Month 3: $1.8M recovered

**Tools genutzt:**
- Transaction Tracing
- Graph Explorer
- Bridge Detection
- Correlation Analysis
- Multi-Sanctions
- Cases Management

---

### 🎣 Use Case 3: Phishing/Scam Analysis

**Szenario:** Fake Airdrop-Website, 500 Opfer, $200K gestohlen.

**Workflow:**
```
1️⃣ VICTIM REPORTS
   • Community: 47 Threat Reports
   • Addresses: 500 victim wallets
   • Scammer Wallet: 0xScam...
   
2️⃣ BULK ANALYSIS
   • Wallet Scanner: Bulk-Scan (CSV)
   • 500 victim addresses
   • Total Loss: $200K confirmed
   
3️⃣ SCAMMER TRACE
   • Trace 0xScam...: Depth 5
   • Pattern: Funds → DEX → Mixer → Exchange
   • Graph: Hub-and-Spoke Pattern
   
4️⃣ THREAT INTEL
   • Submit Threat Report
   • Share mit Community
   • Dark Web: Check for Scammer-Ads
   
5️⃣ TAKEDOWN
   • Report Website to Registrar
   • Report to Etherscan (Phishing Label)
   • Contact Exchanges für Account-Freeze
   
6️⃣ VICTIM NOTIFICATION
   • Export Victim-Liste (CSV)
   • Automated Emails via API
   • Provide Evidence für Claims
```

**Outcome:**
- ✅ Website taken down (Day 2)
- ✅ Etherscan Phishing-Label added
- ✅ 2 Exchange-Accounts frozen
- ✅ $45K recovered für Victims
- ✅ Community-Warning published

**Tools genutzt:**
- Threat Intelligence
- Wallet Scanner (Bulk)
- Transaction Tracing
- Community Reports
- Graph Explorer

---

### 🏛️ Use Case 4: Asset Recovery für Gericht

**Szenario:** Court-Order für Asset-Freeze, Full-Audit required.

**Workflow:**
```
1️⃣ COMPREHENSIVE TRACE
   • Source: 0xDefendant...
   • Depth: 10 (maximize coverage)
   • All Chains: Check Bridges
   • Time Range: Full History
   
2️⃣ EVIDENCE COLLECTION
   • Every Transaction: Screenshot
   • Every Transfer: SHA256-Hash
   • Every Address: Risk-Score
   • Chain-of-Custody: Timestamped
   
3️⃣ LEGAL DOCUMENTATION
   • Generate: Court-Ready PDF (50 pages)
   • Include: All Evidence Files
   • Include: Expert Declaration
   • Digital Signature: RSA-PSS
   
4️⃣ EXCHANGE COORDINATION
   • Identify: All Exchange-Deposits
   • Legal Requests: Freeze-Orders
   • KYC Data: Subpoena
   • Timeline: Document all responses
   
5️⃣ ONGOING MONITORING
   • Alerts: If any funds move
   • Weekly Reports: Status Updates
   • Court Filings: Evidence Updates
```

**Legal Package includes:**
```
📦 EVIDENCE PACKAGE
├── executive_summary.pdf
├── detailed_analysis.pdf (50 pages)
├── transaction_list.csv (2,341 rows)
├── evidence/
│   ├── blockchain_screenshots/ (234 files)
│   ├── exchange_responses/ (12 files)
│   └── expert_declarations/ (3 files)
├── signatures/
│   ├── sha256_manifest.txt
│   └── rsa_signature.sig
└── chain_of_custody.json
```

**Admissibility:**
- ✅ Tamper-Proof (SHA256)
- ✅ Timestamped (Blockchain)
- ✅ Expert-Verified
- ✅ Court-Accepted Format

---

### 💼 Use Case 5: Compliance/AML Due Diligence

**Szenario:** New Customer Onboarding, KYC-Check required.

**Workflow:**
```
1️⃣ CUSTOMER SUBMITS
   • Wallet Address: 0xCustomer...
   • Chain: Ethereum
   • Purpose: Business Account
   
2️⃣ AUTOMATED SCREENING
   • API Call: /api/v1/risk/stream
   • Risk Copilot: Live Score
   • Multi-Sanctions: All 9 Lists
   • Threat Intel: Community Reports
   
3️⃣ DECISION MATRIX
   Risk 0-30: ✅ AUTO-APPROVE
   Risk 31-60: ⚠️ MANUAL REVIEW
   Risk 61-80: 🔴 ENHANCED DUE DILIGENCE
   Risk 81-100: ❌ AUTO-REJECT
   
4️⃣ ENHANCED DD (if needed)
   • Full Trace: Depth 5
   • Source of Funds: Analysis
   • Correlation: Check related wallets
   • Interview: Request explanation
   
5️⃣ DOCUMENTATION
   • Save as Case: "KYC-Customer-12345"
   • Export: Compliance-Report
   • Archive: 7-year retention
   • Audit-Trail: All decisions logged
```

**Automation:**
```javascript
// API Integration
const riskScore = await checkAddress("0xCustomer...");

if (riskScore < 30) {
  return { decision: "APPROVED", reason: "Low Risk" };
} else if (riskScore < 60) {
  return { decision: "REVIEW", reason: "Medium Risk" };
} else {
  return { decision: "REJECT", reason: "High Risk" };
}
```

**Performance:**
- Automated Screening: <5 seconds
- Manual Review: 2-4 hours
- Enhanced DD: 1-2 days
- False Positive Rate: <2%

---

## ⌨️ 2. Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + K` | Command Palette |
| `Ctrl + N` | New Trace |
| `Ctrl + Alt + C` | New Case |
| `Ctrl + Alt + A` | AI Agent |
| `Ctrl + S` | Save Current |
| `Esc` | Close Dialog |
| `?` | Show Help |

### Navigation

| Shortcut | Destination |
|----------|-------------|
| `G` then `H` | Home (Dashboard) |
| `G` then `T` | Tracing |
| `G` then `C` | Cases |
| `G` then `G` | Graph Explorer |
| `G` then `A` | AI Agent |

### Graph Explorer

| Shortcut | Action |
|----------|--------|
| `Space` + Drag | Pan |
| `Scroll` | Zoom |
| `Shift + Click` | Multi-Select |
| `Ctrl + F` | Search |
| `Ctrl + A` | Select All |
| `Delete` | Delete Selected |
| `Ctrl + Z` | Undo |

### AI Agent

| Shortcut | Action |
|----------|--------|
| `Enter` | Send Message |
| `Shift + Enter` | New Line |
| `↑` | Previous Command |
| `↓` | Next Command |
| `Esc` | Close Chat |

### Command Palette Templates

| Command | Description |
|---------|-------------|
| `high risk` | High-Risk Trace Template |
| `mixer` | Mixer Activity Check |
| `sanctions` | Full Sanctions Screening |
| `summary` | Daily Summary |
| `bridge` | Bridge Transfer Analysis |

---

## 🔧 3. Troubleshooting

### Problem: Trace zu langsam

**Symptom:** Trace dauert >2 Minuten

**Lösungen:**
```
1. Reduziere Depth: 3 statt 7
2. Reduziere Max Addresses: 50 statt 500
3. Use Filters: "High Value Only"
4. Check Internet: Blockchain-RPC erreichbar?
5. Try Different Time: Peak-Hours vermeiden
```

**Performance-Erwartungen:**
- Depth 2-3: <10s
- Depth 4-5: 10-30s
- Depth 6-7: 30s-2min
- Depth 8+: 2-5min

---

### Problem: Graph Explorer überladen

**Symptom:** 1000+ Nodes, Browser laggt

**Lösungen:**
```
1. Use Clustering:
   [Auto-Cluster] → Group by similarity
   
2. Filter aggressiv:
   ☑ Hide Low-Value (<$1K)
   ☑ Hide Unknown Wallets
   ☑ Show Only: Mixers + Exchanges
   
3. Increase Threshold:
   Risk > 70 only
   
4. Export & Analyze:
   Download CSV → Excel-Pivot
```

---

### Problem: AI Agent antwortet nicht

**Symptom:** Chat hängt, kein Response

**Checks:**
```
1. Check Backend:
   • Is backend running? (docker ps)
   • Logs: docker logs backend
   
2. Check Redis:
   • Redis container UP?
   • Connection OK?
   
3. Browser Console:
   • F12 → Console
   • Errors anzeigen?
   
4. Retry:
   • Reload Page (Ctrl+R)
   • Clear Cache (Ctrl+Shift+Del)
   • Try Different Browser
```

**Common Errors:**
- `429 Too Many Requests` → Wait 1 minute
- `500 Server Error` → Check Backend Logs
- `WebSocket Closed` → Reload Page

---

### Problem: Case wird nicht gespeichert

**Symptom:** "Save as Case" → Error

**Lösungen:**
```
1. Check Permissions:
   • Logged in?
   • Correct Plan? (Community+)
   
2. Check Input:
   • Title filled?
   • Description <5000 chars?
   • Valid Tags?
   
3. Network:
   • Backend erreichbar?
   • CORS Error? (F12 Console)
   
4. Database:
   • PostgreSQL running?
   • Disk space OK?
```

---

### Problem: Evidence-Upload schlägt fehl

**Symptom:** File-Upload hängt/Error

**Lösungen:**
```
1. File-Size:
   Max: 50MB
   → Compress large files
   
2. File-Type:
   Allowed: PDF, PNG, JPG, JSON, CSV, TXT
   → Convert if needed
   
3. Network:
   • Stable Connection?
   • Retry after timeout
   
4. Browser:
   • Modern Browser? (Chrome, Firefox, Edge)
   • JavaScript enabled?
```

---

## 💡 4. Performance-Optimierung

### Für Einzelnutzer

```
1. Browser:
   • Use Chrome/Firefox (latest)
   • Clear Cache wöchentlich
   • Disable unnecessary Extensions
   
2. Traces:
   • Start klein (Depth 2-3)
   • Iterativ erweitern
   • Use Filters!
   
3. Cases:
   • Archive alte Cases
   • Max 50 active Cases
   • Clean up regelmäßig
```

### Für Teams

```
1. Organization:
   • Klare Naming-Conventions
   • Shared Tags verwenden
   • Regular Case-Reviews
   
2. Collaboration:
   • Permissions klar definieren
   • Activity-Log monitoren
   • Weekly Sync-Meetings
   
3. Infrastructure:
   • Dedicated Redis
   • PostgreSQL optimieren
   • Load-Balancer für API
```

### Für Admins

```
1. Monitoring:
   • Prometheus Metrics
   • Grafana Dashboards
   • Alert-Rules setup
   
2. Database:
   • Regular Backups (täglich)
   • Index-Optimization
   • Partition große Tables
   
3. Scaling:
   • Horizontal: Kubernetes
   • Vertical: More RAM/CPU
   • CDN für Frontend
```

---

## 🎓 5. Weiterbildung & Support

### Ressourcen

| Typ | Link | Beschreibung |
|-----|------|--------------|
| 📹 **Videos** | `/docs/videos` | Tutorial-Videos |
| 📧 **Email** | support@platform.com | Technischer Support |
| 💬 **Chat** | Dashboard (unten rechts) | Live-Support |
| 🌐 **Forum** | community.platform.com | Community-Hilfe |
| 📚 **API Docs** | `/docs/API_REFERENCE.md` | Für Entwickler |
| 🎟️ **Tickets** | support.platform.com | Bug-Reports |

### Training

**Empfohlener Lernpfad:**

```
Woche 1: Basics
• Teil 1: Getting Started
• 10 Traces durchführen
• 3 Cases erstellen
• AI Agent testen

Woche 2-3: Advanced
• Teil 2-3 durcharbeiten
• Graph Explorer lernen
• Correlation nutzen
• Team-Features

Woche 4+: Mastery
• Teil 4-5 studieren
• API-Integration
• Custom Workflows
• Best Practices
```

### Certification (Optional)

```
📜 CERTIFIED BLOCKCHAIN FORENSIC ANALYST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Level 1: Basic (20h)
• Platform Basics
• Transaction Tracing
• Cases Management

Level 2: Advanced (40h)
• Graph Analysis
• AI Agent Mastery
• Multi-Chain Investigations

Level 3: Expert (80h)
• Complex Cases
• API Integration
• Expert Witness Testimony

Kontakt: training@platform.com
```

---

## 🎯 6. Quick-Reference Cheat-Sheet

```
┌──────────────────────────────────────────────────────────┐
│  🚀 BLOCKCHAIN FORENSICS - QUICK REFERENCE               │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  CORE WORKFLOWS                                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  1. Quick Analysis:  Dashboard → Trace → Save            │
│  2. Deep Dive:       Trace → Graph → Correlation         │
│  3. Investigation:   Case → Multiple Traces → Evidence   │
│  4. AI-Assisted:     Chat → Ask → Auto-Execute           │
│                                                            │
│  KEYBOARD SHORTCUTS                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Ctrl+K              Command Palette                      │
│  Ctrl+N              New Trace                            │
│  Ctrl+Alt+C          New Case                             │
│  Ctrl+Alt+A          AI Agent                             │
│  ?                   Help                                 │
│                                                            │
│  RISK SCORES                                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  0-30   🟢 Low       Normal Wallets                      │
│  31-60  🟡 Medium    Vorsicht geboten                    │
│  61-80  🟠 High      Analyse erforderlich                │
│  81-100 🔴 Critical  Sanctions/Mixer                      │
│                                                            │
│  ICONS                                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  🏦 Exchange   🌪️ Mixer   🚨 Sanctioned   �� DeFi       │
│  👤 Unknown    🔗 Bridge   💰 High-Value   📊 Report     │
│                                                            │
│  SUPPORT                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  📧 support@platform.com                                  │
│  💬 Chat (Dashboard unten rechts)                         │
│  🌐 community.platform.com                                │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

---

**🎉 GLÜCKWUNSCH!** Du hast das vollständige Handbuch durchgearbeitet!

**Nächste Schritte:**
1. ✅ Starte deine erste Investigation
2. ✅ Join die Community
3. ✅ Share deine Erfolge
4. ✅ Gib Feedback zum Handbuch

**Bei Fragen:** support@platform.com | +43 1 234 5678

**Viel Erfolg bei deinen Ermittlungen! 🚀🔍**
