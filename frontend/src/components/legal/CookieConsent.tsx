import React from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useI18n } from '@/contexts/I18nContext'

// Minimaler DSGVO-Cookie-Banner mit lokaler Präferenzspeicherung
// Speichert Auswahl in localStorage unter "cookie_consent"

export type ConsentState = {
  necessary: boolean
  analytics: boolean
  marketing: boolean
  timestamp: number
  version: number
}

// Helper to open cookie banner programmatically
export function openCookieConsent(showPrefs: boolean = false) {
  try {
    const ev = new CustomEvent('cookie-consent:open', { detail: { showPrefs } })
    window.dispatchEvent(ev)
  } catch {}
}

const CONSENT_VERSION = 1
const STORAGE_KEY = 'cookie_consent'

const EU_LANGS = new Set([
  'de','fr','es','it','pt','nl','pl','cs','sk','hu','ro','bg','el','sl','sr','bs','mk','sq','lt','lv','et','fi','sv','da','ga','mt','lb','rm'
])

export function loadConsent(): ConsentState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const val = JSON.parse(raw) as ConsentState
    if (!val || typeof val !== 'object') return null
    if (val.version !== CONSENT_VERSION) return null
    return val
  } catch { return null }
}

function saveConsent(consent: ConsentState) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(consent))
  } catch {}
}

function emitConsentChanged(consent: ConsentState) {
  try {
    const ev = new CustomEvent('cookie-consent:changed', { detail: consent })
    window.dispatchEvent(ev)
  } catch {}
}

