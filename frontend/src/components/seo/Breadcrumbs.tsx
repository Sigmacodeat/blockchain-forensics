import React from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

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

function removeManaged(idPrefix: string) {
  document.head
    .querySelectorAll(`script[data-managed^="jsonld-${idPrefix}"]`)
    .forEach((n) => n.parentElement?.removeChild(n))
}

export default function Breadcrumbs() {
  const location = useLocation()
  const { lang } = useParams()
  const { t, i18n } = useTranslation()

  React.useEffect(() => {
    // Warten bis Übersetzungs-Resources geladen sind, um missingKey-Logs zu vermeiden
    const nsReady = (typeof i18n.hasLoadedNamespace === 'function' && i18n.hasLoadedNamespace('translation'))
      || (typeof i18n.hasResourceBundle === 'function' && i18n.hasResourceBundle(i18n.language, 'translation'))
    if (!nsReady) {
      removeManaged('breadcrumbs')
      return
    }

    const origin = window.location.origin
    const pathname = location.pathname
    // expect language prefix: /:lang(/-REGION)?/...
    const parts = pathname.replace(/^\/(?:[a-zA-Z]{2}(?:-[A-Z]{2})?)\/?/, '').split('/').filter(Boolean)

    // Do not render breadcrumbs on auth or 404 fallbacks
    const isAuth = /^(login|register|forgot-password)$/.test(parts[0] || '')
    if (isAuth) {
      removeManaged('breadcrumbs')
      return
    }

    const items: Array<{ '@type': 'ListItem'; position: number; name: string; item: string }> = []

    // Home
    const base = `/${lang || 'en'}`
    items.push({ '@type': 'ListItem', position: 1, name: t('breadcrumb.home', 'Home'), item: `${origin}${base}/` })

    const nameMap: Record<string, string> = {
      features: t('breadcrumb.features', 'Features'),
      about: t('breadcrumb.about', 'Über uns'),
      pricing: t('breadcrumb.pricing', 'Preise'),
      search: t('breadcrumb.search', 'Suche'),
      dashboards: t('breadcrumb.dashboards', 'Dashboards'),
      monitoring: t('breadcrumb.monitoring', 'Monitoring'),
      'monitoring/dashboard': t('breadcrumb.monitoring_dashboard', 'Monitoring Dashboard'),
      'legal': t('breadcrumb.legal', 'Rechtliches'),
      'legal/privacy': t('breadcrumb.privacy', 'Datenschutz'),
      'legal/terms': t('breadcrumb.terms', 'AGB'),
      'legal/impressum': t('breadcrumb.impressum', 'Impressum')
    }

    let acc = ''
    parts.forEach((segment, i) => {
      acc = acc ? `${acc}/${segment}` : segment
      const key = acc as keyof typeof nameMap
      const label = nameMap[acc] || segment
      items.push({
        '@type': 'ListItem',
        position: i + 2,
        name: label,
        item: `${origin}${base}/${acc}`
      })
    })

    const data = {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: items
    }

    upsertJsonLd('breadcrumbs', data)

    return () => removeManaged('breadcrumbs')
  }, [location.pathname, lang, i18n.language])

  return null
}
