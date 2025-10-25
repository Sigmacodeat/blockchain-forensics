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
      'en-GB','en-US','en-AU','en-CA','en-NZ','en-IE','en-ZA','en-SG','en-HK','en-IN','en-PH','en-NG','en-KE','en-GH','en-PK',
      'es-ES','es-MX','es-AR','es-CL','es-CO','es-PE','es-VE','es-UY','es-BO','es-EC','es-CR','es-PA','es-PY','es-DO','es-GT','es-HN','es-NI','es-SV','es-PR','es-419',
      'pt-PT','pt-BR','pt-AO','pt-MZ','pt-CV','pt-GW','pt-ST',
      'fr-FR','fr-CA','fr-BE','fr-CH','fr-LU','fr-DZ','fr-MA','fr-TN','fr-SN','fr-CM','fr-CI',
      'de-DE','de-AT','de-CH','de-LU','de-LI','it-CH','it-IT','nl-NL','nl-BE',
      'sv-SE','sv-FI','fi-FI','da-DK','nb-NO','nn-NO','is-IS',
      'pl-PL','cs-CZ','sk-SK','sl-SI','hu-HU','ro-RO','ro-MD','bg-BG','et-EE','lv-LV','lt-LT',
      'sr-RS','sr-BA','bs-BA','mk-MK','sq-AL','sq-MK','sq-XK',
      'el-GR','el-CY',
      'ru-RU','ru-BY','ru-KZ','ru-KG','uk-UA','be-BY',
      'ar-SA','ar-AE','ar-EG','ar-MA','ar-DZ','ar-TN','ar-LB','ar-IQ','ar-JO','ar-OM','ar-QA','ar-KW','ar-BH','ar-PS','ar-LY','ar-SY','ar-YE','ar-SD','he-IL','fa-IR','fa-AF',
      'hi-IN','bn-BD','bn-IN','id-ID','ms-MY','ms-SG','ms-BN','th-TH','ur-PK','ur-IN','vi-VN','ja-JP','ko-KR',
      'zh-CN','zh-TW','zh-HK','zh-MO'
    ]
    const resources = (i18n.options as any)?.resources || {}
    // Base languages: take loaded resources directly so all active bases (bn, fa, id, ms, th, ur, vi, zh-TW, ...) are included
    const baseLangs: string[] = Object.keys(resources)
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