export default function CookieConsent() {
  const { currentLanguage, t } = useI18n()
  const [open, setOpen] = React.useState(false)
  const [showPrefs, setShowPrefs] = React.useState(false)
  const [optAnalytics, setOptAnalytics] = React.useState(false)
  const [optMarketing, setOptMarketing] = React.useState(false)
  const masterRef = React.useRef<HTMLInputElement | null>(null)
  const bannerRef = React.useRef<HTMLDivElement | null>(null)
  const allOn = optAnalytics && optMarketing
  const noneOn = !optAnalytics && !optMarketing
  const mixed = !allOn && !noneOn

  React.useEffect(() => {
    const existing = loadConsent()
    const isEU = EU_LANGS.has((currentLanguage || 'en').split('-')[0])
    // Respect Do Not Track: default toggles remain false; still show banner in EU
    if (!existing && isEU) setOpen(true)
  }, [currentLanguage])

  // Allow other components to open the cookie banner/preferences via CustomEvent
  React.useEffect(() => {
    function onOpen(ev: Event) {
      const detail = (ev as CustomEvent).detail || {}
      setShowPrefs(!!detail.showPrefs)
      setOpen(true)
    }
    window.addEventListener('cookie-consent:open', onOpen as EventListener)
    return () => window.removeEventListener('cookie-consent:open', onOpen as EventListener)
  }, [])

  // Reflect mixed state on the master checkbox (indeterminate UI)
  React.useEffect(() => {
    if (masterRef.current) {
      masterRef.current.indeterminate = mixed
    }
  }, [mixed])

  // Focus banner on open, ESC to close
  React.useEffect(() => {
    if (!open) return
    const node = bannerRef.current
    node?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open])

  const acceptAll = () => {
    const consent: ConsentState = { necessary: true, analytics: true, marketing: true, timestamp: Date.now(), version: CONSENT_VERSION }
    saveConsent(consent)
    emitConsentChanged(consent)
    setOpen(false)
  }
  const acceptNecessary = () => {
    const consent: ConsentState = { necessary: true, analytics: false, marketing: false, timestamp: Date.now(), version: CONSENT_VERSION }
    saveConsent(consent)
    emitConsentChanged(consent)
    setOpen(false)
  }
  const savePreferences = () => {
    const consent: ConsentState = { necessary: true, analytics: optAnalytics, marketing: optMarketing, timestamp: Date.now(), version: CONSENT_VERSION }
    saveConsent(consent)
    emitConsentChanged(consent)
    setOpen(false)
  }
  const openPrefs = () => {
    const existing = loadConsent()
    if (existing) {
      setOptAnalytics(!!existing.analytics)
      setOptMarketing(!!existing.marketing)
    }
    setShowPrefs(true)
  }

  // Listen for programmatic open requests via CustomEvent
  React.useEffect(() => {
    const handler = (e: Event) => {
      try {
        const detail = (e as CustomEvent).detail as { showPrefs?: boolean } | undefined
        if (detail?.showPrefs) {
          openPrefs()
        }
        setOpen(true)
      } catch {
        setOpen(true)
      }
    }
    window.addEventListener('cookie-consent:open', handler as EventListener)
    return () => {
      window.removeEventListener('cookie-consent:open', handler as EventListener)
    }
  }, [])

  if (!open) return null

  return (
    <div className="fixed inset-x-0 bottom-0 z-[60] px-4 pb-4" role="region" aria-label={t('cookie.banner_aria', { defaultValue: 'Cookie-Banner' })}>
      <div
        ref={bannerRef}
        tabIndex={-1}
        className="mx-auto max-w-5xl rounded-xl border border-border bg-background shadow-xl"
        role="dialog"
        aria-modal="false"
        aria-labelledby="cookie-banner-title"
        aria-describedby="cookie-banner-desc"
      >
        <div className="p-4 sm:p-5">
          <h2 id="cookie-banner-title" className="text-base font-semibold mb-1">
            {t('cookie.title', { defaultValue: 'Cookies & Datenschutz' })}
          </h2>
          <p id="cookie-banner-desc" className="text-sm text-muted-foreground mb-3">
            {t('cookie.description', { defaultValue: 'Wir verwenden essenzielle Cookies für den Betrieb dieser Website. Optionale Analyse-Cookies helfen uns, die Nutzung zu verstehen und zu verbessern. Du kannst alle Cookies akzeptieren oder nur notwendige zulassen. Deine Auswahl kannst du jederzeit in den Einstellungen ändern.' })}
          </p>
          {showPrefs && (
            <div className="mb-3 border rounded-md p-3">
              {/* Master toggle: enable/disable all optional cookies */}
              <div className="flex items-start gap-3 mb-3">
                <input
                  id="cc-all-optional"
                  type="checkbox"
                  className="mt-1 h-4 w-4"
                  ref={masterRef}
                  checked={allOn}
                  aria-checked={mixed ? 'mixed' : (allOn ? 'true' : 'false')}
                  onChange={(e) => {
                    const v = e.target.checked
                    setOptAnalytics(v)
                    setOptMarketing(v)
                  }}
                />
                <label htmlFor="cc-all-optional" className="text-sm">
                  <span className="font-medium block">{t('cookie.all_optional_title', { defaultValue: 'Alle optionalen aktivieren' })}</span>
                  <span className="text-muted-foreground">{t('cookie.all_optional_desc', { defaultValue: 'Aktiviert sowohl Analyse- als auch Marketing-Cookies.' })}</span>
                </label>
              </div>
              <div className="flex items-start gap-3 mb-2">
                <input id="cc-analytics" data-testid="toggle-analytics" type="checkbox" className="mt-1 h-4 w-4" checked={optAnalytics} onChange={(e) => setOptAnalytics(e.target.checked)} />
                <label htmlFor="cc-analytics" className="text-sm">
                  <span className="font-medium block">{t('cookie.analytics_title', { defaultValue: 'Analyse-Cookies' })}</span>
                  <span className="text-muted-foreground">{t('cookie.analytics_desc', { defaultValue: 'Hilft uns, Nutzungsmuster zu verstehen und die Website zu verbessern.' })}</span>
                </label>
              </div>
              <div className="flex items-start gap-3">
                <input id="cc-marketing" data-testid="toggle-marketing" type="checkbox" className="mt-1 h-4 w-4" checked={optMarketing} onChange={(e) => setOptMarketing(e.target.checked)} />
                <label htmlFor="cc-marketing" className="text-sm">
                  <span className="font-medium block">{t('cookie.marketing_title', { defaultValue: 'Marketing-Cookies' })}</span>
                  <span className="text-muted-foreground">{t('cookie.marketing_desc', { defaultValue: 'Ermöglicht personalisierte Inhalte und Angebote.' })}</span>
                </label>
              </div>
            </div>
          )}
          <div className="flex items-center gap-3 mb-3 text-xs text-muted-foreground">
            <Link to={`/${currentLanguage}/legal/privacy`} className="underline hover:text-primary">
              {t('cookie.privacy_link', { defaultValue: 'Datenschutzerklärung' })}
            </Link>
            <span aria-hidden>·</span>
            <Link to={`/${currentLanguage}/legal/terms`} className="underline hover:text-primary">
              {t('cookie.terms_link', { defaultValue: 'Nutzungsbedingungen' })}
            </Link>
            {currentLanguage === 'de' && (
              <>
                <span aria-hidden>·</span>
                <Link to={`/${currentLanguage}/legal/impressum`} className="underline hover:text-primary">
                  {t('cookie.imprint_link', { defaultValue: 'Impressum' })}
                </Link>
              </>
            )}
          </div>
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 justify-end">
            {!showPrefs && (
              <Button variant="secondary" onClick={openPrefs} aria-label={t('cookie.preferences', { defaultValue: 'Einstellungen' })}>
                {t('cookie.preferences', { defaultValue: 'Einstellungen' })}
              </Button>
            )}
            {showPrefs && (
              <Button data-testid="save-preferences" variant="outline" onClick={savePreferences} aria-label={t('cookie.save_preferences', { defaultValue: 'Auswahl speichern' })}>
                {t('cookie.save_preferences', { defaultValue: 'Auswahl speichern' })}
              </Button>
            )}
            <Button variant="outline" onClick={acceptNecessary} aria-label={t('cookie.only_necessary', { defaultValue: 'Nur notwendige Cookies' })}>
              {t('cookie.only_necessary', { defaultValue: 'Nur notwendige' })}
            </Button>
            <Button onClick={acceptAll} aria-label={t('cookie.accept_all', { defaultValue: 'Alle Cookies akzeptieren' })}>
              {t('cookie.accept_all', { defaultValue: 'Alle akzeptieren' })}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
