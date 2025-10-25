import { test, expect } from '@playwright/test'

// Navigation Smoke: public routes should render and top navigation should be present
// Assumes baseURL is configured in playwright.config.ts

const PUBLIC_ROUTES = ['/de', '/de/pricing', '/de/features', '/de/about']

test.describe('Public Navigation Smoke', () => {
  test('renders landing content', async ({ page }) => {
    await page.addInitScript(() => {
      try { localStorage.setItem('cookie_consent', JSON.stringify({ version: 1, analytics: false, ts: Date.now() })) } catch {}
    })
    const resp = await page.goto('/de', { waitUntil: 'domcontentloaded' })
    expect(resp?.ok()).toBeTruthy()
    // Check for prominent heading and main-like region
    const h1 = page.getByRole('heading', { level: 1 })
    await expect(h1.first()).toBeVisible({ timeout: 8000 })
    const mainLike = page.locator('#main-content, main, [role="main"]')
    await expect(mainLike.first()).toBeVisible({ timeout: 8000 })
  })

  for (const route of PUBLIC_ROUTES) {
    test(`renders page: ${route}`, async ({ page }) => {
      // Set consent early
      await page.addInitScript(() => {
        try { localStorage.setItem('cookie_consent', JSON.stringify({ version: 1, analytics: false, ts: Date.now() })) } catch {}
      })
      const resp = await page.goto(route, { waitUntil: 'domcontentloaded' })
      expect(resp?.ok()).toBeTruthy()
      const mainLike = page.locator('#main-content, main, [role="main"]')
      await expect(mainLike.first()).toBeVisible({ timeout: 8000 })
      // There should be at least a prominent heading (h1 or role heading level 1)
      const h1 = page.getByRole('heading', { level: 1 })
      await expect(h1.first()).toBeVisible({ timeout: 8000 })
    })
  }
})
