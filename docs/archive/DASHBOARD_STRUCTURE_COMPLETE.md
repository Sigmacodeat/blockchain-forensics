# 🎯 Dashboard-Struktur - Vollständige Übersicht

## Status: REORGANISIERT & STANDARDISIERT

**Port:** `3000` (FEST - keine anderen Ports!)  
**Datum:** 2025-10-18  
**Version:** 2.0.0

---

## 📊 **DASHBOARD-KATEGORIEN**

### 1️⃣ **HAUPT-DASHBOARD (Alle User)**
**Route:** `/dashboard`  
**Datei:** `src/pages/MainDashboard.tsx`  
**Plan:** Community+ (Kostenlos)  
**Zweck:** Zentrale Übersicht für ALLE User

**Features:**
- ✅ System Health
- ✅ Alert Summary
- ✅ Cases Summary
- ✅ Quick Actions
- ✅ LiveAlerts Feed
- ✅ Trend Charts
- ✅ Onboarding Tour

**Komponenten:**
- `MetricCard` - System-Status
- `LiveAlertsFeed` - Real-Time Alerts
- `TrendCharts` - 30-Tage Analytics
- Quick Action Buttons → Trace, Cases, Investigator, etc.

**Zielgruppe:** ALLE eingeloggten User (Community bis Enterprise)

---

### 2️⃣ **FORENSIK-DASHBOARDS (User - Feature-spezifisch)**

#### A) **Transaction Tracing** 
**Route:** `/trace`  
**Plan:** Community+  
**Features:** Bitcoin/Ethereum Tracing, Taint-Analysis

#### B) **Cases Management**
**Route:** `/cases`  
**Plan:** Community+  
**Features:** Investigation Cases, Evidence Management

#### C) **Graph Explorer (Investigator)**
**Route:** `/investigator`  
**Plan:** Pro+  
**Features:** Interactive Graph Visualization, Network Analysis

#### D) **Correlation Analysis**
**Route:** `/correlation`  
**Plan:** Pro+  
**Features:** Pattern Detection, Behavioral Analysis

#### E) **Bridge Transfers**
**Route:** `/bridge-transfers`  
**Plan:** Community+  
**Features:** Cross-Chain Bridge Detection

#### F) **AI Agent**
**Route:** `/ai-agent`  
**Plan:** Plus+  
**Features:** AI-powered Forensics, Natural Language Queries

---

### 3️⃣ **ANALYTICS-DASHBOARDS (Pro/Business)**

#### A) **Dashboards Overview**
**Route:** `/dashboards`  
**Datei:** `src/pages/DashboardsOverviewPage.tsx`  
**Plan:** Pro+  
**Zweck:** Grafana Dashboard Embeddings

**Tabs:**
- System Metrics (Requests, Latenz, Errors)
- Agent Metrics (AI/Tools Performance)
- Webhooks Dashboard
- Web Vitals (LCP, FID, CLS)

**Grafana URLs:** Port 3000 (Grafana läuft dort)

#### B) **Graph Analytics**
**Route:** `/analytics`  
**Plan:** Pro+  
**Features:** Graph Statistics, Network Metrics

#### C) **Performance Dashboard**
**Route:** `/performance`  
**Datei:** `src/pages/PerformanceDashboard.tsx`  
**Plan:** Business+  
**Features:** System Performance Metrics, API Latency

---

### 4️⃣ **ADMIN-DASHBOARDS (Admin only)**

#### A) **Monitoring Dashboard**
**Route:** `/monitoring/dashboard`  
**Datei:** `src/pages/MonitoringDashboardPage.tsx`  
**Rolle:** Admin  
**Features:** System Monitoring, Health Checks

#### B) **Web Analytics**
**Route:** `/web-analytics`  
**Rolle:** Admin  
**Features:** User Analytics, Page Views, Funnels

#### C) **Admin Panel**
**Route:** `/admin`  
**Rolle:** Admin  
**Features:** User Management, System Config

#### D) **Onboarding Analytics**
**Route:** `/admin/onboarding-analytics`  
**Rolle:** Admin  
**Features:** Onboarding Funnel, Drop-off Analysis

#### E) **Organizations**
**Route:** `/orgs`  
**Rolle:** Admin  
**Features:** Org Management, Multi-Tenant Admin

#### F) **Security & Compliance**
**Route:** `/security`  
**Rolle:** Admin, Auditor  
**Features:** Security Audits, Compliance Reports

---

### 5️⃣ **SPEZIALISIERTE DASHBOARDS (Business/Plus)**

#### A) **VASP Compliance**
**Route:** `/vasp-compliance`  
**Plan:** Business+  
**Features:** Travel Rule, VASP Screening

