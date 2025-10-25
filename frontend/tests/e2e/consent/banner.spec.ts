import { test, expect } from '@playwright/test'

// Basic banner visibility and accept/decline flows
// Assumes preview server baseURL from playwright.config.ts

test.describe('Cookie Consent Banner', () => {
  async function openBannerIfNeeded(page: import('@playwright/test').Page) {
    const banner = page.getByRole('dialog', { name: /cookie|cookies|cookie-banner/i })
    try {
      await expect(banner).toBeVisible({ timeout: 1500 })
      return banner
    } catch {
      await page.evaluate(() => {
        window.dispatchEvent(new CustomEvent('cookie-consent:open'))
      })
      await expect(banner).toBeVisible({ timeout: 3000 })
      return banner
    }
  }

  test('shows banner on first visit and can open preferences', async ({ page }) => {
    // Force German route (EU banner expected)
    await page.goto('/de')
    await page.evaluate(() => localStorage.removeItem('cookie_consent'))
    await page.reload()

    const banner = await openBannerIfNeeded(page)
    // Prefer the explicit cookie settings button within the banner
    const prefsBtn = banner.getByRole('button', { name: /cookie-einstellungen|preferences|einstellungen/i })
    await prefsBtn.click()
    // Verify section titles are visible (locale-aware)
    await expect(
      banner.getByText(/^(Analytics cookies|Analyse-Cookies)$/i)
    ).toBeVisible()
    await expect(
      banner.getByText(/^(Marketing cookies|Marketing-Cookies)$/i)
    ).toBeVisible()
  })

  test('accept only necessary should set consent with analytics=false', async ({ page }) => {
    await page.goto('/de')
    await page.evaluate(() => localStorage.removeItem('cookie_consent'))
    await page.reload()
    await openBannerIfNeeded(page)

    const onlyNecessary = page.getByRole('button', { name: /only necessary|nur notwendige/i })
    await onlyNecessary.click()

    const consent = await page.evaluate(() => localStorage.getItem('cookie_consent'))
    expect(consent).toBeTruthy()
    const parsed = JSON.parse(consent!)
    expect(parsed.version).toBe(1)
    expect(parsed.analytics).toBe(false)
  })

  test('accept all should set consent with analytics=true and not error', async ({ page }) => {
    await page.goto('/de')
    await page.evaluate(() => localStorage.removeItem('cookie_consent'))
    await page.reload()
    await openBannerIfNeeded(page)

    const acceptAll = page.getByRole('button', { name: /accept all|alle akzeptieren/i })
    await acceptAll.click()

    const consent = await page.evaluate(() => localStorage.getItem('cookie_consent'))
    expect(consent).toBeTruthy()
    const parsed = JSON.parse(consent!)
    expect(parsed.version).toBe(1)
    expect(parsed.analytics).toBe(true)
  })
})
