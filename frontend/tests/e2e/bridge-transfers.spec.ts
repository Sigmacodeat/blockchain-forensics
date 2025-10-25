import { test, expect } from '@playwright/test';
import { mockAuth } from './auth.setup';

const mockLinks = [
  {
    from_address: '0xSource00000000000000000000000000000000000001',
    to_address: '0xTarget00000000000000000000000000000000000001',
    chain_from: 'ethereum',
    chain_to: 'polygon',
    bridge_name: 'Polygon PoS Bridge',
    tx_hash: '0xabcdef1234567890',
    timestamp: 1_726_000_000,
    value: 12.34,
  },
];

const mockStats = {
  total_bridge_transactions: 128,
  unique_addresses: 42,
  top_bridges: [
    {
      bridge_name: 'Polygon PoS Bridge',
      chain_from: 'ethereum',
      chain_to: 'polygon',
      transaction_count: 64,
    },
  ],
  chain_distribution: {
    ethereum: 80,
    polygon: 48,
  },
};

test.describe('Bridge Transfers Page', () => {
  let lastSearchParams: URLSearchParams | null;

  test.beforeEach(async ({ page }) => {
    lastSearchParams = null;
    await mockAuth(page, 'pro');

    await page.route('**/api/v1/appsumo/my-products', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ products: [], count: 0 }),
      });
    });

    await page.route('**/api/v1/bridge/statistics', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockStats),
      });
    });

    await page.route('**/api/v1/bridge/links**', async (route) => {
      const url = new URL(route.request().url());
      lastSearchParams = url.searchParams;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ total_links: mockLinks.length, links: mockLinks }),
      });
    });
  });

  test('lädt Daten und erlaubt gefilterte Suche', async ({ page }) => {
    await page.goto('/en/bridge-transfers');

    await page.waitForResponse('**/api/v1/bridge/links**');
    expect(lastSearchParams?.get('limit')).toBe('100');

    await expect(page.getByRole('heading', { name: /Bridge Transfers/i })).toBeVisible();
    await expect(page.locator('table')).toContainText('Polygon PoS Bridge');

    await page.fill('#address', '0xabc123');
    await page.fill('#chain_from', 'ethereum');
    await page.fill('#chain_to', 'polygon');

    await Promise.all([
      page.waitForResponse('**/api/v1/bridge/links**'),
      page.getByRole('button', { name: /suchen|search/i }).click(),
    ]);

    expect(lastSearchParams?.get('address')).toBe('0xabc123');
    expect(lastSearchParams?.get('chain_from')).toBe('ethereum');
    expect(lastSearchParams?.get('chain_to')).toBe('polygon');

    await expect(page.locator('table')).toContainText('0xSource0000');
  });

  test('exportiert CSV erfolgreich', async ({ page }) => {
    await page.goto('/en/bridge-transfers');
    await page.waitForResponse('**/api/v1/bridge/links**');

    const exportButton = page.getByRole('button', { name: /csv export/i });
    await expect(exportButton).toBeEnabled();

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      exportButton.click(),
    ]);

    expect(download.suggestedFilename()).toContain('bridge_links');
  });
});
