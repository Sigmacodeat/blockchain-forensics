# 🔐 Kunde vs. Admin – Was sieht wer?

## 🎯 **HAUPTPRODUKT: BLOCKCHAIN-FORENSIK**

Unsere Homepage bietet **Blockchain-Forensik** als Hauptprodukt. Kunden können Bitcoin-Adressen tracen, Transaktionen nachverfolgen und forensische Analysen durchführen.

---

## 👥 **KUNDE sieht (Forensik-Features)**

### **Community (Kostenlos)**
✅ **Basic Forensik**
- Dashboard (Übersicht)
- **Transaction Tracing** – Bitcoin-Adressen tracen! 🔍
- Cases (Forensik-Fälle verwalten)
- Bridge Transfers (Cross-Chain-Bewegungen)
- Alerts anzeigen

**Quotas:**
- 1 Blockchain
- 1 Benutzer
- 1.000 Credits/Monat
- 3 Adressen
- 1 Case
- 1 Alert

---

### **Starter (59$/Monat)**
✅ **Erweiterte Forensik**
- Alles aus Community +
- **Enhanced Tracing** (mehr Tiefe, mehr Adressen)
- Trace Tools (erweiterte Werkzeuge)
- Label-Enrichment (Adressen beschriften)
- PDF-Reports
- Webhooks (limitiert)

**Quotas:**
- 3 Blockchains
- 2 Benutzer
- 5.000 Credits/Monat
- 10 Adressen
- 5 Cases
- 5 Alerts

---

### **Pro (199$/Monat)** ⭐ Beliebteste
✅ **Professional Forensik**
- Alles aus Starter +
- **Graph Explorer** (Investigator) – Netzwerk-Visualisierung
- **Correlation Analysis** – Pattern-Erkennung
- Case Management (vollständig)
- Dashboards (Custom)
- Editable Playbooks
- Unlimited Tracing

**Quotas:**
- 4 Blockchains
- 3 Benutzer
- 20.000 Credits/Monat
- 50 Adressen
- 20 Cases
- 20 Alerts

---

### **Business (499$/Monat)**
✅ **Enterprise Forensik**
- Alles aus Pro +
- Risk-Policies verwalten
- Rollen & Permissions
- SSO (Basic)
- Scheduled Reports
- Compliance Reports
- Performance-Metriken (eigene)

**Quotas:**
- 6 Blockchains
- 10 Benutzer
- 50.000 Credits/Monat
- 250 Adressen
- 100 Cases
- 50 Alerts

---

### **Plus (4.999$/Monat)** 💎
✅ **Financial Institution Features**
- Alles aus Business +
- **AI Agent** (KI-Assistent)
- Advanced Correlation
- Full Investigator
- Travel Rule Support
- All Sanctions Lists
- SSO (SAML)
- Full SIEM Exports
- Unlimited Graph Exports
- Advanced Audit Logs

**Quotas:**
- 10 Blockchains
- 50 Benutzer
- 200.000 Credits/Monat
- 1.000 Adressen
- 500 Cases
- 200 Alerts

---

### **Enterprise (Custom)** 🏢
✅ **Custom Solutions**
- Alles aus Plus +
- Chain of Custody (vollständig)
- eIDAS Signatures
- Data Residency (Custom)
- VPC/On-Prem
- Private Indexers
- GRC/SIEM Integrations
- **White-Label** (eigene Marke)
- Dedicated Support (24/7)
- Custom Policies

**Quotas:** Alles Custom

---

## 🛠️ **ADMIN sieht (System-Management)**

### **Nur für Admins (interne Tools):**

#### **Analytics** 📊
- **Trend Charts** (Traces, Alerts, Risk über Zeit)
- Risk-Distribution
- Time-Series Analysis
- System-Metriken

#### **Monitoring** 🔔
- System Health
- Alert Engine Status
- Performance Monitoring
- Uptime-Tracking

#### **Web Analytics** 🌐
- Website-Traffic
- User-Verhalten
- Conversion-Tracking

#### **Orgs** 🏢
- Organisationen verwalten
- Mandanten-Management

#### **Admin-Panel** ⚙️
- User-Management
- System-Konfiguration
- Billing-Übersicht
- Audit Logs (alle)

---

## 📍 **Navigation (Sidebar)**

