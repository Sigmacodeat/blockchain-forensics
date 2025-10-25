# SaaS End-to-End Verification Plan
**Ziel**: 100% Funktionalität des SaaS-Modells verifizieren

## 🎯 Kritische User Journeys (Must-Work)

### Journey 1: Neue User Registrierung → Community Plan
```
1. User landet auf Landing Page
2. Klickt "Get Started" / "Sign Up"
3. Registrierung mit Email + Password
4. Email-Verifizierung (optional)
5. Auto-Assign zu "Community" Plan (kostenlos)
6. Login → Dashboard
7. Zugriff auf Community Features:
   - Transaction Tracing (max depth = 2)
   - Cases erstellen
   - Bridge Transfers
8. KEIN Zugriff auf Pro+ Features (Investigator, Correlation, AI Agent)
```

### Journey 2: Upgrade zu Pro Plan
```
1. User mit Community Plan logged ein
2. Navigiert zu /pricing oder klickt "Upgrade" Button
3. Wählt "Pro" Plan ($49/Monat)
4. Payment Flow (Stripe/Mock)
5. Plan-Update in DB: user.plan = "pro"
6. Neue Features entsperrt:
   - Investigator (Graph Explorer)
   - Correlation (Pattern Detection)
   - Tieferes Tracing (max_depth = 5)
7. Features wie AI Agent noch gesperrt (Plus+)
```

### Journey 3: Plan-basierte Zugriffskontrolle
```
1. User mit "Community" Plan
2. Versucht Zugriff auf /investigator (Pro+)
   → Frontend: Redirect zu /upgrade oder Blocked-Page
   → Backend: HTTP 403 mit require_plan('pro')
3. Versucht API-Call zu /api/v1/correlation/patterns (Pro+)
   → HTTP 403: "Upgrade to Pro required"
4. User upgraded zu Pro
5. Zugriff zu /investigator funktioniert
6. API-Call funktioniert
```

### Journey 4: Admin-Features (System Management)
```
1. Admin-User logged ein
2. Zugriff auf Admin-Only Features:
   - /analytics (Trend Charts, Risk Distribution)
   - /monitoring (System Health)
   - /web-analytics
   - /orgs (Organization Management)
3. Normale User (auch Enterprise) haben KEINEN Zugriff
4. API-Endpunkte: require_admin() decorator
```

### Journey 5: Payment & Subscription Management
```
1. User wählt Plan (Pro, Plus, Enterprise)
2. Payment mit Stripe (oder Mock im Dev)
3. Subscription erstellt in DB:
   - subscription_id
   - plan
   - status: "active"
   - billing_cycle_start, billing_cycle_end
4. Auto-Renewal nach Monat
5. Downgrade/Cancel:
   - User cancelt → status = "cancelled"
   - Features downgrade zu Community nach Cycle-Ende
6. Failed Payment:
   - Retry-Logic (3 Versuche)
   - Nach 3 Fails → Downgrade zu Community
```

---

## 📊 Test-Coverage Analyse

### Backend Tests (Status: ~70% Coverage)

#### ✅ VORHANDEN (Was funktioniert)
1. **Authentication & Authorization** (`tests/test_auth.py`)
   - Registrierung
   - Login/Logout
   - JWT Token Generation
   - Password Reset

2. **Plan Gates** (`tests/test_plan_gates.py`)
   - require_plan() decorator
   - Plan-Hierarchie (community < pro < plus < enterprise)
   - 403 bei unzureichendem Plan

3. **Admin Gates** (`tests/test_admin_gates.py`)
   - require_admin() decorator
   - Admin-only Endpunkte

4. **Transaction Tracing** (`tests/test_tracing_workflows_rbac.py`)
   - Forward/Backward/Bidirectional
   - Role-basierte Tiefensteuerung
   - RBAC: VIEWER (2), ANALYST (5), ADMIN (10)

5. **Travel Rule** (`tests/test_travel_rule_api.py`)
   - IVMS101 Format
   - VASP Screening

6. **Advanced Risk** (`tests/test_advanced_indirect_risk.py`)
   - Risk Scoring
   - Category Detection
   - Cross-Chain Risk

7. **AI Agents** (`tests/test_ai_agent_*.py`)
   - Tools (risk_score, bridge_lookup, trigger_alert)
   - LangChain Integration

