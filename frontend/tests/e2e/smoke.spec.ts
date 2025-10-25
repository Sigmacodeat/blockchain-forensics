import { test, expect } from '@playwright/test';

// Minimal, robuste Smoke-Checks für öffentliche Seiten
test.describe('Public smoke', () => {
  test('landing page renders and language redirect works', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/\w{2}(-[A-Z]{2})?\/?$/);
    await expect(page.getByRole('navigation').first()).toBeVisible();
  });

  test('pricing page loads', async ({ page }) => {
    await page.goto('/en/pricing');
    await expect(page).toHaveURL(/\/en\/pricing/);
    // Akzeptiere irgendeine sichtbare Überschrift als Beleg, dass Seite lädt
    await expect(page.getByRole('heading').first()).toBeVisible();
  });
});
