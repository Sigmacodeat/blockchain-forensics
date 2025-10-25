import { useEffect } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { LANGUAGES } from '@/contexts/I18nContext'

// Simple SEO helper to inject canonical and x-default hreflang
// Note: Language-prefixed routes are not used yet; we add x-default and canonical only.
export default function SeoI18n() {
  const location = useLocation()
  const params = useParams()
  const { i18n } = useTranslation()

  useEffect(() => {
    const siteUrl = (import.meta as any).env?.VITE_SITE_URL || ''
    const path = location.pathname
    const canonicalUrl = siteUrl ? `${siteUrl}${path}` : window.location.origin + path

    // create/update canonical link
    let canonical = document.querySelector('link[rel="canonical"]') as HTMLLinkElement | null
    let createdCanonical = false
    if (!canonical) {
      canonical = document.createElement('link')
      canonical.rel = 'canonical'
      createdCanonical = true
    }
    if (canonical) {
      canonical.href = canonicalUrl
      if (createdCanonical) document.head.appendChild(canonical)
    }

    // Remove previous hreflang alternates (we'll recreate)
    document.querySelectorAll('link[rel="alternate"][hreflang]').forEach(el => el.parentElement?.removeChild(el))

    // x-default hreflang (points to canonical)
    const xDefault = document.createElement('link')
    xDefault.rel = 'alternate'
    xDefault.hreflang = 'x-default'
    xDefault.href = canonicalUrl
    document.head.appendChild(xDefault)

    // Full hreflang set using language-prefixed routes across all supported locales
    const REGIONALS = [
      // Englisch
      'en-GB','en-US','en-AU','en-CA','en-NZ','en-ZA','en-SG','en-IE','en-IN','en-PH','en-HK',
      // Spanisch
      'es-ES','es-MX','es-AR','es-CL','es-CO','es-PE','es-VE','es-UY','es-419',
      // Portugiesisch
      'pt-PT','pt-BR','pt-AO','pt-MZ',
      // Französisch
      'fr-FR','fr-CA','fr-BE','fr-CH','fr-LU','fr-DZ','fr-MA','fr-TN',
      // Deutsch
      'de-DE','de-AT','de-CH',
      // Italienisch
      'it-IT','it-CH',
      // Niederländisch
      'nl-NL','nl-BE',
      // Weitere Europäische
      'pl-PL','cs-CZ','sk-SK','hu-HU','ro-RO','bg-BG','el-GR','sl-SI','sr-RS','bs-BA',
      'mk-MK','sq-AL','lt-LT','lv-LV','et-EE','fi-FI','sv-SE','da-DK','nb-NO','nn-NO',
      'is-IS','ga-IE','mt-MT','lb-LU','rm-CH','uk-UA','be-BY','ru-RU','tr-TR',
      // Asiatisch
      'ar-SA','hi-IN','ja-JP','ko-KR','zh-CN','zh-HK','zh-TW',
      // Hebräisch
      'he-IL'
    ]
    const resources = (i18n.options as any)?.resources || {}
    const available: Set<string> = new Set(Object.keys(resources))
    const baseLangs: string[] = LANGUAGES
      .map(l => l.code)
      // prefer locales that have loaded resources; fall back to full list
      .filter(code => available.size === 0 || available.has(code))
    const supportedLangs: string[] = Array.from(new Set([...baseLangs, ...REGIONALS]))
    const currentLang = params.lang || i18n.language || 'en'
    const pathname = location.pathname
    const withoutLangPrefix = pathname.replace(/^\/[a-zA-Z]{2}(?:-[A-Z]{2})?\b/, '') || '/'

    supportedLangs.forEach((lng) => {
      const href = siteUrl
        ? `${siteUrl}/${lng}${withoutLangPrefix}`
        : `${window.location.origin}/${lng}${withoutLangPrefix}`
      const link = document.createElement('link')
      link.rel = 'alternate'
      link.hreflang = lng
      link.href = href
      document.head.appendChild(link)
    })

    // set html lang in case provider didn't yet
    const lang = i18n.language || 'en'
    const html = document.documentElement
    if (html.getAttribute('lang') !== lang) {
      html.setAttribute('lang', lang)
    }

    return () => {
      // Keep canonical and x-default persistent between route changes; no cleanup
    }
  }, [location.pathname, i18n.language, params.lang])

  return null
}
