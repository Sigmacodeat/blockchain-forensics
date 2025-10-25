# Internationalisierungs-Audit Report
**Datum:** 2025-01-16
**Status:** 🔴 Kritische Probleme gefunden

---

## 1. PROBLEM-ZUSAMMENFASSUNG

### 🔴 Kritisch
1. **34 Sprachen nicht importiert** - Nur 17 von 42 Sprachen werden in `i18n/config.ts` geladen
2. **Keine Währungszuordnung** - Alle Länder zeigen nur USD (PricingPage.tsx, Zeile 52)
3. **LANGUAGES Array unvollständig** - Nur 8 von 42 Sprachen in I18nContext.tsx
4. **Fehlende hreflang Tags** - Kein SEO für lokale Märkte

### 🟡 Wichtig
1. **Unvollständige Übersetzungen** - Keys wie "agent.*", "investigator.*", "corr.*" in vielen Dateien
2. **Inkonsistente Fallback-Logik** - EN als Fallback für 34 Sprachen

---

## 2. VERFÜGBARE SPRACHDATEIEN (42)

| # | Code | Sprache | Datei vorhanden | Import in config.ts | In LANGUAGES Array | Größe |
|---|------|---------|-----------------|---------------------|-------------------|-------|
| 1 | ar | Arabisch | ✅ | ✅ | ❌ | 61.5 KB |
| 2 | be | Weißrussisch | ✅ | ❌ (→EN) | ❌ | 68.3 KB |
| 3 | bg | Bulgarisch | ✅ | ❌ (→EN) | ❌ | 68.7 KB |
| 4 | bs | Bosnisch | ✅ | ✅ | ❌ | 49.1 KB |
| 5 | cs | Tschechisch | ✅ | ❌ (→EN) | ❌ | 47.8 KB |
| 6 | da | Dänisch | ✅ | ❌ (→EN) | ❌ | 48.5 KB |
| 7 | de | Deutsch | ✅ | ✅ | ✅ | 52.2 KB |
| 8 | el | Griechisch | ✅ | ❌ (→EN) | ❌ | 61.1 KB |
| 9 | en | Englisch | ✅ | ✅ | ✅ | 50.9 KB |
| 10 | es | Spanisch | ✅ | ✅ | ✅ | 53.9 KB |
| 11 | et | Estnisch | ✅ | ❌ (→EN) | ❌ | 48.8 KB |
| 12 | fi | Finnisch | ✅ | ❌ (→EN) | ❌ | 49.9 KB |
| 13 | fr | Französisch | ✅ | ✅ | ✅ | 54.6 KB |
| 14 | ga | Irisch | ✅ | ❌ (→EN) | ❌ | 48.6 KB |
| 15 | hi | Hindi | ✅ | ✅ | ❌ | 74.2 KB |
| 16 | hu | Ungarisch | ✅ | ❌ (→EN) | ❌ | 57.7 KB |
| 17 | is | Isländisch | ✅ | ❌ (→EN) | ❌ | 51.8 KB |
| 18 | it | Italienisch | ✅ | ✅ | ❌ | 52.9 KB |
| 19 | ja | Japanisch | ✅ | ✅ | ✅ | 55.0 KB |
| 20 | ko | Koreanisch | ✅ | ✅ | ✅ | 48.6 KB |
| 21 | lb | Luxemburgisch | ✅ | ❌ (→EN) | ❌ | 49.7 KB |
| 22 | lt | Litauisch | ✅ | ❌ (→EN) | ❌ | 51.8 KB |
| 23 | lv | Lettisch | ✅ | ❌ (→EN) | ❌ | 51.8 KB |
| 24 | mk | Mazedonisch | ✅ | ❌ (→EN) | ❌ | 67.7 KB |
| 25 | mt | Maltesisch | ✅ | ❌ (→EN) | ❌ | 52.0 KB |
| 26 | nb | Norwegisch Bokmål | ✅ | ❌ (→EN) | ❌ | 51.8 KB |
| 27 | nl | Niederländisch | ✅ | ✅ | ❌ | 52.8 KB |
| 28 | nn | Norwegisch Nynorsk | ✅ | ❌ (→EN) | ❌ | 47.7 KB |
| 29 | pl | Polnisch | ✅ | ✅ | ❌ | 52.3 KB |
| 30 | pt | Portugiesisch | ✅ | ✅ | ❌ | 53.9 KB |
| 31 | rm | Rätoromanisch | ✅ | ❌ (→EN) | ❌ | 51.6 KB |
| 32 | ro | Rumänisch | ✅ | ✅ | ❌ | 54.2 KB |
| 33 | ru | Russisch | ✅ | ✅ | ✅ | 67.1 KB |
| 34 | sk | Slowakisch | ✅ | ❌ (→EN) | ❌ | 50.4 KB |
| 35 | sl | Slowenisch | ✅ | ❌ (→EN) | ❌ | 48.2 KB |
| 36 | sq | Albanisch | ✅ | ❌ (→EN) | ❌ | 55.1 KB |
| 37 | sr | Serbisch | ✅ | ❌ (→EN) | ❌ | 49.5 KB |
| 38 | sv | Schwedisch | ✅ | ❌ (→EN) | ❌ | 49.7 KB |
| 39 | tr | Türkisch | ✅ | ✅ | ❌ | 49.4 KB |
| 40 | uk | Ukrainisch | ✅ | ❌ (→EN) | ❌ | 67.4 KB |
| 41 | zh-CN | Chinesisch (VR) | ✅ | ✅ | ✅ (als 'zh') | 44.5 KB |
| 42 | zh | - | ❌ | ❌ | ✅ | - |

