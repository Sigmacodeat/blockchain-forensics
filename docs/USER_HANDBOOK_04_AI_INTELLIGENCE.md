# 📘 Benutzerhandbuch Teil 4: AI & Intelligence

> **KI-Power für Ermittlungen - AI Agent, Threat Intel, Dark Web**

---

## 🤖 1. AI Agent - Dein Forensik-Assistent

### Was ist der AI Agent?

**Dein intelligenter Co-Pilot für Blockchain-Ermittlungen - beantwortet Fragen, führt Analysen durch, generiert Reports.**

### 🎯 Was kann der Agent?

| Aufgabe | Beispiel-Befehl |
|---------|----------------|
| **Traces durchführen** | "Analysiere 0x1234... auf Mixer" |
| **Sanctions-Checks** | "Check gegen alle Sanctions-Listen" |
| **Reports generieren** | "Erstelle PDF für Gericht" |
| **Pattern-Erkennung** | "Finde alle Tornado Cash Exits" |
| **Multi-Chain-Analysis** | "Verfolge über Bridges" |
| **Risk-Assessment** | "Was sind die Top-Risiken?" |

### 📖 AI Agent nutzen

#### 1. Agent öffnen

**3 Wege:**
- Dashboard → AI Agent
- Forensik Control Center (Dashboard-Chat)
- Keyboard: `Ctrl + Alt + A`

#### 2. Erste Schritte

**Einfache Fragen:**
```
User: "Was kann ich mit dieser Plattform machen?"

AI Agent: ��
Ich kann dir bei Blockchain-Ermittlungen helfen:

🔍 Transaction Tracing
📊 Risk Analysis
🚨 Sanctions Screening
🕸️ Network Visualization
📄 Report Generation

Welche Adresse möchtest du untersuchen?
```

#### 3. Forensik-Commands

**Beispiel 1: Quick Analysis**
```
User: "Analysiere 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

AI Agent: 🔧 Starting trace...
✅ Trace complete

🚨 KRITISCHE FINDINGS:
• Risk Score: 78/100 (HIGH)
• 2x Tornado Cash Mixers
• 1x OFAC Sanctions Match
• $2.4M Total Volume

📊 Empfehlung:
• Sofort melden an Compliance
• Vertiefte Untersuchung nötig
• Case erstellt: AUTO-2024-0015

[📄 Full Report] [🕸️ Graph View]
```

**Beispiel 2: Multi-Sanctions Check**
```
User: "Check 0x1234... gegen alle Sanctions"

AI Agent: 🔧 Checking 9 sanctions lists...

✅ RESULTS:
• OFAC (US): ❌ Not listed
• UN Security Council: ❌ Not listed
• EU Sanctions: ✅ MATCH!
  - Added: 2023-11-15
  - Reason: Money Laundering
  - Reference: EU 2023/12345

• UK HM Treasury: ❌ Not listed
• Canada OSI: ❌ Not listed
...

🚨 CRITICAL: EU Sanctions Match!
→ Immediate action required
→ Evidence saved: sanctions_match.json
```

**Beispiel 3: Pattern-Detection**
```
User: "Finde alle Adressen die Tornado Cash nutzen"

AI Agent: 🔧 Scanning network...

🌪️ TORNADO CASH ACTIVITY DETECTED:

High Confidence (95%+):
• 0x1234... - 3 deposits, $500K
• 0x5678... - 7 deposits, $1.2M
• 0xAbCd... - 1 deposit, $200K

Medium Confidence (75-95%):
• 0xDeFa... - Timing suspicious
• 0x9876... - Amount patterns

📊 Total: 5 addresses, $1.9M volume

[Save as Case] [Generate Report]
```

#### 4. Command Palette (Dashboard-Chat)

**Quick Actions via Templates:**

```
Ctrl+K → Command Palette
┌────────────────────────────────────┐
│ 🔍 Quick Forensik-Commands         │
├────────────────────────────────────┤
│ → High-Risk Trace                  │
│ → Mixer Activity Check             │
│ → Daily Summary                    │
│ → Sanctions Screening              │
│ → Bridge Transfers                 │
│ → Active Cases                     │
└────────────────────────────────────┘
```

**Template: High-Risk Trace**
```
AI Agent (auto-filled):
"Starte High-Risk Trace für [Adresse]:
• Depth 5
• Focus: Mixers, Sanctions, Exchanges
• Generate court-ready report"
```

#### 5. Natural Language Tools

**Der Agent hat Zugriff auf 20+ Tools:**

| Tool-Kategorie | Tools |
|----------------|-------|
| **Tracing** | trace_address, bridge_lookup |
| **Risk** | risk_score, threat_intel_enrich |
| **Sanctions** | check_sanctions (9 Listen) |
| **Intelligence** | darkweb_query, community_reports |
| **Cases** | create_case, add_evidence |
| **Reports** | generate_pdf, export_csv |

