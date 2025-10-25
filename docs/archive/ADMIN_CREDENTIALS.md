# 🔐 Admin-Zugangsdaten

## ⚠️ VERTRAULICH - NUR FÜR INTERNE NUTZUNG

---

## 👤 **ADMIN-ACCOUNT**

### **Standard Admin-Login:**
```
E-Mail:     admin@blockchain-forensics.com
Passwort:   Admin2025!Secure
Rolle:      admin
Plan:       enterprise
```

### **Test Admin-Login:**
```
E-Mail:     test-admin@blockchain-forensics.com
Passwort:   TestAdmin2025!
Rolle:      admin
Plan:       enterprise
```

---

## 🔑 **SUPER-ADMIN (Notfall-Zugang)**

```
E-Mail:     superadmin@blockchain-forensics.com
Passwort:   SuperAdmin2025!Emergency
Rolle:      admin
Plan:       enterprise
MFA:        optional (kann aktiviert werden)
```

---

## 👥 **TEST-ACCOUNTS (Verschiedene Rollen)**

### **1. Community User (Kostenlos):**
```
E-Mail:     test-community@blockchain-forensics.com
Passwort:   Community2025!
Rolle:      user
Plan:       community
Zugriff:    3 Dashboards (Trace, Cases, Bridge-Transfers)
```

### **2. Pro User:**
```
E-Mail:     test-pro@blockchain-forensics.com
Passwort:   Pro2025!
Rolle:      user
Plan:       pro
Zugriff:    9 Dashboards (+ Investigator, Correlation, Analytics)
```

### **3. Business User:**
```
E-Mail:     test-business@blockchain-forensics.com
Passwort:   Business2025!
Rolle:      user
Plan:       business
Zugriff:    10 Dashboards (+ Performance)
```

### **4. Plus User:**
```
E-Mail:     test-plus@blockchain-forensics.com
Passwort:   Plus2025!
Rolle:      user
Plan:       plus
Zugriff:    11 Dashboards (+ AI Agent)
```

### **5. Auditor (Spezial-Rolle):**
```
E-Mail:     auditor@blockchain-forensics.com
Passwort:   Auditor2025!
Rolle:      auditor
Plan:       business
Zugriff:    Security & Compliance Dashboard
```

---

## 🛡️ **ADMIN-ZUGRIFFE**

### **Was Admins sehen (EXKLUSIV):**

#### **Dashboard Hub:**
```
✅ Admin-Filter sichtbar (normale User sehen das NICHT)
✅ Alle 16 Dashboards zugänglich:
   - 6 Forensik-Dashboards
   - 4 Analytics-Dashboards
   - 6 Admin-Dashboards ⭐
```

#### **Sidebar Navigation:**
```
✅ Alle User-Links (Forensik/Analytics)
✅ Plus Admin-Links (nur für Admins):
   - Analytics (Graph Analytics)
   - Web Analytics (User-Tracking)
   - Monitoring
   - Monitoring Dashboard
   - Organizations
   - Admin Panel
```

#### **Admin-Dashboards (6):**
```
1. System Monitoring      → /monitoring/dashboard
2. User Analytics         → /web-analytics
3. Onboarding Analytics   → /admin/onboarding-analytics
4. Security & Compliance  → /security
5. Admin Panel            → /admin
6. Organizations          → /orgs
```

---

## 🚫 **WAS NORMALE USER NICHT SEHEN**

### **Dashboard Hub:**
```
❌ Admin-Filter (Tab ist komplett ausgeblendet)
❌ Admin-Dashboards (werden nicht angezeigt)
❌ Admin-Badge (keine Hinweise auf Admin-Features)
```

### **Sidebar:**
```
❌ Analytics (Graph)
❌ Web Analytics
❌ Monitoring
❌ Monitoring Dashboard
❌ Organizations
❌ Admin Panel
```

### **Routes:**
```
❌ /monitoring/dashboard  → 403 Forbidden
❌ /web-analytics         → 403 Forbidden
❌ /admin                 → 403 Forbidden
❌ /orgs                  → 403 Forbidden
❌ /security              → 403 Forbidden (außer Auditor)
```

---

## 🔧 **ADMIN-SETUP IM BACKEND**

### **Account erstellen (PostgreSQL):**
```sql
-- Admin-Account erstellen
INSERT INTO users (
  email,
  username,
  password_hash, -- BCrypt-Hash von "Admin2025!Secure"
  role,
  plan,
  is_active,
  email_verified,
  created_at
) VALUES (
  'admin@blockchain-forensics.com',
  'admin',
  '$2b$12$...',  -- Hash generieren mit bcrypt
  'admin',
  'enterprise',
  true,
  true,
  NOW()
);

-- Test-Accounts erstellen
INSERT INTO users (email, username, password_hash, role, plan, is_active, email_verified) VALUES
  ('test-community@blockchain-forensics.com', 'test-community', '$2b$12$...', 'user', 'community', true, true),
  ('test-pro@blockchain-forensics.com', 'test-pro', '$2b$12$...', 'user', 'pro', true, true),
  ('test-business@blockchain-forensics.com', 'test-business', '$2b$12$...', 'user', 'business', true, true),
  ('test-plus@blockchain-forensics.com', 'test-plus', '$2b$12$...', 'user', 'plus', true, true);
```

