# 🌍 I18N Quick Reference Guide

## Schnellstart

```bash
# Fehlende Übersetzungen finden
npm run i18n:check

# Detaillierten Report ansehen
npm run i18n:report

# Audit-Report lesen
npm run i18n:audit
```

---

## Verfügbare Sprachen (42)

```typescript
import { LANGUAGES } from '@/contexts/I18nContext'

// Alle Sprachen anzeigen
console.log(LANGUAGES) // Array von 42 Sprachen
```

| Code | Sprache | Native Name | Flag |
|------|---------|-------------|------|
| en | English | English | 🇺🇸 |
| de | German | Deutsch | 🇩🇪 |
| fr | French | Français | 🇫🇷 |
| es | Spanish | Español | 🇪🇸 |
| it | Italian | Italiano | 🇮🇹 |
| pt | Portuguese | Português | 🇵🇹 |
| nl | Dutch | Nederlands | 🇳🇱 |
| pl | Polish | Polski | 🇵🇱 |
| cs | Czech | Čeština | 🇨🇿 |
| sk | Slovak | Slovenčina | 🇸🇰 |
| hu | Hungarian | Magyar | 🇭🇺 |
| ro | Romanian | Română | 🇷🇴 |
| bg | Bulgarian | Български | 🇧🇬 |
| el | Greek | Ελληνικά | 🇬🇷 |
| sl | Slovenian | Slovenščina | 🇸🇮 |
| sr | Serbian | Српски | 🇷🇸 |
| bs | Bosnian | Bosanski | 🇧🇦 |
| mk | Macedonian | Македонски | 🇲🇰 |
| sq | Albanian | Shqip | 🇦🇱 |
| lt | Lithuanian | Lietuvių | 🇱🇹 |
| lv | Latvian | Latviešu | 🇱🇻 |
| et | Estonian | Eesti | 🇪🇪 |
| fi | Finnish | Suomi | 🇫🇮 |
| sv | Swedish | Svenska | 🇸🇪 |
| da | Danish | Dansk | 🇩🇰 |
| nb | Norwegian Bokmål | Norsk Bokmål | 🇳🇴 |
| nn | Norwegian Nynorsk | Nynorsk | 🇳🇴 |
| is | Icelandic | Íslenska | 🇮🇸 |
| ga | Irish | Gaeilge | 🇮🇪 |
| mt | Maltese | Malti | 🇲🇹 |
| lb | Luxembourgish | Lëtzebuergesch | 🇱🇺 |
| rm | Romansh | Rumantsch | 🇨🇭 |
| uk | Ukrainian | Українська | 🇺🇦 |
| be | Belarusian | Беларуская | 🇧🇾 |
| ru | Russian | Русский | 🇷🇺 |
| tr | Turkish | Türkçe | 🇹🇷 |
| ar | Arabic | العربية | 🇸🇦 |
| hi | Hindi | हिन्दी | 🇮🇳 |
| zh-CN | Chinese | 简体中文 | 🇨🇳 |
| ja | Japanese | 日本語 | 🇯🇵 |
| ko | Korean | 한국어 | 🇰🇷 |

---

## Währungen

```typescript
import { getCurrencyForLanguage, formatCurrency } from '@/contexts/I18nContext'

// Automatisch
const currency = getCurrencyForLanguage('de') // 'EUR'

// Mit Formatierung
formatCurrency(999.99, undefined, 'de') // '1.000 €'
formatCurrency(999.99, 'USD', 'en') // '$1,000'
```

### Währungszuordnung

| Währung | Länder/Sprachen |
|---------|-----------------|
| **EUR** | de, fr, es, it, nl, pt, el, ga, lb, mt, et, lv, lt, sk, sl, fi |
| **USD** | en, ar |
| **GBP** | en-GB |
| **CHF** | rm |
| **SEK** | sv |
| **DKK** | da |
| **NOK** | nb, nn |
| **ISK** | is |
| **PLN** | pl |
| **CZK** | cs |
| **HUF** | hu |
| **RON** | ro |
| **BGN** | bg |
| **RSD** | sr |
| **MKD** | mk |
| **ALL** | sq |
| **BAM** | bs |
| **UAH** | uk |
| **BYN** | be |
| **TRY** | tr |
| **CNY** | zh-CN |
| **JPY** | ja |
| **KRW** | ko |
| **INR** | hi |

---

## Usage in Components

### 1. Basic Translation

```tsx
import { useTranslation } from 'react-i18next'

function MyComponent() {
  const { t } = useTranslation()
  
  return <h1>{t('landing.hero.title')}</h1>
}
```

### 2. Mit Parametern

```tsx
const { t } = useTranslation()

<p>{t('pricing.toggle.save', { pct: 20 })}</p>
// Output: "Spare 20%" (de) oder "Save 20%" (en)
```

### 3. Sprache wechseln

```tsx
import { useI18n } from '@/contexts/I18nContext'

function LanguageSwitcher() {
  const { currentLanguage, setLanguage, languages } = useI18n()
  
  return (
    <select value={currentLanguage} onChange={(e) => setLanguage(e.target.value)}>
      {languages.map(lang => (
        <option key={lang.code} value={lang.code}>
          {lang.flag} {lang.nativeName}
        </option>
      ))}
    </select>
  )
}
```

