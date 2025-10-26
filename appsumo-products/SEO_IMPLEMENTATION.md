# SEO Technical Implementation

## 1. hreflang Implementation

Add to each product page head:

```html
<!-- hreflang tags for all supported languages -->
<link rel="alternate" hreflang="en" href="https://domain.com/products/wallet-guardian" />
<link rel="alternate" hreflang="de" href="https://domain.com/products/wallet-guardian/de" />
<link rel="alternate" hreflang="es" href="https://domain.com/products/wallet-guardian/es" />
<link rel="alternate" hreflang="fr" href="https://domain.com/products/wallet-guardian/fr" />
<link rel="alternate" hreflang="it" href="https://domain.com/products/wallet-guardian/it" />
<link rel="alternate" hreflang="pt" href="https://domain.com/products/wallet-guardian/pt" />
<link rel="alternate" hreflang="x-default" href="https://domain.com/products/wallet-guardian" />
```

## 2. Structured Data (JSON-LD)

Add to each product page:

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Wallet Guardian",
  "description": "Real-Time Crypto Security with 15 ML Models",
  "brand": {
    "@type": "Brand",
    "name": "Blockchain Forensics"
  },
  "offers": [
    {
      "@type": "Offer",
      "price": "59",
      "priceCurrency": "USD",
      "availability": "https://schema.org/InStock",
      "priceValidUntil": "2026-12-31"
    },
    {
      "@type": "Offer",
      "price": "119",
      "priceCurrency": "USD",
      "availability": "https://schema.org/InStock",
      "priceValidUntil": "2026-12-31"
    },
    {
      "@type": "Offer",
      "price": "199",
      "priceCurrency": "USD",
      "availability": "https://schema.org/InStock",
      "priceValidUntil": "2026-12-31"
    }
  ],
  "applicationCategory": "SecurityApplication",
  "operatingSystem": "Web Browser",
  "softwareVersion": "2.0.0",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "127"
  }
}
```

## 3. Core Web Vitals Optimization

### Lighthouse Scores Target:
- Performance: >90
- Accessibility: >95
- Best Practices: >95
- SEO: >95

### Optimizations:
- **LCP (<2.5s)**: Optimize hero images, preload critical resources
- **FID (<100ms)**: Minimize JavaScript execution, use web workers for heavy computations
- **CLS (<0.1)**: Reserve space for dynamic content, avoid layout shifts

### Implementation:
```html
<!-- Preload critical resources -->
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/images/hero-bg.webp" as="image">

<!-- Optimize images -->
<img src="/images/hero.webp" alt="..." loading="eager" width="1200" height="600">

<!-- Minimize JS -->
<script defer src="/js/main.js"></script>
```

## 4. Canonical URLs

Add to each localized page:

```html
<!-- Canonical for default language -->
<link rel="canonical" href="https://domain.com/products/wallet-guardian" />

<!-- Canonical for localized pages -->
<link rel="canonical" href="https://domain.com/products/wallet-guardian/de" />
```

## 5. Language-Specific Sitemaps

### sitemap-en.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://domain.com/products/wallet-guardian</loc>
    <lastmod>2025-10-26</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>
```

### sitemap-de.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://domain.com/products/wallet-guardian/de</loc>
    <lastmod>2025-10-26</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>
```

## 6. Robots.txt Configuration

```
User-agent: *
Allow: /

# Block admin areas
Disallow: /admin/
Disallow: /api/admin/

# Allow crawling of all product pages
Allow: /products/

# Sitemap references
Sitemap: https://domain.com/sitemap.xml
Sitemap: https://domain.com/sitemap-en.xml
Sitemap: https://domain.com/sitemap-de.xml
Sitemap: https://domain.com/sitemap-es.xml
```

## 7. Open Graph & Twitter Cards

Add to each product page:

```html
<!-- Open Graph -->
<meta property="og:title" content="Wallet Guardian - Real-Time Crypto Security" />
<meta property="og:description" content="Protect your crypto with 15 ML models across 35+ chains" />
<meta property="og:image" content="https://domain.com/images/wallet-guardian-og.jpg" />
<meta property="og:url" content="https://domain.com/products/wallet-guardian" />
<meta property="og:type" content="product" />

<!-- Twitter Cards -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Wallet Guardian - Real-Time Crypto Security" />
<meta name="twitter:description" content="Protect your crypto with 15 ML models across 35+ chains" />
<meta name="twitter:image" content="https://domain.com/images/wallet-guardian-twitter.jpg" />
```

## 8. Technical Implementation Checklist

- [ ] hreflang tags on all product pages
- [ ] Structured data JSON-LD implemented
- [ ] Core Web Vitals optimized (<2.5s LCP, <100ms FID, <0.1 CLS)
- [ ] Canonical URLs set correctly
- [ ] Language-specific sitemaps generated
- [ ] Robots.txt configured
- [ ] Open Graph and Twitter meta tags added
- [ ] Page speed optimized (gzip, CDN, caching headers)
- [ ] Mobile-first responsive design verified
- [ ] Accessibility (WCAG 2.1 AA) compliance checked
