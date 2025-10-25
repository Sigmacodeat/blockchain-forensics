import { expect, Page } from '@playwright/test'

export async function gotoDEAndReset(page: Page) {
  await page.goto('/de')
  await page.evaluate(() => localStorage.removeItem('cookie_consent'))
  await page.reload()
}

export async function openBannerIfNeeded(page: Page) {
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
