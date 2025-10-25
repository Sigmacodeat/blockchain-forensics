import { test, expect } from '@playwright/test'

// Simple availability checks for static health endpoints served by preview

test.describe('Frontend health endpoints', () => {
  test('GET /healthz returns ok', async ({ request, baseURL }) => {
    const res = await request.get(baseURL! + '/healthz')
    expect(res.ok()).toBeTruthy()
    const text = await res.text()
    expect(text.trim()).toBe('ok')
  })

  test('GET /readyz returns ok', async ({ request, baseURL }) => {
    const res = await request.get(baseURL! + '/readyz')
    expect(res.ok()).toBeTruthy()
    const text = await res.text()
    expect(text.trim()).toBe('ok')
  })
})