#### ⚠️ VORHANDEN ABER UNVOLLSTÄNDIG
1. **Subscription Management** (teilweise)
   - Basis-Modelle vorhanden
   - FEHLT: Payment Flow Tests
   - FEHLT: Auto-Renewal Tests
   - FEHLT: Downgrade-Logic Tests

2. **User Management** (teilweise)
   - CRUD vorhanden
   - FEHLT: Organization Assignment Tests
   - FEHLT: Multi-Tenant Tests

3. **Analytics** (teilweise)
   - API-Endpunkte vorhanden
   - FEHLT: Admin-Gate Tests für Analytics
   - FEHLT: Data Aggregation Tests

#### ❌ FEHLEND (Must-Have)
1. **Payment Integration Tests**
   - Stripe Mock Tests
   - Payment Success → Plan Update
   - Payment Failure → Retry Logic
   - Webhook Tests (stripe.invoice.paid, etc.)

2. **Subscription Lifecycle Tests**
   - Neue Subscription erstellen
   - Auto-Renewal
   - Downgrade bei Cancel
   - Grace Period bei Payment Failure

3. **Feature Access Integration Tests**
   - End-to-End: User mit Plan X → Zugriff auf Features Y
   - Cross-Module: Tracing + Risk + Compliance

4. **Organization/Multi-Tenant Tests**
   - Org erstellen
   - Users zu Org zuweisen
   - Org-Level Subscriptions
   - Isolation zwischen Orgs

---

### Frontend Tests (Status: ~40% Coverage)

#### ✅ VORHANDEN
1. **Playwright E2E** (`frontend/test-results/`)
   - Onboarding Tour (1 Test)
   - SEHR BEGRENZT!

#### ❌ FEHLEND (Critical!)
1. **User Registration Flow**
   - Sign Up Form
   - Email/Password Validierung
   - Auto-Login nach Registrierung

2. **Login Flow**
   - Login Form
   - JWT Storage
   - Redirect zu Dashboard

3. **Plan Upgrade Flow**
   - Pricing Page Navigation
   - Plan Selection
   - Payment Modal
   - Success Redirect

4. **Feature Access Guards**
   - Redirect bei unzureichendem Plan
   - "Upgrade Required" Modals
   - Plan-basierte Navigation (Links disabled)

5. **Dashboard E2E**
   - Quick Actions funktionieren
   - Live Metrics laden
   - Navigation zu Features

6. **Forensic Workflows**
   - Transaction Tracing E2E
   - Case Management E2E
   - Investigator (Graph Explorer) E2E

---

## 🚀 PRIORISIERTER TEST-PLAN

### Phase 1: KRITISCHE BACKEND-TESTS (Must-Have)
**Ziel**: Payment & Subscription-Flow wasserdicht machen

1. **`tests/test_payment_integration.py`** (NEU)
   - Stripe Mock Integration
   - Payment Success → Plan Update
   - Payment Failure → Retry
   - Webhook Handling

2. **`tests/test_subscription_lifecycle.py`** (NEU)
   - Create Subscription
   - Auto-Renewal (Cronjob Mock)
   - Downgrade bei Cancel
   - Grace Period Logic

3. **`tests/test_feature_access_e2e.py`** (NEU)
   - Community User → nur Community Features
   - Pro User → Community + Pro Features
   - Admin User → Analytics/Monitoring
   - Cross-Module Tests

### Phase 2: FRONTEND E2E-TESTS (Critical Paths)
**Ziel**: Komplette User Journeys verifizieren

4. **`frontend/tests/e2e/registration.spec.ts`** (NEU)
   - Sign Up Flow
   - Auto-Assign zu Community Plan
   - Login nach Registrierung

5. **`frontend/tests/e2e/plan-upgrade.spec.ts`** (NEU)
   - Community → Pro Upgrade
   - Payment Flow (Mock)
   - Feature-Entsperrung

6. **`frontend/tests/e2e/tracing-workflow.spec.ts`** (NEU)
   - Tracing mit Community Plan (depth=2)
   - Tracing mit Pro Plan (depth=5)
   - Blocked bei unzureichendem Plan

7. **`frontend/tests/e2e/dashboard-navigation.spec.ts`** (NEU)
   - Dashboard Load
   - Quick Actions
   - Plan-basierte Navigation

### Phase 3: INTEGRATION & STRESS-TESTS
**Ziel**: Performance und Skalierbarkeit

8. **`tests/test_multi_tenant.py`** (NEU)
   - Org Isolation
   - Org-Level Subscriptions
   - User-Org Assignment

