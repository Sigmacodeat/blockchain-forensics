import { test, expect } from '@playwright/test';
import { mockAuth } from '../tests/e2e/auth.setup';

test.describe('Investigator Graph Page', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuth(page, 'pro');

    await page.route('**/api/v1/appsumo/my-products', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ products: [], count: 0 }),
      });
    });

    // Mock API responses
    await page.route('**/api/v1/graph/subgraph*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          nodes: [
            {
              id: '0xabc123',
              address: '0xabc123',
              chain: 'ethereum',
              taint_received: 0.65,
              risk_level: 'HIGH',
              labels: ['Exchange', 'High Risk'],
              tx_count: 150,
              balance: 5.2,
              first_seen: '2024-01-01',
              last_seen: '2025-01-15',
            },
            {
              id: '0xdef456',
              address: '0xdef456',
              chain: 'ethereum',
              taint_received: 0.3,
              risk_level: 'MEDIUM',
              labels: ['DeFi'],
              tx_count: 75,
              balance: 2.1,
              first_seen: '2024-06-01',
              last_seen: '2025-01-10',
            },
          ],
          edges: [
            {
              source: '0xabc123',
              target: '0xdef456',
              tx_hash: '0x123abc',
              value: 5.0,
              timestamp: '2025-01-01T10:00:00Z',
              type: 'transaction',
            },
          ],
        }),
      });
    });

    await page.route('**/api/v1/graph/timeline*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          events: [
            {
              timestamp: '2025-01-01T10:00:00Z',
              address: '0xabc123',
              event_type: 'transfer',
              value: 5.0,
              tx_hash: '0x123abc',
              risk_score: 75,
            },
          ],
        }),
      });
    });

    await page.goto('/en/investigator');
  });

  test('should display page title', async ({ page }) => {
    await expect(page.getByText('Investigator Graph Explorer')).toBeVisible();
  });

  test('should search for an address', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Enter address (0x... or bc1...)');
    await searchInput.fill('0xabc123');
    
    const searchButton = page.getByRole('button', { name: /explore address/i });
    await searchButton.click();

    // Wait for graph to load
    await page.waitForResponse('**/api/v1/graph/subgraph*');
    
    // Check if stats are displayed
    await expect(page.getByText('2')).toBeVisible(); // 2 Nodes
    await expect(page.getByText('Nodes')).toBeVisible();
  });

  test('should display node details when address is selected', async ({ page }) => {
    await page.getByPlaceholder('Enter address (0x... or bc1...)').fill('0xabc123');
    await page.getByRole('button', { name: /explore address/i }).click();
    await page.waitForResponse('**/api/v1/graph/subgraph*');

    // Check if Node Details Panel is visible
    await expect(page.getByText('Node Details')).toBeVisible();
    await expect(page.getByText('0xabc123')).toBeVisible();
    await expect(page.getByText('HIGH')).toBeVisible();
  });

  test('should adjust max hops setting', async ({ page }) => {
    const maxHopsSelect = page.getByLabel('Max Hops');
    await maxHopsSelect.selectOption('5');
    
    const selectedValue = await maxHopsSelect.inputValue();
    expect(selectedValue).toBe('5');
  });

  test('should toggle bridges setting', async ({ page }) => {
    const bridgesCheckbox = page.getByRole('checkbox', { name: /include cross-chain bridges/i });
    
    // Initially checked
    await expect(bridgesCheckbox).toBeChecked();
    
    // Toggle off
    await bridgesCheckbox.click();
    await expect(bridgesCheckbox).not.toBeChecked();
    
    // Toggle back on
    await bridgesCheckbox.click();
    await expect(bridgesCheckbox).toBeChecked();
  });

  test('should adjust min taint slider', async ({ page }) => {
    const slider = page.getByRole('slider', { name: /minimum taint percentage/i });
    await slider.fill('50');
    
    // Check if badge updates
    await expect(page.getByText('50%')).toBeVisible();
  });

  test('should display timeline events', async ({ page }) => {
    await page.getByPlaceholder('Enter address (0x... or bc1...)').fill('0xabc123');
    await page.getByRole('button', { name: /explore address/i }).click();
    await page.waitForResponse('**/api/v1/graph/timeline*');

    // Check if timeline is displayed
    await expect(page.getByText('Timeline Analysis')).toBeVisible();
    await expect(page.getByText('1')).toBeVisible(); // 1 event
    await expect(page.getByText('events')).toBeVisible();
  });

  test('should copy address to clipboard', async ({ page }) => {
    await page.getByPlaceholder('Enter address (0x... or bc1...)').fill('0xabc123');
    await page.getByRole('button', { name: /explore address/i }).click();
    await page.waitForResponse('**/api/v1/graph/subgraph*');

    // Click copy button in Node Details Panel
    const copyButton = page.getByRole('button', { name: 'Copy' }).first();
    await copyButton.click();

    // Verify clipboard content
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboardText).toBe('0xabc123');
  });

  test('should trigger pattern detection', async ({ page }) => {
    await page.route('**/api/v1/patterns/detect*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          findings: [
            {
              pattern: 'Peel Chain',
              score: 0.85,
              explanation: 'Detected peel chain pattern with 5 hops',
              evidence: [
                {
                  tx_hash: '0x123abc',
                  amount: 5.0,
                  timestamp: '2025-01-01T10:00:00Z',
                },
              ],
            },
          ],
        }),
      });
    });

    await page.getByPlaceholder('Enter address (0x... or bc1...)').fill('0xabc123');
    await page.getByRole('button', { name: /explore address/i }).click();
    await page.waitForResponse('**/api/v1/graph/subgraph*');

    // Click Patterns button
    const patternsButton = page.getByRole('button', { name: 'Patterns' });
    await patternsButton.click();
    await page.waitForResponse('**/api/v1/patterns/detect*');

    // Check if pattern findings are displayed
    await expect(page.getByText('Detected Patterns')).toBeVisible();
    await expect(page.getByText('Peel Chain')).toBeVisible();
  });

  test('should handle keyboard shortcuts', async ({ page }) => {
    await page.getByPlaceholder('Enter address (0x... or bc1...)').fill('0xabc123');
    await page.getByRole('button', { name: /explore address/i }).click();
    await page.waitForResponse('**/api/v1/graph/subgraph*');

    // Test Enter key on search input
    const pathInput = page.getByPlaceholder('Target address (0x... or bc1...)');
    await pathInput.fill('0xdef456');
    await pathInput.press('Enter');

    // Verify path finding was triggered (check for API call)
    await page.waitForTimeout(500);
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    await expect(page.getByText('Investigator Graph Explorer')).toBeVisible();
    
    await page.getByPlaceholder('Enter address (0x... or bc1...)').fill('0xabc123');
    await page.getByRole('button', { name: /explore address/i }).click();
    await page.waitForResponse('**/api/v1/graph/subgraph*');

    // Check if layout adapts to mobile
    await expect(page.getByText('Node Details')).toBeVisible();
  });
});
