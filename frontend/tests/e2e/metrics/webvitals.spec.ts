import { test, expect } from '@playwright/test'

// Verify Web Vitals are not sent without analytics consent, and are sent after consent

test.describe('Web Vitals consent gating', () => {
  test('blocks without consent, sends after accept all', async ({ page }) => {
    let requests = 0
    await page.route('**/api/v1/metrics/webvitals', (route) => {
      requests++
      route.fulfill({ status: 200, body: JSON.stringify({ status: 'ok' }) })
    })

    // Start with no consent
    await page.addInitScript(() => {
      try { localStorage.removeItem('cookie_consent') } catch {}
    })

    await page.goto('/de', { waitUntil: 'domcontentloaded' })

    // Wait briefly for any initial vitals - should not send
    await page.waitForTimeout(500)
    expect(requests).toBe(0)

    // Open cookie banner and accept all
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('cookie-consent:open'))
    })
    const banner = page.getByRole('dialog', { name: /cookie|cookies/i })
    await expect(banner).toBeVisible()
    await banner.getByRole('button', { name: /alle akzeptieren|accept all/i }).click()

    // After consent, a vitals event should eventually be sent
    await expect.poll(() => requests, { timeout: 3000 }).toBeGreaterThan(0)
  })
})
