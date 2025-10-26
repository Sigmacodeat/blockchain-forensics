# Blockchain Forensics Blog System

Ein vollständiges, mehrsprachiges Blog-System mit SEO-Optimierung und Multi-Tenant-Unterstützung für AppSumo-Produkte.

## 🚀 Überblick

Das Blog-System bietet:
- **48 Sprachen** mit automatischer Übersetzung
- **SEO-optimiert** mit strukturierten Daten, Sitemaps und RSS
- **Multi-Tenant** für AppSumo-Produkte
- **SPA-Integration** mit React Router
- **Static Export** für optimale Performance

## 📁 Verzeichnis-Struktur

```
blockchain-forensics/
├── content/blog/              # Blog-Artikel-Quellen
│   └── en/                    # Englische Originale
│       └── <slug>.json        # Artikel-Dateien
├── frontend/public/blog/      # Generierte Übersetzungen & Indizes
│   ├── index-<lang>.json      # Index-Dateien
│   ├── rss-<lang>.xml         # RSS-Feeds
│   ├── atom-<lang>.xml        # Atom-Feeds
│   └── <lang>/                # Übersetzte Artikel
├── scripts/                   # Build-Skripte
│   ├── blog-translate.mjs     # Übersetzungs-Pipeline
│   ├── blog-build-index.mjs   # Index-Generierung
│   ├── blog-rss.mjs          # RSS/Atom-Generator
│   └── generate-sitemaps.mjs  # SEO-Sitemaps
└── frontend/src/pages/        # React-Komponenten
    ├── BlogListPage.tsx       # Blog-Übersichtsseite
    └── BlogPostPage.tsx       # Einzelartikel-Seite
```

## 📝 Artikel Erstellen

### Grundstruktur eines Artikels

Erstelle eine neue Datei in `content/blog/en/<slug>.json`:

```json
{
  "slug": "blockchain-forensics-explained",
  "title": "Blockchain Forensics Explained: Tracing Digital Assets",
  "description": "A comprehensive guide to blockchain forensics techniques and tools.",
  "content": "# Introduction\n\nBlockchain forensics is...",
  "datePublished": "2025-01-15T10:00:00Z",
  "dateModified": "2025-01-15T10:00:00Z",
  "author": "SIGMACODE Editorial",
  "category": "blockchain",
  "tags": ["forensics", "blockchain", "cryptocurrency"],
  "featuredImage": {
    "url": "/images/blockchain-forensics.jpg",
    "alt": "Blockchain network visualization",
    "width": 1200,
    "height": 600
  },
  "tenant": "wallet-guardian"  // Optional: für AppSumo-spezifische Artikel
}
```

### Felder-Erklärung

| Feld | Typ | Erforderlich | Beschreibung |
|------|-----|-------------|--------------|
| `slug` | string | ✅ | URL-freundlicher Identifier |
| `title` | string | ✅ | Artikel-Titel |
| `description` | string | ✅ | SEO-Beschreibung (150-160 Zeichen) |
| `content` | string | ✅ | Vollständiger Artikel-Text (Markdown/HTML) |
| `datePublished` | ISO-Date | ✅ | Veröffentlichungsdatum |
| `dateModified` | ISO-Date | ❌ | Letzte Änderung (für SEO) |
| `author` | string | ❌ | Autor-Name |
| `category` | string | ❌ | Hauptkategorie |
| `tags` | string[] | ❌ | Schlagwörter für Filterung |
| `featuredImage` | object | ❌ | Titelbild mit URL, alt, width, height |
| `tenant` | string | ❌ | AppSumo-Produkt-Schlüssel für Multi-Tenant |

### Content-Format

