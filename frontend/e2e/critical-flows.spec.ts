/**
 * E2E Tests - Critical User Journeys
 */

import { test, expect } from '@playwright/test'

test.describe('Critical Flows', () => {
  test('should complete registration', async ({ page }) => {
    await page.goto('/en/register')
    await page.fill('input[name="email"]', `test-${Date.now()}@example.com`)
    await page.fill('input[name="password"]', 'Secure123!')
    await page.fill('input[name="confirmPassword"]', 'Secure123!')
    await page.check('input[type="checkbox"]')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/\/verify/)
  })

  test('should redeem AppSumo code', async ({ page }) => {
    await page.goto('/en/login')
    await page.fill('input[name="email"]', 'test@example.com')
    await page.fill('input[name="password"]', 'Test123!')
    await page.click('button[type="submit"]')
    await page.waitForURL(/\/dashboard/)
    
    await page.goto('/en/redeem/appsumo')
    await page.fill('input[placeholder*="code"]', 'CHATBOT-2-TEST12345')
    await page.click('button:has-text("Redeem")')
    await expect(page.locator('text=/success/i')).toBeVisible({ timeout: 10000 })
  })

  test('should generate AppSumo codes as admin', async ({ page }) => {
    await page.goto('/en/login')
    await page.fill('input[name="email"]', 'admin@example.com')
    await page.fill('input[name="password"]', 'Admin123!')
    await page.click('button[type="submit"]')
    
    await page.goto('/en/admin/appsumo/manager')
    await page.selectOption('select[name="product"]', 'chatbot')
    await page.selectOption('select[name="tier"]', '2')
    await page.fill('input[name="quantity"]', '10')
    await page.click('button:has-text("Generate")')
    await expect(page.locator('text=/generated/i')).toBeVisible({ timeout: 10000 })
  })

  test('should open institutional verification admin page', async ({ page }) => {
    await page.goto('/en/login')
    await page.fill('input[name="email"]', 'admin@example.com')
    await page.fill('input[name="password"]', 'Admin123!')
    await page.click('button[type="submit"]')

    await page.goto('/en/admin/institutional-verifications')

    await expect(page.locator('h1:has-text("Institutional Verification")')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('button:has-text("Review starten")').first()).toBeVisible({ timeout: 10000 })
  })

  test('should handle multilingual', async ({ page }) => {
    await page.goto('/en')
    await page.click('[data-testid="language-selector"]')
    await page.click('text=Deutsch')
    await expect(page).toHaveURL(/\/de\//)
  })
})
