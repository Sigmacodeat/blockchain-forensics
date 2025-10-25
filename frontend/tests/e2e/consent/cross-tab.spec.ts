import { test, expect } from '@playwright/test';
import { gotoDEAndReset, openBannerIfNeeded } from '../utils/consent';

test.describe('Cookie Consent Cross-Tab', () => {
  test('synchronisiert Änderungen via Storage-Event zwischen Tabs', async ({ browser }) => {
    const ctx = await browser.newContext();
    const pageA = await ctx.newPage();
    const pageB = await ctx.newPage();

    await gotoDEAndReset(pageA);
    await gotoDEAndReset(pageB);

    const bannerA = await openBannerIfNeeded(pageA);
    await openBannerIfNeeded(pageB);

    // Öffne Präferenzen und aktiviere Analytics-Cookies in Tab A
    await bannerA.getByRole('button', { name: /einstellungen|preferences/i }).click();
    await bannerA.getByTestId('toggle-analytics').check({ force: true });

    const storageEventSeen = pageB.evaluate(() =>
      new Promise<boolean>((resolve, reject) => {
        const timeout = setTimeout(() => {
          window.removeEventListener('storage', handler);
          reject(new Error('storage event timeout'));
        }, 2_000);

        const handler = (event: StorageEvent) => {
          if (event.key === 'cookie_consent') {
            clearTimeout(timeout);
            window.removeEventListener('storage', handler);
            resolve(true);
          }
        };

        window.addEventListener('storage', handler);
      })
    );

    await bannerA.getByTestId('save-preferences').click();

    await expect(storageEventSeen).resolves.toBeTruthy();

    const consentB = await pageB.evaluate(() => localStorage.getItem('cookie_consent'));
    expect(consentB).toBeTruthy();
    const parsed = JSON.parse(consentB!);
    expect(parsed.version).toBe(1);
    expect(parsed.analytics).toBe(true);

    await ctx.close();
  });
});