**Zusammenfassung:**
- ✅ Importiert: 17/42 (40%)
- ❌ Nur EN-Fallback: 25/42 (60%)
- In LANGUAGES: 8/42 (19%)

---

## 3. WÄHRUNGSZUORDNUNG (FEHLT KOMPLETT)

### Aktueller Status
```typescript
// PricingPage.tsx, Zeile 52
const currency = 'USD' // ❌ Hardcoded für alle Länder!
```

### Benötigte Währungszuordnung

| Land/Region | Code | Währung | ISO |
|-------------|------|---------|-----|
| **Europa (EUR)** |
| Deutschland | de | Euro | EUR |
| Frankreich | fr | Euro | EUR |
| Spanien | es | Euro | EUR |
| Italien | it | Euro | EUR |
| Niederlande | nl | Euro | EUR |
| Portugal | pt | Euro | EUR |
| Griechenland | el | Euro | EUR |
| Österreich | de-AT | Euro | EUR |
| Belgien | nl-BE, fr-BE | Euro | EUR |
| Irland | ga, en-IE | Euro | EUR |
| Luxemburg | lb | Euro | EUR |
| Malta | mt | Euro | EUR |
| Zypern | el-CY | Euro | EUR |
| Estland | et | Euro | EUR |
| Lettland | lv | Euro | EUR |
| Litauen | lt | Euro | EUR |
| Slowakei | sk | Euro | EUR |
| Slowenien | sl | Euro | EUR |
| Finnland | fi | Euro | EUR |
| **Europa (Nicht-EUR)** |
| UK | en-GB | Pfund Sterling | GBP |
| Schweiz | de-CH, fr-CH, it-CH, rm | Schweizer Franken | CHF |
| Norwegen | nb, nn | Norwegische Krone | NOK |
| Schweden | sv | Schwedische Krone | SEK |
| Dänemark | da | Dänische Krone | DKK |
| Island | is | Isländische Krone | ISK |
| Polen | pl | Złoty | PLN |
| Tschechien | cs | Tschechische Krone | CZK |
| Ungarn | hu | Forint | HUF |
| Rumänien | ro | Leu | RON |
| Bulgarien | bg | Lew | BGN |
| Kroatien | hr | Kuna | HRK |
| Serbien | sr | Dinar | RSD |
| Nord-Mazedonien | mk | Denar | MKD |
| Albanien | sq | Lek | ALL |
| Bosnien | bs | Mark | BAM |
| Ukraine | uk | Hrywnja | UAH |
| Weißrussland | be | Rubel | BYN |
| Türkei | tr | Lira | TRY |
| **Asien** |
| China | zh-CN | Yuan | CNY |
| Japan | ja | Yen | JPY |
| Südkorea | ko | Won | KRW |
| Indien | hi | Rupie | INR |
| **Arabisch** |
| VAE/Saudi etc. | ar | US-Dollar/Dirham | USD/AED |
| **USA** |
| USA | en | US-Dollar | USD |

---

## 4. ÜBERSETZUNGS-QUALITÄT

### Vollständig übersetzte Sprachen
✅ **de, en, es, fr, sv** - Alle Keys professionell übersetzt

### Teilweise übersetzt (mit EN-Placeholders)
🟡 **it, pt, nl, pl, tr, ru, ja, ko, ar, hi, bs, ro**
- Sections wie `agent.*`, `investigator.*`, `corr.*` haben Keys statt Texte
- Beispiel in de.json:
  ```json
  "agent": {
    "cancel": "agent.cancel",  // ❌ Key statt Text
    "error": "agent.error"      // ❌ Key statt Text
  }
  ```

### Zu überprüfende Dateien (unvollständig)
- ar.json - Arabisch (RTL!)
- bg.json - Bulgarisch
- cs.json - Tschechisch
- da.json - Dänisch
- el.json - Griechisch
- et.json - Estnisch
- fi.json - Finnisch
- hu.json - Ungarisch
- is.json - Isländisch
- lt.json, lv.json - Baltisch
- mk.json - Mazedonisch
- nb.json, nn.json - Norwegisch
- sk.json, sl.json - Slowakisch/Slowenisch
- sq.json - Albanisch
- sr.json - Serbisch
- uk.json - Ukrainisch
- be.json - Weißrussisch

