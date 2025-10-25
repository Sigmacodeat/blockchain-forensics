import type { ConsentState } from '@/components/legal/CookieConsent'

const STORAGE_KEY = 'cookie_consent'
const CONSENT_VERSION = 1

export function getConsent(): ConsentState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const val = JSON.parse(raw) as ConsentState
    if (!val || typeof val !== 'object') return null
    if (val.version !== CONSENT_VERSION) return null
    return val
  } catch {
    return null
  }
}

export type ConsentCallback = (consent: ConsentState) => void

export function onConsentChange(cb: ConsentCallback) {
  const handler = (ev: Event) => {
    try {
      const detail = (ev as CustomEvent).detail as ConsentState
      if (detail && typeof detail === 'object') cb(detail)
    } catch {}
  }
  window.addEventListener('cookie-consent:changed', handler as EventListener)
  return () => window.removeEventListener('cookie-consent:changed', handler as EventListener)
}
