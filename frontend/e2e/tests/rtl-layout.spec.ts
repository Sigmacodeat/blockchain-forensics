import { test, expect } from '@playwright/test'

test.describe('RTL Layout Support', () => {
  const rtlLocales = ['ar', 'he']

  for (const lang of rtlLocales) {
    test(`RTL rendering for ${lang}`, async ({ page, baseURL }) => {
      await page.goto(`${baseURL}/${lang}/chatbot`, { waitUntil: 'domcontentloaded' })

      // Check root dir attribute
      const htmlDir = await page.locator('html').getAttribute('dir')
      expect(htmlDir).toBe('rtl')

      // Check layout doesn't break (no horizontal scrollbar, visual checks)
      const bodyWidth = await page.locator('body').evaluate((el) => el.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)
      // Allow small tolerance
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20)

      // Verify text alignment (basic sanity)
      const heading = page.locator('h1').first()
      if (await heading.count() > 0) {
        const textAlign = await heading.evaluate((el) => window.getComputedStyle(el).textAlign)
        // RTL typically aligns right or start (which is right in RTL context)
        expect(['right', 'start', 'inherit', '']).toContain(textAlign)
      }
    })
  }
})
