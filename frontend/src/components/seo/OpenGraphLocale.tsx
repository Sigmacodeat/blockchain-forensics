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
      'en-GB','en-US','en-AU','en-CA','en-NZ','en-ZA','en-SG','en-IE','en-IN','en-PH','en-HK',
      'es-ES','es-MX','es-AR','es-CL','es-CO','es-PE','es-VE','es-UY','es-419',
      'pt-PT','pt-BR','pt-AO','pt-MZ',
      'fr-FR','fr-CA','fr-BE','fr-CH','fr-LU','fr-DZ','fr-MA','fr-TN',
      'de-AT','de-CH','it-CH','nl-BE',
      'zh-CN','zh-TW','zh-HK','he-IL'
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