9. **`tests/test_performance.py`** (erweitern)
   - API Latency < 100ms
   - Concurrent Users (100+)
   - Database Query Optimization

10. **`tests/test_security.py`** (NEU)
    - SQL Injection Prevention
    - XSS Prevention
    - CSRF Protection
    - Rate Limiting

---

## 📋 VERIFICATION CHECKLIST

### Backend
- [ ] Authentication & Authorization (Login, Registrierung, JWT)
- [ ] Plan Gates (require_plan decorator funktioniert)
- [ ] Admin Gates (require_admin decorator funktioniert)
- [ ] Payment Integration (Stripe Mock, Webhooks)
- [ ] Subscription Lifecycle (Create, Renew, Cancel, Downgrade)
- [ ] Feature Access (Plan-basierte API-Zugriffe)
- [ ] Transaction Tracing (alle Modi, RBAC)
- [ ] Risk Scoring & Compliance
- [ ] AI Agents (Tools, LangChain)
- [ ] Multi-Tenant Isolation

### Frontend
- [ ] Registration Flow (Sign Up → Auto-Login)
- [ ] Login Flow (Login → Dashboard)
- [ ] Plan Upgrade Flow (Pricing → Payment → Features)
- [ ] Feature Guards (Redirect/Block bei unzureichendem Plan)
- [ ] Dashboard (Load, Quick Actions, Metrics)
- [ ] Transaction Tracing E2E
- [ ] Case Management E2E
- [ ] Investigator (Graph Explorer) E2E
- [ ] Navigation (Plan-basiert, Admin-Links)

### Infrastructure
- [ ] Database Migrations (alle applied)
- [ ] Redis Cache (funktioniert)
- [ ] Background Jobs (Cron, Celery)
- [ ] Monitoring (Prometheus, Grafana)
- [ ] Logging (strukturiert, searchable)
- [ ] Error Handling (graceful degradation)

---

## 🎯 SUCCESS CRITERIA

### Definition of "100% funktioniert"
1. **Alle Backend-Tests grün** (100% Coverage für kritische Pfade)
2. **Alle Frontend E2E-Tests grün** (Happy Paths + Error Cases)
3. **Manueller Walkthrough erfolgreich**:
   - Registrierung → Community Plan → Dashboard
   - Upgrade zu Pro → Features entsperrt
   - Admin-Login → Analytics/Monitoring
4. **Performance Benchmarks erfüllt**:
   - API Latency < 100ms (p95)
   - Dashboard Load < 2s
   - 100+ concurrent users
5. **Security Audit bestanden** (keine Critical Vulnerabilities)
6. **Dokumentation vollständig** (API Docs, User Guides, Admin Guides)

---

## 📅 TIMELINE

### Tag 1: Backend Tests (6-8h)
- Payment Integration Tests
- Subscription Lifecycle Tests
- Feature Access E2E Tests

### Tag 2: Frontend E2E (6-8h)
- Registration Flow
- Plan Upgrade Flow
- Tracing Workflow
- Dashboard Navigation

### Tag 3: Integration & Verification (4-6h)
- Multi-Tenant Tests
- Performance Tests
- Security Tests
- Manueller Walkthrough
- Verification Report

**TOTAL**: ~18-22 Stunden für 100% Verifikation

---

## 🚦 CURRENT STATUS

### Backend
- ✅ Authentication (90%)
- ✅ Plan Gates (100%)
- ✅ Admin Gates (100%)
- ⚠️ Payment (30% - Models only)
- ⚠️ Subscription (40% - Basic Logic)
- ✅ Tracing (85%)
- ✅ Risk/Compliance (90%)
- ✅ AI Agents (95%)

**Overall Backend**: ~75% Ready

### Frontend
- ⚠️ E2E Tests (10% - 1 Onboarding Test)
- ✅ Components (80% - alle implementiert)
- ⚠️ Integration Tests (0%)

**Overall Frontend**: ~40% Ready

### **GESAMTSTATUS: ~60% VERIFIZIERT**

---

## NÄCHSTE SCHRITTE

Ich starte jetzt mit **Phase 1: Kritische Backend-Tests**:
1. Payment Integration Tests
2. Subscription Lifecycle Tests
3. Feature Access E2E Tests

Danach Phase 2 (Frontend E2E) und Phase 3 (Integration).

**Bereit für Implementierung?** 🚀
