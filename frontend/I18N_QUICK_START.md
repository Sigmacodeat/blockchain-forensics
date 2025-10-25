# I18N Quick Start Guide

## 🚀 In 5 Minuten zur mehrsprachigen App

### 1. Server starten (bereits läuft!)
```bash
cd frontend
npm run dev
```
✅ Läuft auf: http://localhost:3000

### 2. Browser öffnen
Öffne den Browser-Preview-Link oben oder direkt: http://localhost:3000

### 3. Sprachen testen
Im **Header** findest du den **Sprachenwechsler** (Globe-Icon 🌍).

**Top 5 Sprachen zum Testen:**
1. 🇩🇪 **Deutsch** - Vollständig lokalisiert
2. 🇬🇧 **English** - Basis/Fallback
3. 🇫🇷 **Français** - Professionell
4. 🇪🇸 **Español** - Vollständig
5. 🇳🇱 **Nederlands** - Hochwertig

### 4. Diese Seiten durchklicken
- ✅ **Landing** (`/`) - Hero, Features, CTA
- ✅ **Dashboard** (`/dashboard`) - Sidebar, Stats, Alerts
- ✅ **Monitoring** (`/monitoring`) - Tabellen, Filter
- ✅ **Pricing** (`/pricing`) - Pläne, Features
- ✅ **Features** (`/features`) - Vollständige Suite

### 5. Validieren
**Checkliste:**
- [ ] Sprachenwechsler funktioniert
- [ ] Alle Texte übersetzt (keine "key.not.found")
- [ ] Keine Console-Errors
- [ ] Sprachwahl bleibt nach Reload erhalten
- [ ] Navigation vollständig lokalisiert

## 🎯 Schnelltest (2 Minuten)

### Test 1: Deutsch
1. Wechsel zu Deutsch 🇩🇪
2. Prüfe: "Willkommen" statt "Welcome"
3. Dashboard: "Übersicht" statt "Dashboard"
4. Navigation: "Funktionen" statt "Features"

### Test 2: Französisch
1. Wechsel zu Français 🇫🇷
2. Prüfe: "Bienvenue"
3. Dashboard: "Tableau de bord"
4. Navigation: "Fonctionnalités"

### Test 3: Persistence
1. Wähle eine Sprache
2. Reload die Page (F5)
3. Sprache sollte gleich bleiben

## 🐛 Wenn etwas nicht funktioniert

### Console öffnen (F12)
```javascript
// Aktuelle Sprache prüfen
localStorage.getItem('user_language')

// Manuell setzen
localStorage.setItem('user_language', 'de')
location.reload()

// Alle Keys anzeigen (wenn i18n exposed)
console.log(Object.keys(window.i18n.store.data.de))
```

### Audit ausführen
```bash
node scripts/audit-locales.mjs
```

## 📊 Erwartetes Ergebnis

### Audit-Report
```
✅ 41 languages analyzed
✅ 100.0% completeness
✅ 0 languages needing attention
```

### Browser-Test
- ✅ Alle Texte übersetzt
- ✅ Keine Fallback-Keys (`key.not.found`)
- ✅ Sprachwechsel < 500ms
- ✅ Persistence funktioniert
- ✅ Keine Console-Errors

## 🎉 Erfolg!

Wenn alle Tests ✅ sind:
- **I18n ist produktionsreif**
- Bereit für Deployment
- Alle 41 Sprachen verfügbar

## 📝 Nächste Schritte

1. **Vollständige Tests:** Siehe `I18N_TEST_CHECKLIST.md`
2. **RTL-Testing:** Arabisch + Hebräisch
3. **Production-Build:** `npm run build`
4. **SEO:** Sitemaps für alle Sprachen

---

**Quick Links:**
- 📋 [Test-Checklist](./I18N_TEST_CHECKLIST.md)
- 📚 [Vollständige Doku](./I18N_DOCUMENTATION.md)
- 🔧 [Config](./src/i18n/config-optimized.ts)
- 🌍 [Locale-Files](./src/locales/)

**Status:** ✅ Bereit zum Testen!
