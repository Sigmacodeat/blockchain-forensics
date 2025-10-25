# I18N Documentation - Blockchain Forensics Frontend

## 📚 Übersicht

Die Anwendung unterstützt **41 Sprachen** mit vollständiger Lokalisierung für alle UI-Komponenten.

### Unterstützte Sprachen

#### Tier 1 (Core-Sprachen, vorgeladen)
- 🇩🇪 **Deutsch** (de)
- 🇬🇧 **Englisch** (en) - Fallback
- 🇳🇱 **Niederländisch** (nl)
- 🇫🇷 **Französisch** (fr)
- 🇪🇸 **Spanisch** (es)

#### Tier 2 (Wichtige Märkte, lazy-loaded)
- 🇮🇹 Italienisch (it)
- 🇵🇹 Portugiesisch (pt)
- 🇷🇺 Russisch (ru)
- 🇵🇱 Polnisch (pl)
- 🇮🇱 Hebräisch (he)
- 🇷🇴 Rumänisch (ro)
- 🇺🇦 Ukrainisch (uk)
- 🇬🇷 Griechisch (el)
- 🇧🇬 Bulgarisch (bg)

#### Tier 3 (Weitere Sprachen, lazy-loaded)
- 🇸🇦 Arabisch (ar)
- 🇮🇳 Hindi (hi)
- 🇯🇵 Japanisch (ja)
- 🇰🇷 Koreanisch (ko)
- 🇨🇳 Chinesisch (zh-CN)
- ... und 22 weitere

**Vollständige Liste:** Siehe `src/i18n/config-optimized.ts` → `AVAILABLE_LANGUAGES`

## 🏗️ Architektur

### Dateistruktur
```
frontend/
├── src/
│   ├── i18n/
│   │   ├── config-optimized.ts    # i18next-Konfiguration
│   │   └── index.ts                # Export
│   └── locales/
│       ├── en.json                 # Englisch (Basis)
│       ├── de.json                 # Deutsch
│       ├── nl.json                 # Niederländisch
│       ├── fr.json                 # Französisch
│       └── ... (41 Sprachen total)
├── scripts/
│   └── audit-locales.mjs          # Qualitäts-Audit-Tool
└── I18N_TEST_CHECKLIST.md         # Testing-Guide
```

### Technologie-Stack
- **Framework:** `i18next` + `react-i18next`
- **Lazy Loading:** `i18next-http-backend`
- **Detection:** `i18next-browser-languagedetector`
- **Storage:** LocalStorage + Cookies

## 🔧 Konfiguration

### Core-Config (`src/i18n/config-optimized.ts`)

```typescript
// Kernsprachen (vorgeladen)
const CORE_LANGUAGES = new Set(['en', 'de', 'fr', 'es', 'nl']);

// Features
i18n
  .use(Backend)               // Lazy Loading
  .use(LanguageDetector)      // Browser-Detection
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    supportedLngs: [...],     // Alle 41 Sprachen
    load: 'languageOnly',     // Keine regionalen Varianten
    interpolation: {
      escapeValue: false      // React escaped bereits
    }
  });
```

### Detection-Reihenfolge
1. **Query-String:** `?lng=de`
2. **LocalStorage:** `user_language`
3. **Cookie:** `user_language`
4. **Browser:** `navigator.language`
5. **Fallback:** `en`

## 📝 Verwendung im Code

### Hooks

```tsx
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t, i18n } = useTranslation();
  
  return (
    <div>
      <h1>{t('landing.hero.title')}</h1>
      <p>{t('landing.hero.subtitle')}</p>
      
      {/* Sprachwechsel */}
      <button onClick={() => i18n.changeLanguage('de')}>
        Deutsch
      </button>
    </div>
  );
}
```

### Verschachtelung

```json
{
  "navigation": {
    "home": "Home",
    "dashboard": "Dashboard",
    "features": "Features"
  }
}
```

```tsx
t('navigation.home')      // "Home"
t('navigation.dashboard') // "Dashboard"
```

### Pluralisierung

```json
{
  "items": "{{count}} item",
  "items_plural": "{{count}} items"
}
```

```tsx
t('items', { count: 1 })  // "1 item"
t('items', { count: 5 })  // "5 items"
```

### Interpolation

```json
{
  "welcome": "Welcome, {{name}}!"
}
```

```tsx
t('welcome', { name: 'John' })  // "Welcome, John!"
```

## 🌍 Neue Sprache hinzufügen

### 1. Locale-Datei erstellen
```bash
cd frontend/src/locales
cp en.json xx.json  # xx = neuer Sprach-Code
```

### 2. Übersetzen
- Alle Keys aus `en.json` beibehalten
- Nur Values übersetzen
- **Namespaced-Keys** (`agent.*`, `corr.*`) können unübersetzt bleiben

### 3. Zur Config hinzufügen
```typescript
// src/i18n/config-optimized.ts
export const AVAILABLE_LANGUAGES = new Set([
  // ...bestehende
  'xx'  // Neue Sprache
]);
```

### 4. Qualitäts-Check
```bash
node scripts/audit-locales.mjs
```

## 🔍 Audit-Tool

### Verwendung
```bash
cd frontend
node scripts/audit-locales.mjs
```

### Output
```
📊 Translation Quality Report
Found 41 language files

┌──────┬───────────┬────────────────┬─────────────┬──────────┐
│ code │ totalKeys │ completeness   │ sameAsEn    │ missing  │
├──────┼───────────┼────────────────┼─────────────┼──────────┤
│ de   │ 1048      │ 100.0%         │ 12          │ 0        │
│ nl   │ 1048      │ 100.0%         │ 319         │ 0        │
│ ...  │           │                │             │          │
└──────┴───────────┴────────────────┴─────────────┴──────────┘
```

