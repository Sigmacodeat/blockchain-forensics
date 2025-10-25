import { test, expect } from '@playwright/test'

const LOCALES = ['en', 'es', 'ar', 'ja']

for (const lang of LOCALES) {
  test.describe(`SEO i18n for ${lang}`, () => {
    test(`meta, canonical, hreflang valid for /${lang}/chatbot`, async ({ page, baseURL }) => {
      await page.goto(`${baseURL}/${lang}/chatbot`, { waitUntil: 'domcontentloaded' })

      // Title present
      const title = await page.title()
      expect(title.length).toBeGreaterThan(5)

      // Description present
      const desc = await page.locator('meta[name="description"]').first().getAttribute('content')
      expect(desc).toBeTruthy()

      // Canonical contains locale
      const canonical = await page.locator('link[rel="canonical"]').getAttribute('href')
      expect(canonical).toContain(`/${lang}/chatbot`)

      // hreflang x-default exists
      await expect(page.locator('link[rel="alternate"][hreflang="x-default"]')).toHaveCount(1)

      // At least some alternates present (including current lang)
      await expect(page.locator(`link[rel="alternate"][hreflang="${lang}"]`)).toHaveCount(1)

      // OG Image present
      const ogImage = await page.locator('meta[property="og:image"]').getAttribute('content')
      expect(ogImage).toBeTruthy()
    })
  })
}
