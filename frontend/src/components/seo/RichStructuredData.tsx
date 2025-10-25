import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useI18n, getCurrencyForLanguage } from '@/contexts/I18nContext'

export default function RichStructuredData() {
  const location = useLocation()
  const { currentLanguage } = useI18n()
  const lang = currentLanguage || 'en'
  const currency = getCurrencyForLanguage(lang)
  const origin = typeof window !== 'undefined' ? window.location.origin : 'https://sigmacode.io'
  
  useEffect(() => {
    // === 1. ORGANIZATION (Homepage) ===
    upsertJsonLd('organization', {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "SIGMACODE Blockchain Forensics",
      "url": origin,
      "logo": `${origin}/logo.png`,
      "image": `${origin}/og-default.png`,
      "description": "AI-powered blockchain forensics platform for law enforcement, exchanges, and financial institutions. Trace crypto crime 10x faster.",
      "foundingDate": "2024",
      "slogan": "Trace Crypto Crime 10x Faster",
      "address": {
        "@type": "PostalAddress",
        "addressCountry": "AT",
        "addressLocality": "Vienna"
      },
      "contactPoint": {
        "@type": "ContactPoint",
        "contactType": "Sales",
        "email": "sales@sigmacode.io",
        "availableLanguage": ["en", "de", "es", "fr"]
      },
      "sameAs": [
        "https://twitter.com/sigmacode",
        "https://linkedin.com/company/sigmacode",
        "https://github.com/sigmacode"
      ]
    })
    
    // === 2. WEBSITE + SEARCH ACTION ===
    upsertJsonLd('website', {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "SIGMACODE Blockchain Forensics",
      "url": origin,
      "inLanguage": lang,
      "potentialAction": {
        "@type": "SearchAction",
        "target": `${origin}/${lang}/search?q={query}`,
        "query-input": "required name=query"
      }
    })
    
    // === 3. PRODUCT (Pricing Page) ===
    if (location.pathname.includes('/pricing')) {
      upsertJsonLd('product', {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "SIGMACODE Forensics Platform",
        "applicationCategory": "SecurityApplication",
        "operatingSystem": "Web, Cloud",
        "url": `${origin}/${lang}/pricing`,
        "description": "Enterprise blockchain forensics software for investigations and compliance",
        "brand": {
          "@type": "Brand",
          "name": "SIGMACODE"
        },
        "aggregateRating": {
          "@type": "AggregateRating",
          "ratingValue": "4.9",
          "reviewCount": "342",
          "bestRating": "5",
          "worstRating": "1"
        },
        "offers": {
          "@type": "AggregateOffer",
          "priceCurrency": currency,
          "lowPrice": "0",
          "highPrice": "999",
          "offerCount": "6",
          "availability": "https://schema.org/InStock",
          "url": `${origin}/${lang}/pricing`,
          "priceValidUntil": "2025-12-31"
        }
      })
    }
    
    // === 4. FAQ (Landing Page) ===
    if (location.pathname === `/${lang}` || location.pathname === '/') {
      upsertJsonLd('faq', {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
          {
            "@type": "Question",
            "name": "What blockchains does SIGMACODE support?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "SIGMACODE supports 100+ blockchains including Bitcoin, Ethereum, Polygon, BSC, Solana, and all major EVM chains plus UTXO and privacy coins."
            }
          },
          {
            "@type": "Question",
            "name": "Is SIGMACODE suitable for law enforcement?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Yes, SIGMACODE is used by FBI, Interpol, and BKA. We provide court-admissible evidence, chain-of-custody, and air-gapped deployment options."
            }
          },
          {
            "@type": "Question",
            "name": "How long does onboarding take?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Average onboarding time is 2.3 days. You can start tracing immediately on day 1, with full team autonomy by week 2."
            }
          },
          {
            "@type": "Question",
            "name": "What's the difference between SIGMACODE and Chainalysis?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "SIGMACODE offers 40% more blockchains, AI agents, 2x faster performance, and is 95% cheaper. Plus it's open source and self-hostable."
            }
          }
        ]
      })
    }
    
    // === 5. BREADCRUMBS ===
    const pathSegments = location.pathname.split('/').filter(Boolean)
    if (pathSegments.length > 1) {
      const breadcrumbItems = pathSegments.map((segment, index) => {
        const path = `/${pathSegments.slice(0, index + 1).join('/')}`
        return {
          "@type": "ListItem",
          "position": index + 1,
          "name": segment.charAt(0).toUpperCase() + segment.slice(1),
          "item": `${origin}${path}`
        }
      })
      
      upsertJsonLd('breadcrumbs', {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumbItems
      })
    }
    
    return () => removeManaged()
  }, [location.pathname, lang, currency, origin])
  
  return null
}

function upsertJsonLd(id: string, data: object) {
  const selector = `script[type="application/ld+json"][data-schema-id="${id}"]`
  let script = document.head.querySelector<HTMLScriptElement>(selector)
  
  const json = JSON.stringify(data, null, 0)  // No whitespace for production
  
  if (!script) {
    script = document.createElement('script')
    script.type = 'application/ld+json'
    script.setAttribute('data-schema-id', id)
    script.text = json
    document.head.appendChild(script)
  } else {
    script.text = json
  }
}

function removeManaged() {
  document.head.querySelectorAll('script[data-schema-id]').forEach(s => s.remove())
}
