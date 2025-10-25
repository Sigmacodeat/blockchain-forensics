# 🚀 Billing System - Quick Start Guide

Schnellanleitung für die Billing-Seite: `http://localhost:3000/en/billing`

---

## 📋 Was ist neu?

### ✅ Unified Billing System
- **Stripe + Crypto**: Beide Zahlungsarten in einer Ansicht
- **4 Tabs**: Übersicht, Zahlungen, Rechnungen, Nutzung
- **Real-Time**: Live Usage Stats mit Progress Bars
- **Modern UI**: Glassmorphism, Animations, Icons

---

## 🎯 Features im Überblick

### Tab 1: Übersicht
- Aktueller Plan (Community, Pro, Plus, etc.)
- Subscription Status (Aktiv, Gekündigt, Testphase)
- Nächste Abrechnung
- Quick Actions (Upgrade, Cancel)

### Tab 2: Zahlungen
- Payment Methods Grid
- Kreditkarten (💳) mit Ablaufdatum
- Crypto Wallets (₿) mit letzter Nutzung
- Add Payment Button

### Tab 3: Rechnungen
- Alle Invoices (Stripe + Crypto)
- Payment Type Badges
- TX-Hash Links zu Etherscan
- PDF Downloads
- Export All

### Tab 4: Nutzung
- Transaction Traces (verwendet / Limit)
- Active Cases (verwendet / Limit)
- API Calls (verwendet / Limit)
- Progress Bars mit Farb-Coding
- Warnings bei >80% Usage

---

## 🔧 Backend-API

### Neue Endpoints:

```bash
# Subscription (Stripe + Crypto unified)
GET /api/v1/billing/subscription

# Payment Methods
GET /api/v1/billing/payment-methods

# Invoices
GET /api/v1/billing/invoices

# Usage Stats
GET /api/v1/billing/usage

# Cancel Subscription
POST /api/v1/billing/cancel

# Stripe Checkout
POST /api/v1/billing/checkout-session

# Stripe Portal
POST /api/v1/billing/portal-session
```

---

## 💳 Zahlungsarten

### Stripe (Karten-Zahlung)
1. Klicke "Plan upgraden"
2. Wähle Plan auf `/pricing`
3. Klicke "Mit Karte zahlen"
4. Stripe Checkout öffnet sich
5. Nach Zahlung: Redirect zu `/billing?success=true`

### Crypto (30+ Coins)
1. Klicke "Plan upgraden"
2. Wähle Plan auf `/pricing`
3. Klicke "Mit Krypto zahlen" (Orange Button)
4. Wähle Coin (BTC, ETH, USDT, etc.)
5. Scan QR oder Copy Address
6. Nach Zahlung: Automatische Aktivierung

---

## 📊 Usage Tracking

### Wie funktioniert es?

1. **Database Queries**
   ```sql
   -- Traces Count
   SELECT COUNT(*) FROM trace_requests 
   WHERE user_id = $1 AND created_at >= $2

   -- Cases Count
   SELECT COUNT(*) FROM cases 
   WHERE org_id = $1 AND created_at >= $2

   -- API Calls Count
   SELECT COUNT(*) FROM api_requests 
   WHERE user_id = $1 AND created_at >= $2
   ```

2. **Plan Limits** (from `plans.json`)
   - Community: 10 Credits/Monat
   - Starter: 50 Credits/Monat
   - Pro: Unlimited (-1)
   - Plus: Unlimited (-1)

3. **Progress Calculation**
   ```typescript
   const percentage = (used / limit) * 100;
   // Color: Green (<75%), Orange (75-90%), Red (>90%)
   ```

---

## 🎨 UI Components

### Badges
- **Status**: Aktiv (Green), Gekündigt (Red), Testphase (Yellow)
- **Payment Type**: Karte (Blue), Krypto (Orange)
- **Invoice Status**: Bezahlt (Green), Offen (Grey)

### Icons
- 💳 `<CreditCard />` - Kartenzahlung
- ₿ `<Bitcoin />` - Kryptowährung
- 📁 `<FileText />` - Rechnungen
- 📊 `<BarChart3 />` - Übersicht
- ⚡ `<Zap />` - Nutzung
- 👑 `<Crown />` - Premium Plan

### Colors
- **Primary**: Purple (#6366f1)
- **Success**: Green (#10b981)
- **Warning**: Orange (#f59e0b)
- **Error**: Red (#ef4444)
- **Crypto**: Orange (#f97316)
- **Card**: Blue (#3b82f6)

---

## 🔐 Security

### Authentication
- Alle Endpoints erfordern `Authorization: Bearer $TOKEN`
- User sieht nur eigene Daten
- Role-based access (Admin kann alle sehen)

### Data Isolation
```typescript
// User ID aus Token
const user_id = current_user.get("user_id");

// Query nur für diesen User
WHERE user_id = $1
```

---

## 📱 Responsive Design

### Desktop (>1024px)
- 4-Column Tab Navigation
- Full Table Display
- Side-by-Side Cards

### Tablet (768px-1024px)
- 2-Column Grids
- Scrollable Tables
- Stacked Cards

### Mobile (<768px)
- 1-Column Grid
- Horizontal Scroll Tables
- Full-Width Tabs
- Touch-Optimized Buttons

---

## 🐛 Troubleshooting

### Problem: "Keine Zahlungsmethoden"
**Lösung**: User muss erst Payment hinzufügen
- Via Stripe Portal
- Oder via Crypto-Zahlung

### Problem: "Keine Rechnungen"
**Lösung**: User hat noch nichts gekauft
- Erst nach erfolgreicher Zahlung sichtbar

### Problem: Usage zeigt 0/0
**Lösung**: Plan-Limits nicht konfiguriert
- Prüfe `plans.json`
- Prüfe Database Tables

### Problem: TX-Hash Link funktioniert nicht
**Lösung**: Nur für Crypto-Payments
- Stripe hat keine TX-Hash
- Link nur bei `payment_type: 'crypto'`

---

## 🚀 Deployment

### Environment Variables
```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_PLUS=price_...

# Crypto
NOWPAYMENTS_API_KEY=...
NOWPAYMENTS_IPN_SECRET=...
NOWPAYMENTS_SANDBOX=false

# Database
DATABASE_URL=postgresql://...
```

### Build Frontend
```bash
cd frontend
npm run build
# Deploy dist/ folder
```

### Start Backend
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## ✅ Testing Checklist

- [ ] Navigate to `/billing`
- [ ] All 4 Tabs load without errors
- [ ] Subscription shows correct plan
- [ ] Payment methods display icons correctly
- [ ] Invoices table shows all payments
- [ ] Usage progress bars animate correctly
- [ ] Responsive design works on mobile
- [ ] Stripe checkout works
- [ ] Crypto modal opens from pricing
- [ ] TX-Hash links open Etherscan
- [ ] PDF downloads work
- [ ] Cancel subscription shows confirmation

---

## 📞 Support

### Fragen?
- **Dokumentation**: `BILLING_SYSTEM_COMPLETE.md`
- **API-Docs**: `http://localhost:8000/docs`
- **Frontend-Code**: `frontend/src/pages/BillingPage.tsx`
- **Backend-Code**: `backend/app/api/v1/billing.py`

---

## 🎉 Launch Checklist

- [x] Backend API implementiert
- [x] Frontend UI fertig
- [x] TypeScript-Typen definiert
- [x] Responsive Design getestet
- [x] Security geprüft
- [x] Documentation geschrieben
- [ ] Production Deploy
- [ ] Monitoring Setup
- [ ] User Testing
- [ ] Marketing Launch

**Status: READY TO SHIP! 🚢**
