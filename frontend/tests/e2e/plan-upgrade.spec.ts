/**
 * Plan Upgrade Flow E2E Tests (Mocked Backend)
 * Validates plan visibility, billing toggle and checkout request flow
 */
import { test, expect } from '@playwright/test';
import { mockAuth } from './auth.setup';

const API_MATCHER = '**/api/v1/billing/**';

test.describe('Plan Upgrade Flow', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuth(page, 'community');

    await page.route('**/api/v1/billing/tenant/plan', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ plan_id: 'community' }),
      });
    });

    await page.route('**/api/v1/billing/checkout', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ url: null }),
      });
    });
  });

  test('zeigt Plan-Karten mit Preisen', async ({ page }) => {
    await page.goto('/en/pricing');

    const proCard = page.getByTestId('plan-card-pro');
    await expect(proCard).toBeVisible();
    await expect(proCard).toContainText('Pro');

    const proPrice = page.getByTestId('plan-price-pro');
    await expect(proPrice).toContainText('$49');
  });

  test('sendet Checkout-Request für Pro-Plan', async ({ page }) => {
    await page.goto('/en/pricing');

    const checkoutButton = page.getByTestId('checkout-pro');
    await expect(checkoutButton).toBeVisible();

    const [request] = await Promise.all([
      page.waitForRequest('**/api/v1/billing/checkout'),
      checkoutButton.click(),
    ]);

    const payload = request.postDataJSON() as Record<string, unknown> | undefined;
    expect(payload).toMatchObject({ plan_id: 'pro' });
  });

  test('zeigt Jahresrabatt nach Toggle', async ({ page }) => {
    await page.goto('/en/pricing');

    await page.click('[data-testid="billing-toggle"]');

    const savingsBadge = page.locator('#savings-pro');
    await expect(savingsBadge).toBeVisible();
    await expect(savingsBadge).toContainText('Spare');
  });
});
