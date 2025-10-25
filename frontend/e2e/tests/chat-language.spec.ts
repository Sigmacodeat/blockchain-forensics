import { test, expect } from '@playwright/test'

// Validate that chat network calls include the lang parameter for locale pages
// NOTE: This test relies on public endpoints and may be skipped if blocked by CORS/WAF.

test.describe('Chat language propagation', () => {
  const locales = ['es', 'fr', 'ja']

  for (const lang of locales) {
    test(`includes lang=${lang} in SSE/WS for /${lang}/chatbot`, async ({ page, baseURL }) => {
      // Intercept stream and websocket requests
      const ssePromise = page.waitForRequest((req) => {
        const url = new URL(req.url())
        return (
          (url.pathname.endsWith('/api/v1/ai/chat/stream') || url.pathname.endsWith('/api/v1/chat/stream')) &&
          url.searchParams.get('lang') === lang
        )
      }, { timeout: 15000 }).catch(() => null)

      const wsPromise = new Promise<boolean>((resolve) => {
        page.on('websocket', (ws) => {
          try {
            const u = new URL(ws.url())
            if ((u.pathname.endsWith('/ws/chat') || u.pathname.endsWith('/api/v1/ws/chat')) && u.searchParams.get('lang') === lang) {
              resolve(true)
            }
          } catch {}
        })
        // timeout safety
        setTimeout(() => resolve(false), 15000)
      })

      await page.goto(`${baseURL}/${lang}/chatbot`, { waitUntil: 'domcontentloaded' })

      // Open the chat widget (button usually at bottom-right)
      // Fallback: send keyboard shortcut to focus widget if needed.
      const openBtn = page.locator('button[aria-label*="Chat"i], button[aria-label*="öffnen"i]').first()
      if (await openBtn.count()) {
        await openBtn.click({ trial: false }).catch(() => {})
      }

      // Type something into potential input and submit to trigger network
      const input = page.locator('input[aria-label*="Nachricht"i], textarea').first()
      if (await input.count()) {
        await input.fill('Hola, prueba de idioma.')
        // Try submit button
        const sendBtn = page.locator('button:has-text("Senden"), button:has-text("Send"), button[type="submit"]').first()
        if (await sendBtn.count()) {
          await sendBtn.click().catch(() => {})
        } else {
          await input.press('Enter').catch(() => {})
        }
      }

      const sse = await ssePromise
      const ws = await wsPromise
      expect(Boolean(sse) || Boolean(ws)).toBeTruthy()
    })
  }
})