### Metriken erklärt
- **totalKeys:** Anzahl der Keys in der Datei
- **completeness:** % der vorhandenen Übersetzungen
- **sameAsEn:** Keys mit identischem Wert wie EN
- **missing:** Fehlende Keys
- **englishish:** Keys mit englischen Wörtern (z.B. "Dashboard")
- **namespaced:** Keys im Format `namespace.key` (absichtlich)

## 🎨 Best Practices

### DO ✅
- **Konsistente Key-Struktur:** `section.subsection.key`
- **Kurze Keys:** `nav.home` statt `navigation.homeButton`
- **Plural-Forms:** Nutze i18next Pluralisierung
- **Namespaces für Features:** `dashboard.*`, `alerts.*`
- **Technische Begriffe:** Lasse international gebräuchliche Terme (z.B. "API", "Dashboard")

### DON'T ❌
- **Hardcoded Strings:** Immer `t()` verwenden
- **Keys löschen:** Führt zu Fehlern in anderen Sprachen
- **Inkonsistente Struktur:** `nav.home` vs `navigation.homeButton`
- **Lange Texte in Keys:** Nutze kurze, beschreibende Keys
- **HTML in Translations:** Verwende Components

### Namespaced-Keys
Einige Keys sind **absichtlich nicht übersetzt** (Platzhalter):
```json
{
  "agent": {
    "title": "agent.title",
    "loading": "agent.loading"
  }
}
```
Diese werden später dynamisch gefüllt oder sind technische Referenzen.

## 🌐 RTL-Support (Right-to-Left)

### Unterstützte RTL-Sprachen
- **Arabisch** (ar)
- **Hebräisch** (he)

### Automatische Anpassung
```tsx
// i18n erkennt RTL automatisch
const isRTL = i18n.dir() === 'rtl';

// In Tailwind/CSS
<div className={isRTL ? 'rtl' : 'ltr'}>
  {/* Content */}
</div>
```

### RTL-Testing
- Layout-Richtung
- Icon-Positionierung
- Textausrichtung
- Scroll-Behavior

## 🚀 Performance

### Lazy Loading
- **Core-Sprachen** (EN, DE, FR, ES, NL): Vorgeladen
- **Andere Sprachen:** Lazy-loaded beim ersten Zugriff
- **Caching:** Translations werden im Browser gecacht

### Optimierungen
```typescript
// Nur benötigte Namespaces laden
useTranslation(['dashboard', 'navigation']);

// Suspense für Lazy Loading
<Suspense fallback={<Loading />}>
  <MyComponent />
</Suspense>
```

### Bundle-Size
- EN (Base): ~50 KB
- Durchschnittliche Sprache: ~52 KB
- Total (alle 41): ~2.1 MB (lazy-loaded!)

## 🧪 Testing

### Unit-Tests
```tsx
import { renderWithI18n } from '@/test-utils';

test('renders translated text', () => {
  const { getByText } = renderWithI18n(<MyComponent />, {
    lng: 'de'
  });
  expect(getByText('Willkommen')).toBeInTheDocument();
});
```

### E2E-Tests (Playwright)
```typescript
test('changes language', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="language-selector"]');
  await page.click('text=Deutsch');
  await expect(page.locator('h1')).toContainText('Willkommen');
});
```

### Manuelle Tests
Siehe `I18N_TEST_CHECKLIST.md`

## 📊 Qualitäts-Standards

### Vollständigkeit
- ✅ **100%** aller Keys übersetzt
- ✅ Keine fehlenden Translations
- ✅ Konsistente Struktur

### Qualität
- ⚠️ **< 5%** identisch zu EN (außer technische Begriffe)
- ⚠️ **< 10%** englische Wörter (außer "Dashboard", "API")
- ✅ Namespaced-Keys erlaubt

### Performance
- ✅ Initial Load < 2s
- ✅ Sprachwechsel < 500ms
- ✅ Lazy Load < 1s

## 🔧 Troubleshooting

### Problem: "Translation not found"
**Lösung:**
1. Prüfe, ob Key in `en.json` existiert
2. Führe Audit aus: `node scripts/audit-locales.mjs`
3. Synchronisiere fehlende Keys

### Problem: Sprache wechselt nicht
**Lösung:**
```javascript
// Console-Check
localStorage.getItem('user_language')
document.cookie

// Manuell setzen
i18n.changeLanguage('de')
```

### Problem: Lazy Load funktioniert nicht
**Lösung:**
1. Prüfe Backend-Config in `config-optimized.ts`
2. Stelle sicher, dass Sprache nicht in `CORE_LANGUAGES` ist
3. Prüfe Browser-Netzwerk-Tab

### Problem: RTL-Layout kaputt
**Lösung:**
```tsx
// Automatische Direction erkennen
const { i18n } = useTranslation();
const dir = i18n.dir();

<html dir={dir}>
  {/* Content */}
</html>
```

## 📚 Weitere Ressourcen

### Dokumentation
- [i18next Docs](https://www.i18next.com/)
- [react-i18next Docs](https://react.i18next.com/)
- [ICU Message Format](https://formatjs.io/docs/core-concepts/icu-syntax/)

### Tools
- **Audit-Tool:** `scripts/audit-locales.mjs`
- **Test-Checklist:** `I18N_TEST_CHECKLIST.md`
- **Locale-Files:** `src/locales/*.json`

### Support
Bei Fragen oder Problemen:
1. Prüfe diese Dokumentation
2. Führe Audit-Tool aus
3. Teste mit Checklist
4. Erstelle GitHub Issue mit Details

---

**Letzte Aktualisierung:** 16. Oktober 2025  
**Version:** 1.0  
**Status:** ✅ Produktionsreif
