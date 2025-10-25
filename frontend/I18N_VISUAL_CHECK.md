# 🎨 I18N Visual Check - Vor dem Go-Live

## ✅ Checkliste für manuelle Tests

### 1. Sprachen-Auswahl testen

```bash
npm run dev
# → http://localhost:5173 öffnen
```

**Test-Schritte:**
- [ ] Navbar → Language Selector öffnen
- [ ] Sollte **42 Sprachen** mit Flags zeigen
- [ ] Jede Sprache auswählen → Seite sollte wechseln
- [ ] Browser Reload → Sprache sollte persistent sein

---

### 2. Top 5 Sprachen vollständig testen

#### ✅ Deutsch (de) 🇩🇪
```
Navbar → Language: Deutsch
```

**Prüfen:**
- [ ] Landing Page: "Enterprise Blockchain Intelligence"
- [ ] Pricing: Preise in **EUR** (€1.234 Format)
- [ ] About: "Über uns" Überschrift
- [ ] Footer: "Alle Rechte vorbehalten"
- [ ] Navigation: Deutsche Beschriftungen

#### ✅ Englisch (en) 🇺🇸
```
Navbar → Language: English
```

**Prüfen:**
- [ ] Landing Page: Englischer Text
- [ ] Pricing: Preise in **USD** ($1,234 Format)
- [ ] About: "About" Heading
- [ ] Footer: "All rights reserved"

#### ✅ Französisch (fr) 🇫🇷
```
Navbar → Language: Français
```

**Prüfen:**
- [ ] Landing Page: Französischer Text
- [ ] Pricing: Preise in **EUR** (1 234 € Format)
- [ ] About: "À propos" Heading

#### ✅ Spanisch (es) 🇪🇸
```
Navbar → Language: Español
```

**Prüfen:**
- [ ] Landing Page: Spanischer Text
- [ ] Pricing: Preise in **EUR** (1.234 € Format)
- [ ] About: "Acerca de" Heading

#### ✅ Italienisch (it) 🇮🇹
```
Navbar → Language: Italiano
```

**Prüfen:**
- [ ] Landing Page: Italienischer Text
- [ ] Pricing: Preise in **EUR** (1.234 € Format)

---

### 3. Währungen testen (Top 10)

| Sprache | Code | Erwartete Währung | Beispiel | Prüfen |
|---------|------|-------------------|----------|--------|
| Deutsch | de | EUR | 999 € | [ ] |
| Englisch | en | USD | $999 | [ ] |
| Schwedisch | sv | SEK | 999 kr | [ ] |
| Polnisch | pl | PLN | 999 zł | [ ] |
| Japanisch | ja | JPY | ¥999 | [ ] |
| Koreanisch | ko | KRW | ₩999 | [ ] |
| Norwegisch | nb | NOK | 999 kr | [ ] |
| Türkisch | tr | TRY | ₺999 | [ ] |
| Ukrainisch | uk | UAH | 999 ₴ | [ ] |
| Chinesisch | zh-CN | CNY | ¥999 | [ ] |

**Test:**
```
1. Pricing Page öffnen
2. Sprache wechseln
3. Währungssymbol + Formatierung prüfen
```

---

### 4. RTL (Right-to-Left) testen

#### ✅ Arabisch (ar) 🇸🇦
```
Navbar → Language: العربية
```

**Prüfen:**
- [ ] `<html dir="rtl">` gesetzt
- [ ] Navigation rechts → links
- [ ] Text rechts-ausgerichtet
- [ ] Währung: USD (arabische Länder nutzen oft USD)

**Visual Check:**
```
+----------------------------------+
|              Navigation       ☰  |
| العربية                          |
|                                  |
|     تحليلات البلوكشين            |
|     للشركات الرقمية             |
+----------------------------------+
```

---

### 5. SEO & hreflang prüfen

```bash
# Browser DevTools öffnen (F12)
# → Elements Tab
# → <head> inspizieren
```

**Sollte vorhanden sein:**
```html
<!-- Canonical -->
<link rel="canonical" href="https://sigmacode.io/pricing" />

<!-- x-default -->
<link rel="alternate" hreflang="x-default" href="https://sigmacode.io/pricing" />

<!-- Alle 42 Sprachen -->
<link rel="alternate" hreflang="de" href="https://sigmacode.io/de/pricing" />
<link rel="alternate" hreflang="fr" href="https://sigmacode.io/fr/pricing" />
<link rel="alternate" hreflang="es" href="https://sigmacode.io/es/pricing" />
<link rel="alternate" hreflang="it" href="https://sigmacode.io/it/pricing" />
<!-- ... 38 weitere -->
```

**Prüfung:**
- [ ] `rel="canonical"` vorhanden
- [ ] `hreflang="x-default"` vorhanden
- [ ] Mindestens **42 hreflang Tags**
- [ ] URLs korrekt formatiert

---

### 6. Responsive Design

#### Desktop (1920x1080)
- [ ] Language Selector in Navbar sichtbar
- [ ] Dropdown mit allen 42 Sprachen funktioniert
- [ ] Flags werden angezeigt

#### Tablet (768x1024)
- [ ] Language Selector in Mobile Menu
- [ ] Alle Sprachen erreichbar