### **Kunde sieht:**
```
📊 Dashboard
🔍 Transaction Tracing     ← HAUPTFEATURE!
📁 Cases
🌉 Bridge Transfers
🔧 Trace Tools              (Starter+)
🕸️ Graph Explorer          (Pro+)
🧠 Correlation              (Pro+)
📈 Dashboards               (Pro+)
⚡ Performance              (Business+)
🛡️ Policies                 (Business+)
🤖 AI Agent                 (Plus+)
```

### **Admin sieht (zusätzlich):**
```
📊 Analytics                ← NUR ADMIN
🌐 Web Analytics            ← NUR ADMIN
🔔 Monitoring               ← NUR ADMIN
🏢 Orgs                     ← NUR ADMIN
⚙️ Admin                    ← NUR ADMIN
```

---

## 🎨 **Dashboard (Hauptseite)**

### **Kunde sieht:**
- KPI-Übersicht (Traces, Cases, Alerts)
- Live Alerts
- System Health
- Quick Actions:
  - Transaction Tracing (alle)
  - Cases (alle)
  - Investigator (Pro+)
  - Correlation (Pro+)
  - AI Agent (Plus+)
- Ops-Übersicht (Aging, Backlog)
- Rule Effectiveness

### **Admin sieht (zusätzlich):**
- **Trend Charts** (nur Admin!) 📊
- Audit KPIs
- Analyst Throughput
- System-Metriken

---

## 🔒 **Backend API-Schutz**

### **Kunde-Endpunkte:**
```python
# Tracing (Community+)
@router.post("/trace")
async def create_trace(user: dict = Depends(get_current_user)):
    # Quotas basierend auf Plan

# Investigator (Pro+)
@router.get("/graph/explore")
async def explore_graph(user: dict = Depends(require_plan('pro'))):
    ...

# AI Agent (Plus+)
@router.post("/ai-agent/query")
async def ai_query(user: dict = Depends(require_plan('plus'))):
    ...
```

### **Admin-Endpunkte:**
```python
# Analytics (Admin only)
@router.get("/analytics/trends")
async def get_trends(user: dict = Depends(require_admin)):
    ...

# Monitoring (Admin only)
@router.get("/monitoring/health")
async def get_health(user: dict = Depends(require_admin)):
    ...
```

---

## ✨ **Was ist neu?**

### **Vorher (FALSCH):**
- ❌ Analytics für Pro+
- ❌ Tracing erst ab Pro
- ❌ Keine klare Trennung

### **Jetzt (KORREKT):**
- ✅ **Tracing ab Community** – Hauptprodukt!
- ✅ **Analytics nur für Admin** – interne Analyse
- ✅ **Klare Trennung**: Forensik vs. System-Management

---

## 🚀 **Empfehlung für Homepage**

### **Landing Page:**
```
Headline: "Bitcoin-Forensik leicht gemacht"
Subline: "Tracen Sie Krypto-Transaktionen, erstellen Sie forensische Reports und lösen Sie Fälle."

CTA: "Jetzt kostenlos starten" → Community-Plan
```

### **Pricing Page:**
- **Community**: "Für Hobbyisten – Bitcoin tracen kostenlos"
- **Starter**: "Für kleine Teams – Mehr Traces, mehr Tools"
- **Pro**: "Für Profis – Graph Explorer & Correlation" ⭐
- **Business**: "Für Unternehmen – Compliance & SSO"
- **Plus**: "Für Banken – AI-Agent & Travel Rule" 💎
- **Enterprise**: "Custom – White-Label & On-Prem" 🏢

---

## 📝 **Zusammenfassung**

| Feature | Community | Starter | Pro | Business | Plus | Enterprise | Admin |
|---------|-----------|---------|-----|----------|------|-----------|-------|
| **Tracing** | ✅ Basic | ✅ Enhanced | ✅ Unlimited | ✅ | ✅ | ✅ | ✅ |
| **Cases** | ✅ View | ✅ Create | ✅ Full | ✅ | ✅ | ✅ | ✅ |
| **Investigator** | ❌ | ❌ | ✅ | ✅ | ✅ Full | ✅ | ✅ |
| **Correlation** | ❌ | ❌ | ✅ Basic | ✅ | ✅ Advanced | ✅ | ✅ |
| **AI Agent** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Policies** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ Custom | ✅ |
| **White-Label** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Analytics** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ ONLY |
| **Monitoring** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ ONLY |

---

**Stand:** Oktober 2025  
**Hauptprodukt:** Blockchain-Forensik (Tracing ab Community!)  
**Admin-Tools:** Analytics, Monitoring, Web-Analytics (nur Admin)