**Beispiel-Flow:**
```
1. User fragt: "Analysiere 0x1234..."
2. Agent ruft: trace_address(0x1234...)
3. Agent sieht: Mixer gefunden
4. Agent ruft: check_sanctions(mixer_address)
5. Agent findet: OFAC-Match
6. Agent ruft: create_case(findings)
7. Agent antwortet mit Summary + Case-Link
```

### 💡 Pro-Tipps

**Effektive Prompts:**
```
✅ GUT: "Analysiere 0x1234... auf Mixer und Sanctions"
❌ SCHLECHT: "Was ist das?"

✅ GUT: "Erstelle Court-Ready Report für Case #7"
❌ SCHLECHT: "Report"

✅ GUT: "Finde alle Bridge-Transfers von Source"
❌ SCHLECHT: "Bridges"
```

**Multi-Step Analysen:**
```
1. "Trace 0x1234... Depth 3"
2. "Check gefundene Mixer gegen Sanctions"
3. "Finde Bridge-Exits"
4. "Continue Trace auf Polygon"
5. "Save all as Case: Operation X"
```

**Keyboard Shortcuts:**
- `Enter` → Send Message
- `Shift+Enter` → New Line
- `Ctrl+K` → Command Palette
- `Esc` → Close Chat

---

## 🚨 2. Threat Intelligence

### Was ist Threat Intel?

**Community-getriebene Threat-Datenbank + Automatische Feeds für aktuelle Scams, Hacks, Phishing.**

### 🎯 Features

#### A) Community Reports

**User können Threats melden:**
```
┌────────────────────────────────────┐
│ 🚨 SUBMIT THREAT REPORT            │
├────────────────────────────────────┤
│ Address: 0x1234...                 │
│                                      │
│ Threat Type:                       │
│ [Dropdown] Scam ▼                  │
│ • Scam/Phishing                    │
│ • Ransomware                       │
│ • Hack/Theft                       │
│ • Mixer/Laundering                 │
│                                      │
│ Description:                       │
│ ┌──────────────────────────────┐  │
│ │ Fake Airdrop, stole $50K     │  │
│ └──────────────────────────────┘  │
│                                      │
│ Evidence (optional):               │
│ [Upload Files]                     │
│                                      │
│ [📤 Submit Report]                 │
└────────────────────────────────────┘
```

**Reward System:**
- Verified Report → +10 Trust Score
- High-Value Intel → +50 Trust Score
- Top-Contributor → Badge

#### B) Threat Feeds (Auto)

**Integrierte Quellen:**
- **CryptoScamDB** - 50,000+ Scams
- **ChainAbuse** - Community Reports
- **Etherscan Labels** - Known Entities
- **DeFiLlama** - DeFi Protocols

**Auto-Update:** Alle 6 Stunden

#### C) Address Enrichment

**API-Endpoint:**
```
GET /api/v1/threat-intel/enrich?address=0x1234...

Response:
{
  "address": "0x1234...",
  "threat_score": 85,
  "labels": ["scam", "phishing"],
  "reports": 47,
  "first_seen": "2023-05-15",
  "sources": ["CryptoScamDB", "Community"],
  "risk_factors": [
    "Multiple scam reports",
    "Phishing website linked",
    "High-value thefts"
  ]
}
```

#### D) Statistics

**Dashboard:**
```
📊 THREAT INTEL STATS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Threats: 125,000+
Community Reports: 12,500
Top Threat: Scam/Phishing (45%)
Last Updated: 2 hours ago

🔥 HOT THREATS (Last 24h)
• 0xAbCd... - Fake Airdrop (+$200K)
• 0xDeFa... - Ponzi Scheme (+$1.5M)
• 0x9876... - NFT Phishing (+$50K)
```

### 💡 Use Cases

**Due Diligence:**
```
1. Check Address gegen Threat-DB
2. Review Community Reports
3. Assess Trust Score
4. Decision: Proceed or Block
```

**Investigation:**
```
1. Find Similar Threats
2. Track Scam Evolution
3. Identify Scam-Networks
4. Share Intel mit Team
```

---

## 🌐 3. Dark Web Monitoring

### Was ist Dark Web Monitoring?

**Automatisches Tracking von Darknet-Marketplaces, Foren, Ransom-Sites für Crypto-bezogene Intelligence.**

### 🎯 Monitored Sources

**4 Marketplace-Types:**
- Drugs/Illegal-Goods
- Stolen Data
- Hacking Services
- Cryptocurrency Services

**3 Forum-Types:**
- Hacking Forums
- Carding Forums
- Cryptocurrency Forums

### 📖 Features

