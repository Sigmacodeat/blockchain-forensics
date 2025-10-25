import React from 'react'
import { useLocation } from 'react-router-dom'
import { useI18n, getCurrencyForLanguage, LOCALE_MAP } from '@/contexts/I18nContext'

function upsertJsonLd(id: string, data: object) {
  const selector = `script[type="application/ld+json"][data-managed="jsonld-${id}"]`
  let el = document.head.querySelector<HTMLScriptElement>(selector)
  const json = JSON.stringify(data)
  if (!el) {
    el = document.createElement('script')
    el.setAttribute('type', 'application/ld+json')
    el.setAttribute('data-managed', `jsonld-${id}`)
    el.text = json
    document.head.appendChild(el)
  } else {
    el.text = json
  }
}

function removeManaged() {
  document.head.querySelectorAll('script[data-managed^="jsonld-"]').forEach(n => n.parentElement?.removeChild(n))
}

export default function StructuredData() {
  const { currentLanguage } = useI18n()
  const location = useLocation()

  React.useEffect(() => {
    const origin = window.location.origin
    const url = `${origin}${location.pathname}${location.search}${location.hash}`
    const lang = currentLanguage || 'en'
    const inLanguage = LOCALE_MAP[lang] || 'en-US'
    const currency = getCurrencyForLanguage(lang)

    // Organization
    upsertJsonLd('org', {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: 'SIGMACODE Blockchain Forensics',
      url: origin,
      logo: `${origin}/favicon.svg`,
      sameAs: [
        'https://www.linkedin.com/company/sigmacode',
        'https://twitter.com/sigmacode'
      ]
    })

    // WebSite + potentialSearchAction (generic)
    upsertJsonLd('website', {
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      name: 'SIGMACODE Blockchain Forensics',
      url: origin,
      inLanguage,
      potentialAction: {
        '@type': 'SearchAction',
        target: `${origin}/${lang}/search?q={query}`,
        'query-input': 'required name=query'
      }
    })

    // Product (Pricing) minimal Offer for SEO; currency varies by locale
    upsertJsonLd('product', {
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: 'SIGMACODE Forensics Platform',
      url: `${origin}/${lang}/pricing`,
      brand: {
        '@type': 'Brand',
        name: 'SIGMACODE'
      },
      offers: {
        '@type': 'AggregateOffer',
        priceCurrency: currency,
        lowPrice: '0',
        highPrice: '999',
        offerCount: '5',
        availability: 'https://schema.org/InStock',
        url: `${origin}/${lang}/pricing`
      }
    })

    return () => removeManaged()
  }, [currentLanguage, location.pathname, location.search, location.hash])

  return null
}