- **Markdown-Support**: Überschriften (#), Listen, Links, Code-Blöcke (```)
- **HTML möglich**: Für komplexe Formatierung
- **Bilder**: Relative Pfade oder absolute URLs
- **Länge**: Keine Begrenzung, aber Performance beachten

## 🔄 Build-Prozess

### Lokale Entwicklung

```bash
# Einzelne Schritte
npm run --prefix frontend blog:translate  # Übersetzung
npm run --prefix frontend blog:index     # Index-Generierung
npm run --prefix frontend blog:rss       # RSS/Atom-Feeds

# Vollständiger Build
npm run --prefix frontend build:optimized
```

### CI/CD Pipeline

```yaml
# GitHub Actions Beispiel
name: Deploy Blog
on:
  push:
    paths:
      - 'content/blog/**'
      - 'scripts/blog-*.mjs'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: npm ci
        working-directory: frontend
      - name: Translate blog posts
        run: npm run blog:translate
        working-directory: frontend
        env:
          DEEPL_API_KEY: ${{ secrets.DEEPL_API_KEY }}
      - name: Build index and RSS
        run: |
          npm run blog:index
          npm run blog:rss
        working-directory: frontend
      - name: Build frontend
        run: npm run build:optimized
        working-directory: frontend
        env:
          VITE_SITE_URL: https://forensics.ai
      - name: Deploy
        run: # Dein Deployment-Befehl
```

## 🌍 Mehrsprachigkeit

### Unterstützte Sprachen

Das System unterstützt 48 Sprachen mit automatischem Fallback auf Englisch:

- **West-Europa**: en, de, fr, es, pt, it, nl
- **Nord-Europa**: da, sv, no, fi, is
- **Ost-Europa**: pl, cs, sk, hu, ro, bg, et, lv, lt, sl, hr, bs, sr, mk, sq
- **Asien**: ar, he, fa, hi, bn, ur, id, ms, th, vi, ja, ko, zh-CN, zh-TW
- **Andere**: el, ru, uk, be, tr, ga, rm, mt

### Übersetzungs-Provider

**Priorität**: DeepL → Google Translate → Fallback auf Englisch

```bash
# DeepL (empfohlen)
export DEEPL_API_KEY=your_deepl_key

# Google Translate (Fallback)
export GOOGLE_API_KEY=your_google_key
```

### Slug-Stabilität

Slugs bleiben sprachübergreifend identisch für bessere SEO:
- `/en/blog/blockchain-forensics-explained`
- `/de/blog/blockchain-forensics-explained`
- `/fr/blog/blockchain-forensics-explained`

## 🔍 SEO-Optimierung

### Meta-Tags

Automatisch generiert pro Artikel:
- `<title>`: "{Titel} - SIGMACODE Forensics"
- `<meta name="description">`
- Open Graph Tags (og:title, og:description, og:image, og:url, og:type)
- Twitter Cards (twitter:card, twitter:title, twitter:description, twitter:image)
- Article Schema (published_time, modified_time, author, tags)

### Hreflang-Alternates

Automatisch für alle Sprachvarianten:
```html
<link rel="alternate" hreflang="en" href="https://forensics.ai/en/blog/article">
<link rel="alternate" hreflang="de" href="https://forensics.ai/de/blog/article">
<link rel="alternate" hreflang="x-default" href="https://forensics.ai/en/blog/article">
```

### Sitemaps

- **Haupt-Sitemap**: `https://forensics.ai/sitemap.xml`
- **Sprach-Sitemaps**: `sitemap-en.xml`, `sitemap-de.xml`, etc.
- **Priorität**: Blog-Artikel = 0.8, Tenant-Artikel = 0.7
- **Frequenz**: weekly

### RSS/Atom-Feeds

- **RSS**: `https://forensics.ai/blog/rss-en.xml`
- **Atom**: `https://forensics.ai/blog/atom-en.xml`
- **Inhalt**: Titel, Beschreibung, Volltext, Metadaten
- **Limit**: 20 neueste Artikel pro Feed

### Strukturierte Daten

BlogPosting JSON-LD automatisch generiert:
```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Artikel-Titel",
  "description": "Beschreibung",
  "image": "https://forensics.ai/images/article.jpg",
  "datePublished": "2025-01-15T10:00:00Z",
  "dateModified": "2025-01-15T10:00:00Z",
  "author": {
    "@type": "Person",
    "name": "SIGMACODE Editorial"
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://forensics.ai/en/blog/article"
  },
  "url": "https://forensics.ai/en/blog/article"
}
```

## 🏢 Multi-Tenant (AppSumo)

### Tenant-spezifische Artikel

Füge `tenant` zu Artikel-JSON hinzu:
```json
{
  "tenant": "wallet-guardian",
  "title": "Enhanced Wallet Security with SIGMACODE"
}
```

### URLs

- **Global**: `/en/blog/article`
- **Tenant**: `/en/projects/wallet-guardian/blog/article`

### Sitemap-Generierung

Tenant-Artikel werden automatisch in Sitemaps aufgenommen mit separaten URLs.

### AppSumo-Integration

1. **Tenant definieren**: z.B. `wallet-guardian`, `complete-security`
2. **Artikel markieren**: `"tenant": "wallet-guardian"`
3. **Build**: Automatisch in Tenant-Sitemaps aufgenommen
4. **Deployment**: Tenant-spezifische URLs verfügbar

## 🚀 Deployment

### Static Export

Das System generiert statische HTML-Dateien für alle Routen:

```bash
npm run --prefix frontend export:static
```

Erzeugt `frontend/dist/` mit:
- `en/blog/index.html` (Blog-Übersicht)
- `en/blog/article-slug/index.html` (Artikel-Detail)
- `en/projects/tenant/blog/index.html` (Tenant-Blog)
- `en/projects/tenant/blog/article-slug/index.html` (Tenant-Artikel)

### CDN-Deployment

1. **Build**: `npm run --prefix frontend build:optimized`
2. **Upload**: `frontend/dist/` zu CDN
3. **Robots.txt**: Sitemap-URL aktualisieren
4. **DNS**: Domain auf CDN verweisen

### Environment Variables

```bash
# Erforderlich
VITE_SITE_URL=https://forensics.ai

# Optional (einer der beiden)
DEEPL_API_KEY=your_deepl_key
GOOGLE_API_KEY=your_google_key
```

## 🧪 Testing

### Lokale Tests

```bash
# Frontend-Tests
npm run --prefix frontend test

# Blog-spezifische Tests
npm run --prefix frontend blog:translate
npm run --prefix frontend blog:index
npm run --prefix frontend blog:rss

# Vollständiger Build-Test
npm run --prefix frontend build:optimized
```

### SEO-Tests

1. **Sitemap validieren**: `https://forensics.ai/sitemap.xml`
2. **RSS-Feeds**: `https://forensics.ai/blog/rss-en.xml`
3. **Meta-Tags**: Browser DevTools
4. **Strukturierte Daten**: Google's Rich Results Test

### Performance-Tests

1. **Lighthouse**: Core Web Vitals prüfen
2. **Page Speed**: Mobile/Desktop Scores
3. **Static Export**: HTML-Dateien auf Existenz prüfen

## 🔧 Wartung

### Neue Sprachen Hinzufügen

1. **Locale hinzufügen**: `frontend/src/locales/<new-lang>.json`
2. **i18n-Update**: Python-Skripte für Übersetzungen
3. **Build-Test**: Neue Sprache in Sitemaps prüfen

### Übersetzungs-Updates

```bash
# Einzelnen Artikel neu übersetzen
BLOG_LANGS=de,fr node scripts/blog-translate.mjs

# Alle Sprachen
node scripts/blog-translate.mjs
```

### Content-Updates

1. **Artikel bearbeiten**: `content/blog/en/<slug>.json`
2. **Build ausführen**: `npm run --prefix frontend build:optimized`
3. **Deploy**: Neue Version live schalten

## 📊 Monitoring

### SEO-Metriken

- **Google Search Console**: Indexierung, Suchanfragen
- **Google Analytics**: Traffic, Conversions
- **Ahrefs/Semrush**: Backlinks, Rankings

### Performance-Metriken

- **Core Web Vitals**: CLS, FID, LCP
- **Lighthouse Scores**: Performance, SEO, Accessibility
- **Page Speed Insights**: Mobile/Desktop

### Content-Metriken

- **Artikel-Views**: Analytics tracking
- **Engagement**: Time on page, bounce rate
- **Social Shares**: Share-Buttons integrieren

## 🆘 Troubleshooting

### Häufige Probleme

**Übersetzung schlägt fehl**
```bash
# API-Key prüfen
echo $DEEPL_API_KEY

# Einzelne Sprache testen
BLOG_LANGS=en node scripts/blog-translate.mjs
```

**Sitemap-Fehler**
```bash
# Sitemap neu generieren
VITE_SITE_URL=https://forensics.ai node scripts/generate-sitemaps.mjs

# robots.txt prüfen
curl https://forensics.ai/robots.txt
```

**Build-Fehler**
```bash
# Dependencies neu installieren
npm ci --prefix frontend

# Cache leeren
npm run --prefix frontend clean
```

### Support

Bei Problemen:
1. **Logs prüfen**: Build-Output analysieren
2. **Dateien validieren**: JSON-Syntax prüfen
3. **Netzwerk**: API-Keys und Konnektivität testen
4. **GitHub Issues**: Detaillierte Bug-Reports erstellen

---

## 📋 Checklist für neue Artikel

- [ ] Titel und Beschreibung SEO-optimiert
- [ ] Slug URL-freundlich und einzigartig
- [ ] Featured Image vorhanden (1200x600px)
- [ ] Kategorie und Tags gesetzt
- [ ] Datum korrekt (ISO-Format)
- [ ] Content auf Rechtschreibung prüfen
- [ ] Übersetzung getestet
- [ ] Sitemap-Eintrag geprüft
- [ ] Live-URL funktioniert

## 🎯 Erfolgsmetriken

- **SEO**: Top-10 Rankings für Ziel-Keywords
- **Traffic**: 50%+ aus organischer Suche
- **Engagement**: Durchschnitt 3+ Minuten Lesezeit
- **Conversion**: 5%+ Newsletter-Anmeldungen
- **Social**: 1000+ Shares pro Monat

---

*Dieses Dokument wird regelmäßig aktualisiert. Letzte Änderung: Oktober 2025*