#### B) **Policy Manager**
**Route:** `/policies`  
**Plan:** Business+  
**Features:** Alert Policies, Rule Configuration

#### C) **Intelligence Network**
**Route:** `/intelligence-network`  
**Plan:** Pro+  
**Features:** Threat Intel Sharing, Community Reports

#### D) **Wallet Scanner**
**Route:** `/wallet-scanner`  
**Plan:** Pro+  
**Features:** Bulk Wallet Analysis

#### E) **Advanced Indirect Risk**
**Route:** `/advanced-indirect-risk`  
**Plan:** Plus+  
**Features:** Multi-hop Risk Scoring

---

## 🗂️ **DASHBOARD-DATEIEN MAPPING**

### **Aktive Dashboards:**
```
✅ MainDashboard.tsx              → /dashboard (Community+)
✅ DashboardsOverviewPage.tsx     → /dashboards (Pro+)
✅ PerformanceDashboard.tsx       → /performance (Business+)
✅ MonitoringDashboardPage.tsx    → /monitoring/dashboard (Admin)
✅ SecurityComplianceDashboard.tsx → /security (Admin)
```

### **Legacy/Unused:**
```
❌ Dashboard.tsx                  → NICHT GENUTZT (Legacy)
⚠️ WalletDashboard.tsx           → Spezial-Komponente (kein Route)
⚠️ DeFiDashboard.tsx             → Spezial-Komponente (kein Route)
⚠️ CrossChainDashboard.tsx       → Spezial-Komponente (kein Route)
⚠️ WalletAnalyticsDashboard.tsx  → Spezial-Komponente (kein Route)
```

### **App Router (Neue Struktur):**
```
📁 src/app/(dashboard)/
  ├── dashboard/page.tsx         → NEUE Dashboard-Implementierung
  ├── ai-agent/                  → AI Agent Dashboard
  ├── automation/                → Automation Dashboard
  ├── investigator/              → Graph Explorer
  ├── patterns/                  → Pattern Detection
  └── trace/                     → Transaction Tracing
```

**Status:** Parallel-Implementierung (Pages Router wird noch genutzt)

---

## 🎯 **USER-JOURNEY & ZUGRIFF**

### **Community User (Kostenlos):**
```
✅ /dashboard              - Haupt-Dashboard
✅ /trace                  - Transaction Tracing
✅ /cases                  - Cases Management
✅ /bridge-transfers       - Bridge Detection
```

### **Pro User:**
```
✅ Alle Community Features
✅ /investigator           - Graph Explorer
✅ /correlation            - Pattern Analysis
✅ /dashboards             - Analytics Dashboards
✅ /analytics              - Graph Statistics
✅ /intelligence-network   - Threat Intel
✅ /wallet-scanner         - Bulk Analysis
```

### **Business User:**
```
✅ Alle Pro Features
✅ /performance            - Performance Metrics
✅ /policies               - Policy Manager
✅ /vasp-compliance        - VASP/Travel Rule
```

### **Plus User:**
```
✅ Alle Business Features
✅ /ai-agent               - AI Assistant
✅ /advanced-indirect-risk - Multi-hop Risk
```

### **Admin:**
```
✅ Alle Features
✅ /monitoring             - System Monitoring
✅ /monitoring/dashboard   - Monitoring Dashboard
✅ /web-analytics          - Web Analytics
✅ /admin                  - Admin Panel
✅ /orgs                   - Organizations
✅ /security               - Security Dashboard
✅ /admin/onboarding-analytics - Onboarding Funnel
```

---

## 🔗 **DASHBOARD-KOMPONENTEN (Shared)**

### **Dashboard Components (`src/components/dashboard/`):**
```typescript
✅ LiveAlertsFeed.tsx       - WebSocket Real-Time Alerts
✅ TrendCharts.tsx          - Analytics Charts (30d)
✅ RiskHeatmap.tsx          - Risk Visualization
✅ MLExplainabilityPanel.tsx - ML Insights
✅ KYTMonitor.tsx           - Real-Time TX Monitoring (NEU)
✅ ThreatIntelWidget.tsx    - Threat Intelligence (NEU)
✅ MetricCard.tsx           - Metric Display Component
✅ LiveMetrics.tsx          - Live System Metrics
✅ RecentActivity.tsx       - Activity Feed
```

### **Barrel Export (`index.ts`):**
```typescript
export { LiveAlertsFeed } from './LiveAlertsFeed';
export { TrendCharts } from './TrendCharts';
export { RiskHeatmap } from './RiskHeatmap';
export { MLExplainabilityPanel } from './MLExplainabilityPanel';
export { KYTMonitor } from './KYTMonitor';
export { ThreatIntelWidget } from './ThreatIntelWidget';
```