### 4. Preise anzeigen

```tsx
import { useTranslation } from 'react-i18next'
import { getCurrencyForLanguage } from '@/contexts/I18nContext'

function PriceDisplay({ amount }) {
  const { i18n } = useTranslation()
  const lang = i18n.language
  const currency = getCurrencyForLanguage(lang)
  
  const formatted = new Intl.NumberFormat(lang, {
    style: 'currency',
    currency,
    maximumFractionDigits: 0
  }).format(amount)
  
  return <span>{formatted}</span>
}

// Oder einfacher:
import { formatCurrency } from '@/contexts/I18nContext'

<span>{formatCurrency(999, undefined, 'de')}</span> // '999 €'
```

### 5. Datum formatieren

```tsx
import { formatDate } from '@/contexts/I18nContext'

const dateString = formatDate(new Date(), 'de')
// Output: "16. Januar 2025"
```

---

## Translation Keys

### Struktur

```
locales/
├── en.json          # Englisch (Referenz)
├── de.json          # Deutsch
├── fr.json          # Französisch
├── es.json          # Spanisch
└── ... (38 weitere)
```

### Beispiel en.json

```json
{
  "landing": {
    "hero": {
      "title": "Enterprise Blockchain Intelligence",
      "subtitle": "AI‑driven compliance, investigations, and risk monitoring"
    }
  },
  "pricing": {
    "header": {
      "title": "The right plan for every team"
    },
    "card": {
      "per_month": "per month",
      "custom": "Custom"
    }
  }
}
```

### Keys hinzufügen

1. In `en.json` Key mit Wert hinzufügen
2. Gleichen Key in allen anderen Sprachen hinzufügen
3. Script ausführen:
   ```bash
   npm run i18n:check
   ```

---

## SEO & hreflang

Automatisch via `<SeoI18n />` Komponente in `App.tsx`:

```tsx
import SeoI18n from '@/components/SeoI18n'

function App() {
  return (
    <>
      <SeoI18n /> {/* Generiert hreflang für alle 42 Sprachen */}
      <YourApp />
    </>
  )
}
```

**Generiert:**
```html
<link rel="canonical" href="https://sigmacode.io/pricing" />
<link rel="alternate" hreflang="x-default" href="https://sigmacode.io/pricing" />
<link rel="alternate" hreflang="de" href="https://sigmacode.io/de/pricing" />
<link rel="alternate" hreflang="fr" href="https://sigmacode.io/fr/pricing" />
<!-- ... für alle 42 Sprachen -->
```

---

## RTL Support (Arabisch)

Automatisch aktiviert für `ar`:

```tsx
// In I18nContext.tsx
useEffect(() => {
  const rtlLangs = new Set(['ar', 'he', 'fa', 'ur'])
  const isRtl = rtlLangs.has(lang)
  document.documentElement.setAttribute('dir', isRtl ? 'rtl' : 'ltr')
}, [lang])
```

**Output:**
```html
<html lang="ar" dir="rtl">
```

---

## Testing

```bash
# 1. Fehlende Keys finden
npm run i18n:check

# 2. In Browser testen
npm run dev

# 3. Sprache wechseln
# → Navbar → Language Selector → Sprache auswählen

# 4. Währung prüfen
# → /pricing öffnen
# → Sprache auf 'de' → Sollte '€' zeigen
# → Sprache auf 'en' → Sollte '$' zeigen
```

---

## Troubleshooting

### Problem: "Key not found"

**Lösung:**
```bash
npm run i18n:check
# Schau in i18n-missing-keys.json, welche Keys fehlen
```

### Problem: Falsche Währung

**Check:**
```typescript
import { CURRENCY_MAP } from '@/contexts/I18nContext'
console.log(CURRENCY_MAP['de']) // Sollte 'EUR' sein
```

### Problem: hreflang Tags fehlen

**Check:**
```tsx
// SeoI18n.tsx ist in App.tsx eingebunden?
import SeoI18n from '@/components/SeoI18n'

function App() {
  return (
    <>
      <SeoI18n /> {/* ← WICHTIG! */}
      ...
    </>
  )
}
```

---

## Performance

### Bundle Size pro Sprache

Jede Sprache fügt ~50KB hinzu:
- en.json: 51KB
- de.json: 52KB
- fr.json: 55KB
- ...

**Gesamt:** ~2.1MB für alle 42 Sprachen

### Lazy Loading (Optional)

```typescript
// Statt statischen Imports
import enTranslations from '../locales/en.json'

// Dynamisch laden (Code-Splitting)
const resources = {
  en: {
    translation: () => import('../locales/en.json')
  }
}
```

→ Spart Initial Bundle Size, lädt Sprachen on-demand

---

## Checkliste für neue Sprache

- [ ] JSON-Datei in `/locales/` erstellen
- [ ] In `i18n/config.ts` importieren
- [ ] In `LANGUAGES` Array hinzufügen
- [ ] In `CURRENCY_MAP` Währung zuordnen
- [ ] In `LOCALE_MAP` Locale definieren
- [ ] Keys übersetzen
- [ ] `npm run i18n:check` ausführen
- [ ] Browser-Test durchführen

---

**Ende des Quick Reference Guides**
