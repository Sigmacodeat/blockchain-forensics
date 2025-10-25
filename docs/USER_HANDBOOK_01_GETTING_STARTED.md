# 📘 Benutzerhandbuch Teil 1: Getting Started

> **Willkommen bei der modernsten Blockchain-Forensik-Plattform!**

---

## 📋 Inhaltsverzeichnis

1. [Was ist diese Plattform?](#-was-ist-diese-plattform)
2. [5-Minuten Quickstart](#-5-minuten-quickstart)
3. [Dashboard Überblick](#-dashboard-überblick)
4. [Erste Schritte](#-erste-schritte)
5. [Pläne & Features](#-pläne--features)

---

## 🎯 Was ist diese Plattform?

### Dein All-in-One Tool für Blockchain-Forensik

Diese Plattform ist deine **komplette Lösung** für professionelle Krypto-Ermittlungen:

- 🔍 **Geldwäsche aufdecken** - Verfolge verdächtige Transaktionen über 35+ Blockchains
- 🚨 **Sanktions-Verstöße erkennen** - Screening gegen OFAC, UN, EU und 6 weitere Listen
- 🕵️ **Betrug identifizieren** - Erkenne Mixer, Scams, Hacks und illegale Aktivitäten
- 💼 **Compliance sicherstellen** - FATF Travel Rule, regulatorische Reports
- 🤖 **KI-gestützt arbeiten** - AI Agent automatisiert komplexe Analysen

### 🎓 Für wen ist diese Plattform?

| Zielgruppe | Hauptnutzen |
|------------|-------------|
| 🚔 **Strafverfolgung** | Ermittlungen, Beweissicherung, Geldwäsche-Bekämpfung |
| ⚖️ **Anwälte & Juristen** | Asset Recovery, gerichtsverwertbare Evidence |
| 🏦 **Compliance Officers** | AML/KYC, Sanktions-Screening, Travel Rule |
| 🔎 **Private Investigators** | Betrugsuntersuchungen, Due Diligence |
| 📊 **Blockchain-Analysten** | Research, Risk-Assessment, Netzwerk-Analyse |

### 🌟 Was macht uns besonders?

**Im Vergleich zu Chainalysis, TRM Labs, Elliptic:**

| Feature | Wir | Chainalysis | TRM Labs | Elliptic |
|---------|-----|-------------|----------|----------|
| **Chains** | 35+ | 25 | 20 | 18 |
| **AI Agent** | ✅ Vollständig | ❌ | ❌ | ❌ |
| **Open Source** | ✅ | ❌ | ❌ | ❌ |
| **Sprachen** | 42 | 15 | 8 | 5 |
| **Preis (Entry)** | $0 | $16.000 | $20.000 | $30.000 |
| **Self-Hosting** | ✅ | ❌ | ❌ | ❌ |
| **Mixer Demixing** | ✅ Open | ✅ Proprietary | ❌ | ❌ |
| **Real-Time KYT** | <100ms | ~200ms | ~150ms | ~180ms |

**🏆 Ergebnis:** Enterprise-Grade Features zu 95% niedrigeren Kosten!

---

## ⚡ 5-Minuten Quickstart

### Schritt 1: Account erstellen (30 Sekunden)

1. **Gehe zu** `https://your-platform.com/signup`
2. **Wähle einen Plan:**

| Plan | Preis | Ideal für |
|------|-------|-----------|
| 🆓 **Community** | Kostenlos | Testen, Einzelfälle |
| ⭐ **Pro** | $199/Monat | Profis, kleine Teams |
| 🚀 **Plus** | $499/Monat | Mit AI Agent |
| 💎 **Enterprise** | Custom | White-Label, unbegrenzte User |

3. **Email bestätigen** → Du erhältst Link
4. **🎉 Fertig!** Du bist drin

### Schritt 2: Deine erste Untersuchung (2 Minuten)

**Szenario:** Verdächtige Ethereum-Adresse analysieren

#### 2.1 Zum Dashboard navigieren

Nach Login landest du automatisch auf `/dashboard`

```
┌─────────────────────────────────────────────────┐
│  🏠 DASHBOARD                        👤 Max     │
│                                                   │
│  ⚡ QUICK ACTIONS                                │
│  ┌────────────┬────────────┬────────────┐       │
│  │ 🔍 Trace   │ 📁 Cases   │ 🕸️ Graph  │       │
│  └────────────┴────────────┴────────────┘       │
└─────────────────────────────────────────────────┘
```

#### 2.2 Transaction Tracing starten

1. **Klick auf "🔍 Transaction Tracing"**
2. **Adresse eingeben:**
   ```
   0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   ```
3. **Chain auswählen:** `Ethereum`
4. **Parameter setzen:**
   - Depth: `3` (Standard)
   - Max Addresses: `50`
   - Direction: `Both` (ein- und ausgehend)
5. **Klick "Start Trace"**

#### 2.3 Ergebnisse verstehen

Nach ~5 Sekunden siehst du:

```
┌────────────────────────────────────────┐
│  📊 TRACE RESULTS                      │
│                                          │
│  🚨 RISK SCORE: 78/100 (HIGH)          │
│                                          │
│  Findings:                               │
│  ⚠️  3 Sanctioned Addresses            │
│  🌪️  2 Mixer Connections               │
│  💰  12 Exchange Deposits              │
│  📊  Total Volume: $2.4M               │
│                                          │
│  [💾 Save as Case] [📊 Report]         │
└────────────────────────────────────────┘
```

**💡 Was bedeutet das?**
- **Risk Score 78** = Hohes Risiko, weitere Analyse empfohlen
- **Sanctioned Addresses** = OFAC/UN gelistet, illegal!
- **Mixer Connections** = Tornado Cash o.ä., Geldwäsche-Verdacht
- **Exchange Deposits** = Möglicher Cash-Out-Punkt

#### 2.4 Fall speichern

1. **Klick "💾 Save as Case"**
2. **Case-Name:** "Investigation: Suspicious ETH Wallet"
3. **Tags hinzufügen:** `#mixer #sanctions #urgent`
4. **Klick "Create"**

**🎯 Glückwunsch!** Erste Investigation abgeschlossen in 2 Minuten!

### Schritt 3: AI Agent nutzen (1 Minute)

**Der schnellste Weg:** Lass die KI arbeiten!

1. **Chat öffnen** (unten rechts: 💬 Symbol)
2. **Frag etwas wie:**

```
"Analysiere 0x742d35Cc... auf Sanctions und Mixer"
```

3. **AI macht automatisch:**
   - ✅ Trace starten
   - ✅ Multi-Sanctions Check (OFAC, UN, EU...)
   - ✅ Mixer Detection
   - ✅ Risk-Scoring
   - ✅ Report generieren

4. **Ergebnis in ~10 Sekunden:**

```
🤖 AI Agent:

Analyse abgeschlossen für 0x742d35Cc...

🚨 KRITISCHE FINDINGS:
• 3 OFAC-Sanctioned Addresses gefunden
• 2 Tornado Cash Mixer-Verbindungen
• Risk Score: 78/100 (HIGH RISK)

📊 Empfehlung:
• Sofort melden an Compliance
• Vertiefte Untersuchung nötig
• Case erstellt: "AUTO-2024-0015"

[📄 Full Report] [🕸️ Graph View]
```

**💡 Pro-Tipp:** AI Agent kann auch:
- "Erstelle Report für Gericht"
- "Finde alle Bridge-Transfers"
- "Check gegen alle Sanctions-Listen"
- "Was sind die Top-Risiken?"

---

## 📊 Dashboard Überblick

### Hauptbereiche erklärt

Nach dem Login siehst du **4 Hauptbereiche:**

#### 1. 📈 Live Metrics (Oben)

```
┌──────────────┬──────────────┬──────────────┐
│ Active Cases │ Traces Today │ Risk Alerts  │
│     12 ↗     │    43 ↗      │     3 ↘     │
└──────────────┴──────────────┴──────────────┘
```

**Was bedeutet das?**
- **Active Cases:** Deine offenen Ermittlungsfälle
- **Traces Today:** Anzahl Analysen heute (zeigt deine Aktivität)
- **Risk Alerts:** Neue High-Risk Findings (benötigen Aufmerksamkeit)
- **Trend-Pfeile:** ↗ = mehr als gestern, ↘ = weniger

#### 2. ⚡ Quick Actions (Mitte)

Deine wichtigsten Tools - **ein Klick zum Start:**

| Icon | Feature | Was macht es? | Wann nutzen? |
|------|---------|---------------|--------------|
| 🔍 | **Transaction Tracing** | Geldflüsse verfolgen | Immer, wenn verdächtige Adresse |
| 📁 | **Cases** | Fälle organisieren | Für längere Untersuchungen |
| 🕸️ | **Graph Explorer** | Visuelles Netzwerk | Komplexe Strukturen visualisieren |
| 🔗 | **Bridge Transfers** | Cross-Chain Tracking | Multi-Blockchain Flows |
| 🤖 | **AI Agent** | KI-Assistent | Für schnelle Analysen |
| 📊 | **Reports** | Evidence generieren | Für Behörden/Gerichte |

#### 3. 📋 Recent Activity (Unten Links)

**Timeline deiner letzten Actions:**

```
• 10:30 - Trace completed: 0xAbCd... → Mixer detected
• 09:15 - New alert: High-risk transaction (Score: 85)
• 08:45 - Case updated: "Operation Darkweb"
• Yesterday - Report exported: case_007.pdf
```

**💡 Nutzen:** Schnell sehen, was du zuletzt gemacht hast

#### 4. 🔔 Notifications (Oben Rechts)

**Alerts & Updates:**

```
🔔 (3)
  • High-risk address detected in Case #7
  • New sanctions list update (OFAC)
  • Team member added note to your case
```

---

## 🚀 Erste Schritte

### Navigation lernen

#### Linke Sidebar (Hauptmenü)

```
┌─────────────────────┐
│ 🏠 Dashboard        │ ← Start
│ 🔍 Tracing          │ ← Haupttool
│ 📁 Cases            │ ← Deine Fälle
│ 🕸️ Graph Explorer   │ ← Visualisierung
│ 🔗 Bridge Transfers │ ← Cross-Chain
│ 🎯 Correlation      │ ← Muster finden
│ 🤖 AI Agent         │ ← KI-Assistent
│ 👁️ Wallet Scanner   │ ← Seeds prüfen
│ 🚨 Threat Intel     │ ← Community Reports
│ ⚖️ Compliance       │ ← Sanctions, VASP
│ ⚙️ Settings         │ ← Einstellungen
└─────────────────────┘
```

**💡 Faustregel:**
- **Neue Investigation?** → 🔍 Tracing
- **Fall dokumentieren?** → 📁 Cases
- **Komplexe Struktur?** → 🕸️ Graph
- **Schnelle Frage?** → 🤖 AI Agent

#### Keyboard Shortcuts

| Shortcut | Aktion |
|----------|--------|
| `Ctrl + K` | Command Palette (schneller Zugriff auf alles) |
| `Ctrl + N` | Neue Trace |
| `Ctrl + Alt + C` | New Case |
| `Ctrl + Alt + A` | AI Agent öffnen |
| `Esc` | Dialog schließen |

---

## 📦 Pläne & Features

### Feature-Matrix

| Feature | Community | Pro | Plus | Enterprise |
|---------|-----------|-----|------|------------|
| **Transaction Tracing** | ✅ Basic | ✅ Unlimited | ✅ | ✅ |
| **Chains** | 10 | 35+ | 35+ | 35+ |
| **Cases** | 5 aktive | Unlimited | Unlimited | Unlimited |
| **Graph Explorer** | ❌ | ✅ | ✅ | ✅ |
| **Correlation Analysis** | ❌ | ✅ | ✅ | ✅ |
| **AI Agent** | ❌ | ❌ | ✅ | ✅ |
| **Wallet Scanner** | ❌ | ✅ | ✅ | ✅ |
| **Threat Intelligence** | Basic | Full | Full | Full |
| **Dark Web Monitoring** | ❌ | ✅ | ✅ | ✅ |
| **Multi-Sanctions** | OFAC only | 9 Lists | 9 Lists | 9 Lists |
| **VASP Directory** | ❌ | 5,000+ | 5,000+ | 5,000+ |
| **Travel Rule** | ❌ | ✅ | ✅ | ✅ |
| **KYT Real-Time** | ❌ | ✅ | ✅ | ✅ |
| **Evidence Export** | PDF | PDF/CSV | All formats | All + API |
| **Team Members** | 1 | 3 | 10 | Unlimited |
| **API Access** | ❌ | Read-Only | Full | Full + Custom |
| **White-Label** | ❌ | ❌ | ❌ | ✅ |
| **Support** | Community | Email | Priority | Dedicated |
| **Preis** | $0 | $199/mo | $499/mo | Custom |

### Was sollte ich wählen?

#### 🆓 Community Plan - Für dich wenn:
- ✅ Du die Plattform testen willst
- ✅ Einzelne Fälle gelegentlich
- ✅ Budget limitiert
- ❌ NICHT für: Professionelle Ermittlungen

#### ⭐ Pro Plan - Für dich wenn:
- ✅ Regelmäßige Ermittlungen
- ✅ Kleines Team (bis 3 Personen)
- ✅ Vollständige Forensik-Tools brauchst
- ✅ Graph Explorer & Correlation wichtig
- ❌ NICHT für: Wenn AI-Automation nötig

#### 🚀 Plus Plan - Für dich wenn:
- ✅ AI Agent für Effizienz
- ✅ Hohe Anzahl Cases
- ✅ Team-Kollaboration wichtig
- ✅ Maximale Produktivität
- **→ EMPFOHLEN für Profis!**

#### 💎 Enterprise - Für dich wenn:
- ✅ Große Organisation (Police, Agency)
- ✅ White-Label brauchen
- ✅ Unbegrenzte User
- ✅ Custom Integrations
- ✅ Dedicated Support

---

## 🎓 Nächste Schritte

**Du bist jetzt startklar!** Gehe weiter zu:

- 📖 **[Teil 2: Core Features](USER_HANDBOOK_02_CORE_FEATURES.md)** - Transaction Tracing, Cases, Bridge Transfers im Detail
- 📖 **[Teil 3: Advanced Features](USER_HANDBOOK_03_ADVANCED_FEATURES.md)** - Graph Explorer, Correlation, Wallet Scanner
- 📖 **[Teil 4: AI & Intelligence](USER_HANDBOOK_04_AI_INTELLIGENCE.md)** - AI Agent, Threat Intel, Dark Web
- 📖 **[Teil 5: Best Practices](USER_HANDBOOK_05_BEST_PRACTICES.md)** - Use Cases, Tipps, Troubleshooting

---

**💡 Schneller Einstieg?**
- Video-Tutorials: `/docs/videos`
- Live-Demo buchen: support@platform.com
- Community Forum: community.platform.com

**Viel Erfolg bei deinen Ermittlungen! 🚀**