---

## 5. FEHLENDE KEYS (Beispiel aus en.json vs. de.json)

### Unübersetzte Sections in ALLEN Dateien:
```
agent.cancel
agent.error
agent.error_unknown
agent.examples.*
agent.instructions
agent.loading
agent.placeholder
agent.retry
agent.send
agent.subtitle
agent.title
agent.welcome

investigator.actions.*
investigator.connected.*
investigator.graph.*
investigator.path.*
investigator.search.*
investigator.settings.*
investigator.timeline.*

corr.controls.*
corr.overview.*
corr.rules.*
corr.sev.*
corr.suppressions.*
corr.test.*

coverage.* (alle Subsections)

address_analysis.* (alle)
```

---

## 6. SEO & LOKALISIERUNG

### ❌ Fehlt komplett:
1. **hreflang Tags** für alle Sprachen
2. **Lokale URLs** (z.B. `/de/pricing`, `/fr/pricing`)
3. **Sitemap mit Sprachvarianten**
4. **Geo-Targeting Meta-Tags**

### Benötigte SeoI18n Erweiterung:
```tsx
<link rel="alternate" hreflang="de" href="https://sigmacode.io/de" />
<link rel="alternate" hreflang="fr" href="https://sigmacode.io/fr" />
// ... für alle 42 Sprachen
```

---

## 7. NÄCHSTE SCHRITTE (PRIORISIERT)

### Phase 1: Kritisch (JETZT) ✅
1. ✅ Alle 42 Sprachen in `i18n/config.ts` importieren
2. ✅ LANGUAGES Array auf 42 erweitern mit korrekten Flags
3. ✅ Währungszuordnung implementieren
4. ✅ PricingPage.tsx für Multi-Currency anpassen

### Phase 2: Übersetzungen (HEUTE)
5. ⏳ Fehlende Keys in allen 42 Dateien übersetzen
   - Script zum Finden aller Keys mit Wert = Key-Name
   - Batch-Translation via DeepL API

### Phase 3: SEO (MORGEN)
6. ⏳ hreflang Tags in SeoI18n.tsx
7. ⏳ Lokale Routing-Struktur
8. ⏳ Sitemap mit allen Sprachen

### Phase 4: Testing (ÜBERMORGEN)
9. ⏳ Automatische Tests für fehlende Keys
10. ⏳ Visual Regression Tests für alle Sprachen
11. ⏳ RTL-Support für Arabisch testen

---

## 8. CODE-ÄNDERUNGEN

### Datei 1: `i18n/config.ts`
**Problem:** 25 Sprachen nicht importiert
**Fix:** Alle 42 Sprachen importieren

### Datei 2: `contexts/I18nContext.tsx`
**Problem:** LANGUAGES Array hat nur 8 Einträge
**Fix:** Auf 42 erweitern

### Datei 3: `pages/PricingPage.tsx`
**Problem:** Hardcoded USD
**Fix:** Currency-Mapping basierend auf Sprache

### Datei 4: `components/SeoI18n.tsx`
**Problem:** Keine hreflang Tags
**Fix:** Dynamische Tags für alle Sprachen

---

## 9. GESCHÄTZTE AUFWAND

| Task | Aufwand | Priorität |
|------|---------|-----------|
| Import aller Sprachen | 30 Min | P0 |
| LANGUAGES Array erweitern | 1h | P0 |
| Währungszuordnung | 2h | P0 |
| Fehlende Keys finden | 1h | P1 |
| Keys übersetzen (42 Sprachen) | 8-12h | P1 |
| hreflang Tags | 2h | P2 |
| Lokales Routing | 4h | P2 |
| Testing | 4h | P3 |
| **GESAMT** | **22-28h** | - |

---

## 10. QUALITÄTSKRITERIEN FÜR "100% READY"

✅ **MUSS:**
- [ ] Alle 42 Sprachen importiert und funktional
- [ ] Alle Keys in allen Sprachen übersetzt (keine "key.name" Werte)
- [ ] Währung korrekt pro Land/Region
- [ ] LANGUAGES Array vollständig mit korrekten Flags
- [ ] RTL-Support für ar (Arabisch)

🟡 **SOLLTE:**
- [ ] hreflang Tags für alle Sprachen
- [ ] Lokale URLs (`/de/*`, `/fr/*`)
- [ ] Automated Tests für fehlende Keys

🟢 **KANN:**
- [ ] Geo-IP basierte Sprachwahl
- [ ] A/B Testing verschiedener Übersetzungen
- [ ] Analytics pro Sprache

---

**Ende des Audit Reports**
