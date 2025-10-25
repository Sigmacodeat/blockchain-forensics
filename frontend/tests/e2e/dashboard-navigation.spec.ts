import { test, expect } from '@playwright/test';
import { mockAuth } from './auth.setup';

test.describe('Dashboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuth(page, 'pro');

    await page.route('**/api/v1/appsumo/my-products', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ products: [], count: 0 }),
      });
    });

    await page.goto('/en/dashboard');
  });

  test('zeigt Sidebar-Links und erlaubt Navigation', async ({ page }) => {
    const sidebar = page.locator('[data-tour="sidebar"]');
    await expect(sidebar).toBeVisible();

    await page.locator('[data-tour="trace-action"] a').click();
    await expect(page).toHaveURL(/\/en\/trace/);

    await page.locator('[data-tour="investigator-action"] a').click();
    await expect(page).toHaveURL(/\/en\/investigator/);
  });

  test('Command Palette navigiert zu Cases', async ({ page }) => {
    await page.keyboard.press('Meta+K');

    const palette = page.locator('[role="dialog"]');
    await expect(palette).toBeVisible();

    await page.getByPlaceholder(/search/i).fill('Cases');

    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\/en\/cases/);
  });
});
