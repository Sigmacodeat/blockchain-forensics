import { test, expect } from '@playwright/test';
import { gotoDEAndReset, openBannerIfNeeded } from '../utils/consent';

test.describe('Cookie Preferences', () => {
  test('speichert aktivierte Analytics- und Marketing-Cookies', async ({ page }) => {
    await gotoDEAndReset(page);
    const banner = await openBannerIfNeeded(page);

    await banner.getByRole('button', { name: /einstellungen|preferences/i }).click();

    const analyticsToggle = banner.getByTestId('toggle-analytics');
    const marketingToggle = banner.getByTestId('toggle-marketing');

    await analyticsToggle.check({ force: true });
    await marketingToggle.check({ force: true });

    await banner.getByTestId('save-preferences').click();

    const consentStr = await page.evaluate(() => localStorage.getItem('cookie_consent'));
    expect(consentStr).toBeTruthy();
    const consent = JSON.parse(consentStr!);
    expect(consent.analytics).toBe(true);
    expect(consent.marketing).toBe(true);
    expect(consent.version).toBe(1);
  });
});
