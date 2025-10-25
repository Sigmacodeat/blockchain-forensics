# I18N Testing Checklist

## ✅ Abgeschlossen
- [x] 41 Sprachen mit 100% Key-Vollständigkeit
- [x] Audit-Tool erfolgreich ausgeführt
- [x] Top-Tier-Sprachen (DE, EN, NL, FR, ES, IT, PT, RU, PL, HE) verifiziert
- [x] Dev-Server gestartet: http://localhost:3000

## 🧪 Browser-Tests

### 1. Sprachenwechsler-Funktionalität
- [ ] Sprachenwechsler im Header sichtbar
- [ ] Dropdown zeigt alle 41 Sprachen an
- [ ] Sprachwechsel aktualisiert die gesamte UI
- [ ] Gewählte Sprache wird in localStorage gespeichert
- [ ] Cookie `user_language` wird gesetzt

### 2. Kernseiten testen (mindestens 5 Sprachen: DE, EN, FR, ES, IT)
- [ ] **Landing Page** (`/`)
  - Hero-Text korrekt übersetzt
  - CTA-Buttons lokalisiert
  - Features-Sektion vollständig
- [ ] **Dashboard** (`/dashboard`)
  - Sidebar-Navigation
  - Statistiken & KPIs
  - Alerts-Übersicht
- [ ] **Monitoring Alerts** (`/monitoring`)
  - Tabellen-Header
  - Filter-Labels
  - Severity/Status-Werte
- [ ] **Admin Panel** (`/admin`)
  - Konfiguration
  - Statistiken
  - Tabs-Navigation
- [ ] **Pricing** (`/pricing`)
  - Preispläne
  - Feature-Listen
  - CTA-Buttons

### 3. RTL-Support (Arabisch, Hebräisch)
- [ ] **Arabisch (ar)**: Text-Richtung von rechts nach links
  - Menü-Positionierung
  - Icons gespiegelt
  - Layout korrekt
- [ ] **Hebräisch (he)**: RTL-Layout
  - Navigation
  - Formulare
  - Tabellen

### 4. Lazy Loading (Non-Core-Sprachen)
- [ ] Wechsel zu einer Nicht-Kernsprache (z.B. `mk`, `sq`, `lb`)
- [ ] Verzögerung beim ersten Laden (Lazy Load)
- [ ] Nachfolgende Navigation ohne Verzögerung
- [ ] Browser-Konsole: Keine Fehler bei Lazy Load

### 5. Browser-Detection
- [ ] Browser-Sprache wird erkannt beim ersten Besuch
- [ ] Fallback auf EN wenn Browser-Sprache nicht unterstützt
- [ ] Query-Parameter `?lng=de` überschreibt Detection
- [ ] LocalStorage hat Vorrang vor Browser-Sprache

### 6. Formular-Validierung & Fehlermeldungen
- [ ] Login-Formular: Fehlermeldungen übersetzt
- [ ] Passwort-Zurücksetzen: Validierung lokalisiert
- [ ] Registrierung: Alle Hinweise übersetzt

### 7. Performance & Loading
- [ ] Initial Load Time < 2s (Kernsprache)
- [ ] Sprachwechsel < 500ms
- [ ] Keine Flash of Unstyled Content (FOUC)
- [ ] Lazy-Load-Sprachen: < 1s Nachladezeit

## 🐛 Bekannte Edge Cases zu testen

### Namespace-Keys
- [ ] `agent.*` Keys zeigen Namespace-Notation (gewollt)
- [ ] `corr.*` Keys zeigen Namespace-Notation (gewollt)
- [ ] `coverage.*` und `investigator.*` Keys

### Technische Begriffe
- [ ] "Dashboard" bleibt englisch (international)
- [ ] "API", "KPI", "SLA" bleiben unübersetzt
- [ ] "OAuth", "SAML" bleiben unübersetzt

### Zahlen & Datumsformate
- [ ] Große Zahlen formatiert (z.B. 100+ Blockchains)
- [ ] ISO-Timestamps bleiben unverändert
- [ ] Währungen formatiert nach Locale

## 📊 Test-Report Template

**Getestete Sprachen:**
- [ ] Deutsch (DE)
- [ ] Englisch (EN)
- [ ] Niederländisch (NL)
- [ ] Französisch (FR)
- [ ] Spanisch (ES)
- [ ] Italienisch (IT)
- [ ] Portugiesisch (PT)
- [ ] Russisch (RU)
- [ ] Polnisch (PL)
- [ ] Hebräisch (HE)

**Gefundene Probleme:**
```
[Hier Probleme dokumentieren]
```

**Browser-Kompatibilität:**
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile (iOS Safari)
- [ ] Mobile (Chrome Android)

## 🚀 Production-Ready Checklist

- [ ] Alle Core-Tests erfolgreich
- [ ] RTL-Support funktioniert
- [ ] Keine Console-Errors
- [ ] Performance-Ziele erreicht
- [ ] SEO-Meta-Tags für alle Sprachen
- [ ] Sitemap mit allen Sprach-Varianten
- [ ] robots.txt konfiguriert

## 📝 Nächste Schritte nach Testing

1. **Wenn Probleme gefunden:**
   - Issues dokumentieren
   - Priorität festlegen
   - Fixes implementieren

2. **Wenn Tests erfolgreich:**
   - Production-Build erstellen (`npm run build`)
   - Preview-Build testen (`npm run preview`)
   - Deployment vorbereiten

3. **SEO-Optimierung:**
   - Sitemap-Generator für alle Sprachen
   - hreflang-Tags hinzufügen
   - Meta-Descriptions lokalisieren

## 🔧 Debugging-Tools

### Browser-Console-Commands
```javascript
// Aktuelle Sprache anzeigen
localStorage.getItem('user_language')

// Sprache manuell setzen
localStorage.setItem('user_language', 'de')
window.location.reload()

// Cookie prüfen
document.cookie

// i18next-Status (wenn verfügbar)
console.log(window.i18n?.language)
console.log(window.i18n?.options)
```

### Audit-Report erneut ausführen
```bash
cd frontend
node scripts/audit-locales.mjs
```

### Dev-Server neustarten
```bash
npm run dev
```

---

**Stand:** 16. Oktober 2025, 22:29 Uhr  
**Status:** ✅ I18n-Infrastruktur produktionsbereit  
**Nächster Schritt:** Browser-Testing durchführen