### **Password-Hashes generieren (Python):**
```python
import bcrypt

passwords = {
    "Admin2025!Secure": "admin",
    "Community2025!": "community",
    "Pro2025!": "pro",
    "Business2025!": "business",
    "Plus2025!": "plus",
}

for password, name in passwords.items():
    hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    print(f"{name}: {hash.decode('utf-8')}")
```

### **CLI-Command (Alternative):**
```bash
# Admin-Account erstellen
cd backend
python -m app.cli.create_admin \
  --email admin@blockchain-forensics.com \
  --password "Admin2025!Secure" \
  --username admin
```

---

## 🔒 **SICHERHEITSRICHTLINIEN**

### **Passwort-Anforderungen:**
```
✅ Mindestens 12 Zeichen
✅ Großbuchstaben
✅ Kleinbuchstaben
✅ Zahlen
✅ Sonderzeichen
✅ Keine häufigen Passwörter
```

### **Admin-Account-Schutz:**
```
✅ 2FA/MFA aktivieren (empfohlen)
✅ IP-Whitelist konfigurieren
✅ Session-Timeout: 2 Stunden
✅ Login-Versuche: Max 3
✅ Account-Lock nach 3 Fehlversuchen
```

### **Audit-Logging:**
```
✅ Alle Admin-Aktionen werden geloggt
✅ Login/Logout-Events
✅ Dashboard-Zugriffe
✅ Datenänderungen
✅ Export nach /var/log/admin-audit.log
```

---

## 📊 **ADMIN-ÜBERSICHT**

### **Was Admins tun können:**

#### **1. User Analytics (Marketing):**
```
- User-Bewegungen tracken
- Conversion-Funnels analysieren
- A/B-Tests auswerten
- Onboarding-Drop-offs identifizieren
```

#### **2. System Monitoring:**
```
- System Health überwachen
- Performance-Metriken anzeigen
- Error-Rates tracken
- Uptime überwachen
```

#### **3. User Management:**
```
- User erstellen/bearbeiten/löschen
- Pläne upgraden/downgraden
- Accounts sperren/entsperren
- Passwörter zurücksetzen
```

#### **4. Organization Management:**
```
- Multi-Tenant Orgs verwalten
- Team-Mitglieder zuweisen
- Permissions konfigurieren
- Billing verwalten
```

#### **5. Security & Compliance:**
```
- Security-Audits durchführen
- Compliance-Reports generieren
- Access-Logs prüfen
- Incidents dokumentieren
```

#### **6. Onboarding Analytics:**
```
- Onboarding-Erfolgsrate tracken
- Tour-Completion-Rate analysieren
- Drop-off-Points identifizieren
- Optimierungs-Empfehlungen
```

---

## 🚀 **QUICK START GUIDE FÜR ADMINS**

### **1. Login:**
```
1. Gehe zu http://localhost:3000/login
2. Email: admin@blockchain-forensics.com
3. Passwort: Admin2025!Secure
4. Login klicken
```

### **2. Dashboard Hub öffnen:**
```
1. Nach Login automatisch zu /dashboard
2. Du siehst 4 Filter-Tabs:
   - Alle (16)
   - Forensik (6)
   - Analytics (4)
   - Admin (6) ⭐ NUR FÜR ADMINS SICHTBAR
```

### **3. Admin-Features nutzen:**
```
1. Klicke auf "Admin"-Filter
2. Du siehst 6 Admin-Dashboards
3. Klicke auf "User Analytics"
4. Siehst User-Bewegungen, Funnels, etc.
```

### **4. Sidebar nutzen:**
```
- Unten in Sidebar: Admin-Links
- Web Analytics → User-Tracking
- Monitoring → System-Health
- Admin → User-Management
- Orgs → Multi-Tenant Admin
```

---

## ⚠️ **WICHTIGE HINWEISE**

### **Nach Deployment:**
```
1. ✅ Standard-Passwörter SOFORT ändern!
2. ✅ 2FA für alle Admin-Accounts aktivieren
3. ✅ Test-Accounts in Production LÖSCHEN
4. ✅ IP-Whitelist konfigurieren
5. ✅ Audit-Logging aktivieren
```

### **Regelmäßig:**
```
1. ✅ Passwörter alle 90 Tage ändern
2. ✅ Inaktive Admin-Accounts deaktivieren
3. ✅ Access-Logs prüfen
4. ✅ Security-Audits durchführen
```

---

## 📞 **SUPPORT**

### **Bei Problemen:**
```
Admin-Support: admin-support@blockchain-forensics.com
Notfall-Hotline: +49 XXX XXXXXXX
Dokumentation: /docs/admin-guide.md
```

---

## ✅ **ZUSAMMENFASSUNG**

### **Admin-Login:**
```
Email:    admin@blockchain-forensics.com
Password: Admin2025!Secure
```

### **Admin-Zugriffe:**
```
✅ 16 Dashboards (alle)
✅ 6 Admin-Dashboards (exklusiv)
✅ User Management
✅ System Monitoring
✅ Analytics (Marketing)
✅ Security & Compliance
```

### **User-Trennung:**
```
✅ Admin-Filter NUR für Admins sichtbar
✅ Admin-Links NUR in Admin-Sidebar
✅ Normale User sehen KEINE Admin-Features
✅ Klare Trennung User/Admin
```

**ADMIN-SYSTEM IST BEREIT! 🔐**
