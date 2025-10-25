/**
 * Tracing Workflow E2E Tests
 * Tests transaction tracing with plan-based depth limits
 */
import { test, expect } from '@playwright/test';

// ⚠️  REQUIRES BACKEND + AUTH
test.describe('Transaction Tracing - Community Plan (AUTH REQUIRED)', () => {
  test.beforeEach(async ({ page }) => {
    // Login as Community user
    await page.goto('/login');
    await page.fill('input[name="email"]', 'community@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should access tracing page', async ({ page }) => {
    await page.goto('/trace');
    
    // Should display trace form
    await expect(page.locator('input[name="address"]')).toBeVisible();
    await expect(page.locator('select[name="chain"]')).toBeVisible();
    await expect(page.locator('input[name="depth"]')).toBeVisible();
  });

  test('should trace with depth 2 (Community limit)', async ({ page }) => {
    await page.goto('/trace');
    
    // Fill trace form
    await page.fill('input[name="address"]', '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
    await page.selectOption('select[name="chain"]', 'ethereum');
    await page.fill('input[name="depth"]', '2');
    
    // Submit trace
    await page.click('button:has-text("Start Trace")');
    
    // Should show loading state
    await expect(page.locator('text=/tracing/i')).toBeVisible();
    
    // Should display results
    await expect(page.locator('[data-testid="trace-results"]')).toBeVisible({ timeout: 15000 });
    
    // Should show depth 2 results
    await expect(page.locator('text=/depth.*2/i')).toBeVisible();
  });

  test('should block depth > 2 for Community users', async ({ page }) => {
    await page.goto('/trace');
    
    await page.fill('input[name="address"]', '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
    await page.fill('input[name="depth"]', '5');
    
    await page.click('button:has-text("Start Trace")');
    
    // Should show upgrade prompt
    await expect(page.locator('text=/upgrade.*pro/i')).toBeVisible();
    
    // Should NOT execute trace
    await expect(page.locator('[data-testid="trace-results"]')).not.toBeVisible();
  });

  test('should show upgrade CTA when reaching limit', async ({ page }) => {
    await page.goto('/trace');
    
    // Try to set depth 5
    await page.fill('input[name="depth"]', '5');
    
    // Should show tooltip/warning
    await expect(page.locator('text=/pro.*required/i')).toBeVisible();
    
    // Should display "Upgrade" button
    await expect(page.locator('button:has-text("Upgrade")')).toBeVisible();
  });
});

test.describe('Transaction Tracing - Pro Plan (AUTH REQUIRED)', () => {
  test.beforeEach(async ({ page }) => {
    // Login as Pro user
    await page.goto('/login');
    await page.fill('input[name="email"]', 'pro@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should trace with depth 5 (Pro limit)', async ({ page }) => {
    await page.goto('/trace');
    
    // Fill trace form with depth 5
    await page.fill('input[name="address"]', '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
    await page.selectOption('select[name="chain"]', 'ethereum');
    await page.fill('input[name="depth"]', '5');
    
    await page.click('button:has-text("Start Trace")');
    
    // Should execute successfully
    await expect(page.locator('[data-testid="trace-results"]')).toBeVisible({ timeout: 15000 });
    
    // Should show depth 5 results
    await expect(page.locator('text=/depth.*5/i')).toBeVisible();
  });

  test('should allow forward and backward tracing', async ({ page }) => {
    await page.goto('/trace');
    
    await page.fill('input[name="address"]', '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
    
    // Select bidirectional tracing
    await page.selectOption('select[name="direction"]', 'bidirectional');
    
    await page.click('button:has-text("Start Trace")');
    
    // Should show both incoming and outgoing transactions
    await expect(page.locator('text=/incoming/i')).toBeVisible();
    await expect(page.locator('text=/outgoing/i')).toBeVisible();
  });

  test('should export trace results', async ({ page }) => {
    await page.goto('/trace');
    
    // Execute trace
    await page.fill('input[name="address"]', '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
    await page.click('button:has-text("Start Trace")');
    
    await expect(page.locator('[data-testid="trace-results"]')).toBeVisible({ timeout: 15000 });
    
    // Click export button
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export")');
    
    const download = await downloadPromise;
    
    // Should download JSON file
    expect(download.suggestedFilename()).toMatch(/trace.*\.json/i);
  });

  test('should visualize trace graph', async ({ page }) => {
    await page.goto('/trace');
    
    await page.fill('input[name="address"]', '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
    await page.click('button:has-text("Start Trace")');
    
    await expect(page.locator('[data-testid="trace-results"]')).toBeVisible({ timeout: 15000 });
    
    // Switch to graph view
    await page.click('button:has-text("Graph View")');
    
    // Should display graph visualization
    await expect(page.locator('[data-testid="trace-graph"]')).toBeVisible();
    
    // Should have nodes and edges
    await expect(page.locator('[data-node]')).toHaveCount(3, { timeout: 5000 }); // At least 3 nodes
  });
});

test.describe('Trace Results & Analysis (AUTH REQUIRED)', () => {
  test('should display risk scores in results', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'pro@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await page.goto('/trace');
    await page.fill('input[name="address"]', '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
    await page.click('button:has-text("Start Trace")');
    
    await expect(page.locator('[data-testid="trace-results"]')).toBeVisible({ timeout: 15000 });
    
    // Should display risk scores
    await expect(page.locator('text=/risk.*score/i')).toBeVisible();
    await expect(page.locator('[data-testid="risk-indicator"]')).toBeVisible();
  });

  test('should highlight sanctioned addresses', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'pro@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await page.goto('/trace');
    await page.fill('input[name="address"]', '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
    await page.click('button:has-text("Start Trace")');
    
    await expect(page.locator('[data-testid="trace-results"]')).toBeVisible({ timeout: 15000 });
    
    // If sanctioned addresses found, should highlight them
    const sanctionedIndicator = page.locator('[data-risk="sanctioned"]');
    if (await sanctionedIndicator.isVisible()) {
      await expect(sanctionedIndicator).toHaveClass(/.*red.*/i); // Red highlight
    }
  });

  test('should create case from trace results', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'pro@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await page.goto('/trace');
    await page.fill('input[name="address"]', '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
    await page.click('button:has-text("Start Trace")');
    
    await expect(page.locator('[data-testid="trace-results"]')).toBeVisible({ timeout: 15000 });
    
    // Click "Create Case" button
    await page.click('button:has-text("Create Case")');
    
    // Should show case creation modal
    await expect(page.locator('[data-testid="case-modal"]')).toBeVisible();
    
    // Fill case details
    await page.fill('input[name="caseTitle"]', 'Suspicious Activity Investigation');
    await page.fill('textarea[name="caseDescription"]', 'Trace revealed suspicious patterns');
    
    await page.click('button[type="submit"]:has-text("Create")');
    
    // Should create case and redirect
    await expect(page.locator('text=/case.*created/i')).toBeVisible();
  });
});
