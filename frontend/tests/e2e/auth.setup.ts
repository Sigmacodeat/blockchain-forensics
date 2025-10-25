/**
 * Authentication Setup für Playwright E2E Tests
 * Erstellt authentifizierte Sessions für verschiedene User-Rollen
 */
import { test as setup, expect } from '@playwright/test';
import path from 'path';

const authDir = path.join(__dirname, '../../.auth');

// Community User Setup
setup('authenticate as community user', async ({ page }) => {
  // TODO: Backend muss laufen für echte Auth
  // Für jetzt: Skip oder Mock
  console.log('⚠️  Auth setup skipped - Backend required');
});

// Pro User Setup
setup('authenticate as pro user', async ({ page }) => {
  console.log('⚠️  Auth setup skipped - Backend required');
});

// Admin User Setup
setup('authenticate as admin user', async ({ page }) => {
  console.log('⚠️  Auth setup skipped - Backend required');
});

/**
 * Mock Auth Helper für Tests ohne Backend
 * Setzt Session-Storage direkt
 */
export async function mockAuth(
  page: any,
  role: 'community' | 'pro' | 'plus' | 'admin'
) {
  await page.addInitScript((role: string) => {
    const mockUser = {
      community: {
        id: '1',
        email: 'community@example.com',
        name: 'Community User',
        plan: 'community',
        role: 'user',
      },
      pro: {
        id: '2',
        email: 'pro@example.com',
        name: 'Pro User',
        plan: 'pro',
        role: 'user',
      },
      plus: {
        id: '3',
        email: 'plus@example.com',
        name: 'Plus User',
        plan: 'plus',
        role: 'user',
      },
      admin: {
        id: '99',
        email: 'admin@example.com',
        name: 'Admin User',
        plan: 'enterprise',
        role: 'admin',
      },
    };

    const user = mockUser[role as keyof typeof mockUser];
    
    // Mock Session Storage
    sessionStorage.setItem('user', JSON.stringify(user));
    sessionStorage.setItem('token', 'mock-jwt-token');
    
    // Mock Local Storage für Consent
    localStorage.setItem('cookieConsent', JSON.stringify({
      necessary: true,
      analytics: true,
      marketing: false,
    }));
  }, role);
}
