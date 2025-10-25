import React from 'react'

function upsertMeta(name: string, content: string, key: string) {
  if (!content) return
  const selector = `meta[name="${name}"][data-managed="verify-${key}"]`
  let el = document.head.querySelector<HTMLMetaElement>(selector)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute('name', name)
    el.setAttribute('data-managed', `verify-${key}`)
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

export default function VerificationTags() {
  React.useEffect(() => {
    const gsc = (import.meta as any).env?.VITE_GSC_VERIFICATION || ''
    const bing = (import.meta as any).env?.VITE_BING_VERIFICATION || ''
    const yandex = (import.meta as any).env?.VITE_YANDEX_VERIFICATION || ''
    const naver = (import.meta as any).env?.VITE_NAVER_VERIFICATION || ''

    removeManaged('verify-')
    if (gsc) upsertMeta('google-site-verification', gsc, 'gsc')
    if (bing) upsertMeta('msvalidate.01', bing, 'bing')
    if (yandex) upsertMeta('yandex-verification', yandex, 'yandex')
    if (naver) upsertMeta('naver-site-verification', naver, 'naver')

    return () => removeManaged('verify-')
  }, [])
  return null
}
