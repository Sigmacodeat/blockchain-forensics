import React from 'react'
import { useLocation } from 'react-router-dom'
import i18n from '@/i18n/config-optimized'

function upsertLink(rel: string, attrs: Record<string, string>, key: string) {
  const selectorParts = [
    `link[rel="${rel}"]`,
    ...Object.entries(attrs).map(([k, v]) => `[${k}="${v}"]`)
  ]
  const selector = selectorParts.join('') + `[data-managed="hreflang-${key}"]`
  let el = document.head.querySelector<HTMLLinkElement>(selector)
  if (!el) {
    el = document.createElement('link')
    el.setAttribute('rel', rel)
    el.setAttribute('data-managed', `hreflang-${key}`)
    Object.entries(attrs).forEach(([k, v]) => el!.setAttribute(k, v))
    document.head.appendChild(el)
  } else {
    Object.entries(attrs).forEach(([k, v]) => el!.setAttribute(k, v))
  }
}

function removeManaged(prefix: string) {
  const nodes = Array.from(document.head.querySelectorAll(`link[data-managed^="${prefix}"]`))
  nodes.forEach((n) => n.parentElement?.removeChild(n))
}

function stripLangPrefix(pathname: string): string {
  // Matches /en or /en-US or /de at start
  const re = /^\/[a-zA-Z]{2}(?:-[A-Z]{2})?(\/?|\b)/
  if (re.test(pathname)) {
    const rest = pathname.replace(re, '/')
    return rest === '//' ? '/' : rest
  }
  return pathname
}

export default function HreflangManager() {
  const location = useLocation()

  React.useEffect(() => {
    const origin = window.location.origin
    const resources = (i18n.options as any)?.resources || {}
    // Ensure critical languages are considered even if not preloaded as core languages
    const langs: string[] = Array.from(new Set([
      ...Object.keys(resources),
      'fa','ur','id','vi','th','bn'
    ]))
    // Zusätzliche regionale Varianten für vollständige hreflang-Abdeckung
    const regionalVariants = [
      'en-GB','en-US','en-AU','en-CA','en-NZ','en-ZA','en-SG','en-IE','en-IN','en-PH','en-HK',
      'es-ES','es-MX','es-AR','es-CL','es-CO','es-PE','es-VE','es-UY','es-419',
      'pt-PT','pt-BR','pt-AO','pt-MZ',
      'fr-FR','fr-CA','fr-BE','fr-CH','fr-LU','fr-DZ','fr-MA','fr-TN',
      'de-AT','de-CH','it-CH','nl-BE',
      'zh-CN','zh-TW','zh-HK','he-IL','fa-IR','ur-PK','id-ID','vi-VN','th-TH','bn-BD'
    ]

    const rest = stripLangPrefix(location.pathname)

    // Clean previous managed links
    removeManaged('hreflang-')
    removeManaged('canonical-')

    // Add alternates for each available base language
    langs.forEach((code) => {
      const href = `${origin}/${code}${rest}${location.search}${location.hash}`
      upsertLink('alternate', { hreflang: code, href }, code)
    })

    // Add alternates for regional variants (mapped to same path prefix)
    regionalVariants.forEach((code) => {
      const base = code.split('-')[0]
      // Wenn die Basissprache existiert, generieren wir auch die regionale hreflang-Variante
      if (langs.includes(base)) {
        const href = `${origin}/${code}${rest}${location.search}${location.hash}`
        upsertLink('alternate', { hreflang: code, href }, code)
      }
    })

    // x-default pointing to fallback language
    const fallback = (i18n.options as any)?.fallbackLng || 'en'
    const fallbackCode = Array.isArray(fallback) ? fallback[0] : fallback
    const xDefaultHref = `${origin}/${fallbackCode}${rest}${location.search}${location.hash}`
    upsertLink('alternate', { hreflang: 'x-default', href: xDefaultHref }, 'x-default')

    // canonical for current URL
    const canonicalHref = `${origin}${location.pathname}${location.search}${location.hash}`
    const link = document.createElement('link')
    link.setAttribute('rel', 'canonical')
    link.setAttribute('href', canonicalHref)
    link.setAttribute('data-managed', 'canonical-current')
    document.head.appendChild(link)

    return () => {
      removeManaged('hreflang-')
      removeManaged('canonical-')
    }
  }, [location.pathname, location.search, location.hash])

  return null
}
