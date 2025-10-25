import { test, expect } from '@playwright/test';

import { mockAuth } from './auth.setup';

test.describe('Onboarding Tour', () => {
  test('startet automatisch und markiert Tour als gesehen', async ({ page }) => {
    await mockAuth(page, 'community');

    await page.goto('/en/dashboard');

    await expect(page.locator('[data-tour="quick-actions"]')).toBeVisible();

    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('joyride:complete'));
    });

    const storageKey = 'onboarding-community-v1-1';
    const seen = await page.evaluate((key) => localStorage.getItem(key), storageKey);
    expect(seen).toBe('true');
  });
});
