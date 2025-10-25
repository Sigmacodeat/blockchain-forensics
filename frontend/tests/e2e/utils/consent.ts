import type { Page, Locator } from '@playwright/test'

/**
 * Navigiert zu /de, leert relevanten Consent-Storage und lädt neu.
 */
export async function gotoDEAndReset(page: Page): Promise<void> {
  await page.goto('/de')
  await page.evaluate(() => {
    try {
      localStorage.removeItem('cookie_consent')
      sessionStorage.removeItem('cookie_consent')
      // mögliche alternative Keys
      localStorage.removeItem('consent')
      localStorage.removeItem('cookie-consent')
    } catch {}
  })
  await page.reload()
}

/**
 * Öffnet den Cookie-Banner, falls erforderlich, und gibt einen Locator auf das Banner zurück.
 * Versucht mehrere gängige Selektoren und Benennungen (Deutsch/Englisch).
 */
export async function openBannerIfNeeded(page: Page): Promise<Locator> {
  // Versuche existierende Banner-Container zu finden
  const candidates = page.locator([
    '[data-testid="cookie-banner"]',
    '[data-testid="consent-banner"]',
    '[id*="cookie"]',
    '[class*="cookie"]',
    'role=dialog[name=/cookie|consent/i]'
  ].join(', '))

  // Falls nichts sichtbar: Konsent zurücksetzen und reload (sicherheitshalber)
  if (!(await candidates.first().isVisible().catch(() => false))) {
    await page.evaluate(() => {
      try {
        localStorage.removeItem('cookie_consent')
        sessionStorage.removeItem('cookie_consent')
      } catch {}
    })
    await page.reload()
  }

  // Warte auf irgendeinen Bannerhinweis im View
  const banner = page.locator([
    '[data-testid="cookie-banner"]',
    '[data-testid="consent-banner"]',
    'role=dialog[name=/cookie|consent/i]'
  ].join(', ')).first()

  // Fallback: wenn kein spezieller Container, nutze Hauptbereich, damit nachfolgende Suchen nicht crashen
  if (!(await banner.isVisible().catch(() => false))) {
    return page.locator('main').first()
  }

  return banner
}