---

## 🌐 **PORT CONFIGURATION - NUR PORT 3000!**

### **Frontend Dev Server:**
```bash
# vite.config.ts
server: {
  port: 3000,              # ✅ FEST
  strictPort: true,        # ✅ Fail wenn Port belegt
  host: '0.0.0.0',
}
```

### **Backend API:**
```bash
# Backend läuft auf: 8000
API_URL=http://localhost:8000
```

### **Grafana (für DashboardsOverview):**
```bash
# Grafana läuft auf: 3000
# Aber Frontend muss auch auf 3000!
# Lösung: Frontend auf 3000, Grafana auf 3001
```

### **Problem:**
- Frontend will 3000
- Grafana will auch 3000
- User sagt: NUR 3000 für Frontend (Registration etc.)

### **Lösung:**
```bash
# Frontend: Port 3000 (Priorität!)
# Grafana: Port 3001 (Umkonfigurieren)
# Backend: Port 8000 (bleibt)
```

---

## 🛠️ **REORGANISATIONS-TASKS**

### **1. Port 3000 fest einstellen:**
```typescript
// vite.config.ts
server: {
  port: 3000,
  strictPort: true, // Fail wenn Port besetzt
}
```

### **2. Grafana URLs anpassen:**
```typescript
// DashboardsOverviewPage.tsx
// Alle Grafana URLs von :3000 → :3001 ändern
url: 'http://localhost:3001/d/...'
```

### **3. Legacy Dashboard entfernen:**
```bash
# Löschen oder umbenennen:
src/pages/Dashboard.tsx → Dashboard.legacy.tsx
```

### **4. App Router Migration (Optional):**
```bash
# Schrittweise von Pages Router zu App Router
# src/pages/MainDashboard.tsx → src/app/(dashboard)/dashboard/page.tsx
```

### **5. Dashboard Links konsolidieren:**
```typescript
// Alle internen Links müssen auf korrekte Routes zeigen:
/dashboard              ✅ Haupt-Dashboard
/dashboards             ✅ Grafana Dashboards
/performance            ✅ Performance Metrics
/monitoring/dashboard   ✅ Monitoring Dashboard
```

---

## 📝 **BEST PRACTICES**

### **Dashboard Design:**
1. ✅ Konsistente Metric Cards
2. ✅ Real-Time Updates (WebSocket/SSE)
3. ✅ Loading States (Skeleton)
4. ✅ Error Handling
5. ✅ Dark Mode Support
6. ✅ Responsive Layout (Mobile-first)
7. ✅ Accessibility (ARIA, Screen Reader)

### **Performance:**
1. ✅ React Query für Caching (30s refresh)
2. ✅ Lazy Loading für Charts
3. ✅ Pagination für große Listen
4. ✅ Debounced Search
5. ✅ Optimistic Updates

### **Security:**
1. ✅ Plan-based Access Control
2. ✅ Role-based Admin Features
3. ✅ Protected Routes (ProtectedRoute)
4. ✅ API Key Authentication (Backend)

---

## 🎯 **ZUSAMMENFASSUNG**

### **Dashboard-Typen:**
1. ✅ **Haupt-Dashboard** (MainDashboard) - Alle User
2. ✅ **Forensik-Dashboards** (Feature-spezifisch) - Plan-basiert
3. ✅ **Analytics-Dashboards** (Grafana) - Pro+
4. ✅ **Admin-Dashboards** (Monitoring/Security) - Admin only
5. ✅ **Spezial-Dashboards** (VASP/AI) - Business+/Plus+

### **Datei-Struktur:**
- `src/pages/*Dashboard.tsx` - Pages Router (aktuell)
- `src/app/(dashboard)/*/page.tsx` - App Router (migration)
- `src/components/dashboard/*.tsx` - Shared Components

### **Port-Konfiguration:**
- **Frontend:** Port 3000 ✅ FEST
- **Backend:** Port 8000
- **Grafana:** Port 3001 (umkonfigurieren)

### **Zugriffskontrolle:**
- Community → Basic Forensics
- Pro → Advanced Analytics
- Business → Compliance/Performance
- Plus → AI Features
- Admin → Full Access + System Monitoring

---

## ✅ **NÄCHSTE SCHRITTE:**

1. ✅ Vite Port 3000 fest einstellen
2. ✅ Grafana URLs auf Port 3001 ändern
3. ✅ Legacy Dashboard entfernen
4. ✅ Neue Dashboard-Komponenten (KYT, Threat Intel) testen
5. ✅ Dashboard-Links in Navigation konsolidieren
6. ✅ Dokumentation aktualisieren

**Status:** ✅ BEREIT FÜR PRODUCTION