#### Mobile (375x667)
- [ ] Hamburger Menu → Languages
- [ ] Touch-friendly Auswahl
- [ ] Kein horizontal Scroll

---

### 7. Performance Check

```bash
# Build erstellen
npm run build

# Bundle Size prüfen
ls -lh dist/assets/*.js | grep -i "locale\|i18n"
```

**Erwartung:**
- Jede Sprache: ~50KB
- Total für 42 Sprachen: ~2.1MB
- Gzip: ~600KB

**Akzeptabel für:**
- ✅ Breitband (< 1 Sekunde)
- ✅ Mobile 4G (< 3 Sekunden)
- 🟡 Mobile 3G (< 10 Sekunden)

---

### 8. Browser-Kompatibilität

#### ✅ Chrome/Edge (Chromium)
- [ ] Language Detection funktioniert
- [ ] Währungsformatierung korrekt
- [ ] Flags werden angezeigt

#### ✅ Firefox
- [ ] Gleiche Tests wie Chrome
- [ ] Intl API unterstützt

#### ✅ Safari (Mac/iOS)
- [ ] Währungssymbole korrekt (€, $, £, ¥)
- [ ] Keine Font-Issues bei Flags

---

### 9. Fallback-Verhalten testen

**Szenario:** Fehlender Key in Sprache

```typescript
// Beispiel: Ein Key existiert in en.json, aber nicht in de.json
"missing.key": "This is only in English"
```

**Erwartung:**
- Sprache: Deutsch → Sollte **englischen** Fallback zeigen
- Keine Fehlermeldung im Console
- Keine leeren Strings

**Test:**
```
1. Browser Console öffnen
2. Nach "missing" oder "undefined" suchen
3. Sollte nichts finden
```

---

### 10. Console Errors prüfen

```bash
npm run dev
# → Browser Console öffnen (F12 → Console)
```

**Sollte KEINE Errors zeigen:**
- ❌ "Translation key not found"
- ❌ "Failed to load locale"
- ❌ "Currency undefined"
- ❌ "Invalid hreflang"

**OK wenn:**
- ⚠️ Warnings über fehlende experimentelle Keys (agent.*, corr.*)

---

## 📊 Schnell-Check Tabelle

### Haupt-Features

| Feature | Status | Getestet |
|---------|--------|----------|
| **42 Sprachen auswählbar** | ✅ | [ ] |
| **Währungen automatisch** | ✅ | [ ] |
| **SEO hreflang Tags** | ✅ | [ ] |
| **RTL für Arabisch** | ✅ | [ ] |
| **Landing Page übersetzt** | ✅ | [ ] |
| **Pricing Page übersetzt** | ✅ | [ ] |
| **About Page übersetzt** | ✅ | [ ] |
| **Navigation übersetzt** | ✅ | [ ] |
| **Footer übersetzt** | ✅ | [ ] |

### Technisch

| Technisch | Status | Getestet |
|-----------|--------|----------|
| **Keine Console Errors** | ✅ | [ ] |
| **Bundle Size < 3MB** | ✅ | [ ] |
| **Load Time < 5s** | ✅ | [ ] |
| **Mobile-friendly** | ✅ | [ ] |
| **Browser-kompatibel** | ✅ | [ ] |

---

## 🎯 Go-Live Kriterien

### MUST HAVE (Blocker)
- [ ] Top 5 Sprachen (de, en, fr, es, it) vollständig getestet
- [ ] Währungen für EUR, USD, GBP korrekt
- [ ] SEO: hreflang Tags vorhanden
- [ ] Keine kritischen Console Errors
- [ ] Mobile Navigation funktioniert

### SHOULD HAVE (Nice to have)
- [ ] Alle 42 Sprachen getestet
- [ ] Alle 24 Währungen geprüft
- [ ] RTL perfekt für Arabisch
- [ ] Performance < 3s Load Time
- [ ] Bundle optimiert

### COULD HAVE (Post-Launch)
- [ ] A/B Testing verschiedener Übersetzungen
- [ ] Analytics pro Sprache
- [ ] Geo-IP basierte Auto-Erkennung
- [ ] Lazy Loading für Sprachen

---

## 🚀 Final Check vor Deployment

```bash
# 1. Linter
npm run lint

# 2. Build
npm run build

# 3. I18N Check
npm run i18n:check

# 4. Preview
npm run preview

# 5. Manual Tests (diese Checkliste)
# → Alle oben durchgehen

# 6. Deploy!
```

---

## 📞 Support Checkliste

**Falls Probleme auftreten:**

### Sprache wird nicht angezeigt
```bash
# Prüfen ob importiert
cat src/i18n/config.ts | grep "import.*Translations"
# Sollte alle 42 Sprachen zeigen
```

### Falsche Währung
```typescript
// In Browser Console
import { CURRENCY_MAP } from '@/contexts/I18nContext'
console.log(CURRENCY_MAP)
// Prüfe ob Sprache → Währung korrekt gemappt
```

### hreflang fehlt
```javascript
// In Browser Console
document.querySelectorAll('link[rel="alternate"][hreflang]').length
// Sollte >= 42 sein
```

### Übersetzung fehlt
```bash
npm run i18n:check
# Zeigt fehlende Keys
```

---

**Ende des Visual Checks**  
**Vor Go-Live:** Alle [ ] abhaken!
