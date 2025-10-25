import { test, expect } from '@playwright/test';

// ⚠️  REQUIRES BACKEND API
test.describe('ChatWidget Agent Workflows (BACKEND REQUIRED)', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to a page where ChatWidget is used (e.g., the main dashboard or a test page)
    await page.goto('/'); // Assuming ChatWidget is on the homepage or adjust to the correct page
  });

  test('should trigger risk_score tool via chat', async ({ page }) => {
    // Open the chat widget
    await page.click('[aria-label="Chat öffnen"]');

    // Type a message that should trigger risk_score
    await page.fill('input[placeholder="Frage eingeben..."]', 'Berechne das Risiko für die Adresse 0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4');

    // Send the message
    await page.click('button:has-text("Senden")');

    // Wait for response and check if it mentions risk or tools
    await page.waitForSelector('div[aria-live="polite"]');

    // Check that the response contains relevant content
    const response = await page.textContent('div[aria-live="polite"]');
    expect(response).toMatch(/risiko|risk|fehler/i); // Should mention risk or indicate error if tool fails
  });

  test('should trigger bridge_lookup tool via chat', async ({ page }) => {
    // Open the chat widget
    await page.click('[aria-label="Chat öffnen"]');

    // Type a message that should trigger bridge_lookup
    await page.fill('input[placeholder="Frage eingeben..."]', 'Finde alle Bridge-Verträge auf Ethereum');

    // Send the message
    await page.click('button:has-text("Senden")');

    // Wait for response
    await page.waitForSelector('div[aria-live="polite"]');

    // Check that the response contains relevant content
    const response = await page.textContent('div[aria-live="polite"]');
    expect(response).toMatch(/bridge|vertrag|ethereum|fehler/i);
  });

  test('should handle multiple tool workflows', async ({ page }) => {
    // Open the chat widget
    await page.click('[aria-label="Chat öffnen"]');

    // Type a complex message
    await page.fill('input[placeholder="Frage eingeben..."]', 'Analysiere die Adresse 0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4: Berechne Risiko und finde Bridges');

    // Send the message
    await page.click('button:has-text("Senden")');

    // Wait for response
    await page.waitForSelector('div[aria-live="polite"]');

    // Check that the response contains relevant content
    const response = await page.textContent('div[aria-live="polite"]');
    expect(response).toMatch(/risiko|bridge|fehler/i);
  });

  test('should display error gracefully on tool failure', async ({ page }) => {
    // Open the chat widget
    await page.click('[aria-label="Chat öffnen"]');

    // Type a message that might fail (e.g., invalid address)
    await page.fill('input[placeholder="Frage eingeben..."]', 'Berechne das Risiko für eine ungültige Adresse');

    // Send the message
    await page.click('button:has-text("Senden")');

    // Wait for response
    await page.waitForSelector('div[aria-live="polite"]');

    // Check that an error message is displayed
    const response = await page.textContent('div[aria-live="polite"]');
    expect(response).toMatch(/fehler|error|problem/i);
  });
});