#### A) IOC Extraction

**Was wird automatisch erkannt?**
```
Bitcoin Addresses: bc1q..., 1A1zP1...
Ethereum Addresses: 0x742d...
Monero Addresses: 4...
Onion URLs: http://...onion
Email Addresses: seller@...
Telegram Handles: @username
```

#### B) Keyword Alerts

**Setup:**
```
┌────────────────────────────────────┐
│ 🚨 DARK WEB ALERTS                 │
├────────────────────────────────────┤
│ Keywords (1 per line):             │
│ ┌──────────────────────────────┐  │
│ │ ransomware                   │  │
│ │ binance hack                 │  │
│ │ stolen database              │  │
│ └──────────────────────────────┘  │
│                                      │
│ Alert Channels:                    │
│ ☑ Email                            │
│ ☑ Dashboard Notification           │
│ ☐ Webhook                          │
│                                      │
│ [💾 Save Alerts]                   │
└────────────────────────────────────┘
```

**Alert-Example:**
```
🚨 NEW DARK WEB MENTION

Keyword: "binance hack"
Source: Hacking Forum XYZ
Posted: 2024-01-15 14:30 UTC
Excerpt: "Selling Binance KYC data, 
          10K users, Bitcoin only..."
Extracted IOCs:
• BTC: bc1q...
• Telegram: @seller123

[View Full] [Add to Case]
```

#### C) Ransom Tracking

**Monitor bekannte Ransom-Groups:**
```
📊 ACTIVE RANSOM CAMPAIGNS

LockBit 3.0:
• Active Victims: 47
• Bitcoin Addresses: 12
• Total Ransom: $4.2M
• Last Activity: 6 hours ago

Conti:
• Active Victims: 23
• Bitcoin Addresses: 8
• Total Ransom: $2.1M
• Last Activity: 1 day ago

[Track Payments] [Export Report]
```

#### D) Marketplace Analysis

**Statistics:**
```
🛒 MARKETPLACE ACTIVITY

Top Listings (Crypto-related):
1. Stolen Exchange Accounts - 234 listings
2. Crypto Mixing Services - 156 listings
3. Wallet Hacking Tools - 89 listings
4. KYC Data - 67 listings

Payment Methods:
• Bitcoin: 67%
• Monero: 28%
• Ethereum: 5%

[Detailed Report]
```

### 💡 Use Cases

**Ransomware Investigation:**
```
1. Identify Ransom Address
2. Track on Dark Web Posts
3. Find Group Attribution
4. Monitor Payment Activity
5. Coordinate Takedown
```

**Stolen Data Tracking:**
```
1. Monitor for Company Name
2. Alert on Data Leaks
3. Track Seller Wallets
4. Prevent Further Sales
```

**⚠️ Legal Notice:**
```
Dark Web Monitoring für:
✅ Law Enforcement
✅ Authorized Investigations
✅ Threat Intelligence
❌ Illegal Activities
```

---

## 🎯 4. Intent Detection

### Was ist Intent Detection?

**AI erkennt automatisch, was du vorhast und bietet passende Actions an.**

### 🎯 Detected Intents

| User-Input | Detected Intent | Action |
|------------|----------------|--------|
| "0x1234..." | Ethereum Address | → Trace vorschlagen |
| "bc1q..." | Bitcoin Address | → Bitcoin Trace |
| "7EqQd..." | Solana Address | → Solana Trace |
| "Case #7" | Case Reference | → Open Case |
| "Tornado Cash" | Mixer Query | → Mixer Analysis |

### 📖 Beispiele

**Auto-Suggestions:**
```
User: "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

AI Agent:
🤖 Ethereum-Adresse erkannt!

Möchtest du:
• 🔍 Trace starten (Depth 3)
• 📊 Risk Analysis
• 🚨 Sanctions Check
• 💾 Add to Case

[Trace starten] [Mehr Optionen]
```

**Multi-Chain Detection:**
```
User: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"

AI Agent:
🤖 Bitcoin-Adresse erkannt!

💡 TIPP: Bitcoin-Support ist aktiv!

Möchtest du:
• 🔍 Bitcoin Trace (UTXO)
• 📊 Address Details
• 🔗 Check for BTC Bridges

[Bitcoin Trace starten]
```

### 💡 Features

**Smart Context:**
```
Wenn du bist auf:
• /trace → Suggest adding to trace
• /cases → Suggest creating case
• /investigator → Suggest graph view
```

**Auto-Navigation:**
```
User: "Trace 0x1234..."

AI Agent:
🤖 Navigating zu /trace...
✅ Address pre-filled
🚀 Ready to start!

[Start Trace]
```

---

**➡️ Weiter zu [Teil 6: Best Practices](USER_HANDBOOK_06_BEST_PRACTICES.md)**
