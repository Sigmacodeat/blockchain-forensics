import React from 'react'
import { useLocation, useParams } from 'react-router-dom'
import i18n from '@/i18n/config-optimized'

function upsertMeta(prop: string, content: string, key: string) {
  if (!content) return
  const selector = `meta[property="${prop}"][data-managed="og-${key}"]`
  let el = document.head.querySelector<HTMLMetaElement>(selector)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute('property', prop)
    el.setAttribute('data-managed', `og-${key}`)
    el.setAttribute('content', content)
    document.head.appendChild(el)
  } else {
    el.setAttribute('content', content)
  }
}

function removeManaged(prefix: string) {
  const nodes = Array.from(document.head.querySelectorAll(`meta[data-managed^="${prefix}"]`))
  nodes.forEach((n) => n.parentElement?.removeChild(n))
}

export default function OpenGraphLocale() {
  const { lang } = useParams()
  const location = useLocation()

  React.useEffect(() => {
    const resources = (i18n.options as any)?.resources || {}
    const bases: string[] = Object.keys(resources)

    // Convert our locale format to og:locale (e.g., en-GB -> en_GB; fr -> fr_FR fallback)
    const toOg = (code: string): string => {
      if (/^[a-z]{2}-[A-Z]{2}$/.test(code)) return code.replace('-', '_')
      // default country for base language (rough heuristic)
      const fallback: Record<string, string> = { en: 'US', fr: 'FR', es: 'ES', pt: 'PT', de: 'DE', it: 'IT', nl: 'NL', ja: 'JP', ko: 'KR', zh: 'CN' }
      const cc = fallback[code] || code.toUpperCase()
      return `${code}_${cc}`
    }

    removeManaged('og-')

    const current = (lang || i18n.language || 'en') as string
    upsertMeta('og:locale', toOg(current), 'locale')

    // alternates for all other locales
    const alternates: string[] = []
    // common regionals to expose as alternates
    const regionalVariants = [
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
    // base
    alternates.push(...bases)
    // regional
    alternates.push(...regionalVariants)

    Array.from(new Set(alternates)).forEach((code) => {
      if (code === current) return
      upsertMeta('og:locale:alternate', toOg(code), `alt-${code}`)
    })

    return () => removeManaged('og-')
  }, [lang, location.pathname])

  return null
}
