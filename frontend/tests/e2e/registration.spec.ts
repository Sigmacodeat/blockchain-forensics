/**
 * Registration Flow E2E Tests
 * 
 * ⚠️  REQUIRES BACKEND + DATABASE
 * Diese Tests sind deaktiviert bis Backend läuft
 */
import { test, expect } from '@playwright/test';

test.describe('User Registration Flow (BACKEND REQUIRED)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display registration page', async ({ page }) => {
    // Click "Sign Up" or "Get Started" button
    await page.click('text=Get Started');
    
    // Should navigate to registration page
    await expect(page).toHaveURL(/\/register/);
    
    // Should display registration form
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('input[name="username"]')).toBeVisible();
  });

  test('should register new user with Community plan', async ({ page }) => {
    await page.goto('/register');
    
    // Fill registration form
    const timestamp = Date.now();
    const testEmail = `test+${timestamp}@example.com`;
    const testUsername = `testuser_${timestamp}`;
    
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="username"]', testUsername);
    await page.fill('input[name="password"]', 'SecureP@ssw0rd123');
    await page.fill('input[name="confirmPassword"]', 'SecureP@ssw0rd123');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
    
    // Should show welcome message
    await expect(page.locator('text=Welcome')).toBeVisible();
    
    // Should display Community plan badge
    await expect(page.locator('text=Community')).toBeVisible();
  });

  test('should auto-login after registration', async ({ page }) => {
    await page.goto('/register');
    
    // Register
    const timestamp = Date.now();
    await page.fill('input[name="email"]', `test+${timestamp}@example.com`);
    await page.fill('input[name="username"]', `user_${timestamp}`);
    await page.fill('input[name="password"]', 'Test123!@#');
    await page.fill('input[name="confirmPassword"]', 'Test123!@#');
    
    await page.click('button[type="submit"]');
    
    // Wait for dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
    
    // Should NOT show login form
    await expect(page.locator('text=Login')).not.toBeVisible();
    
    // Should show user menu
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should show validation errors for invalid input', async ({ page }) => {
    await page.goto('/register');
    
    // Try to submit with invalid email
    await page.fill('input[name="email"]', 'invalid-email');
    await page.fill('input[name="username"]', 'user');
    await page.fill('input[name="password"]', 'short');
    
    await page.click('button[type="submit"]');
    
    // Should display validation errors
    await expect(page.locator('text=/invalid email/i')).toBeVisible();
    await expect(page.locator('text=/password.*too short/i')).toBeVisible();
  });

  test('should prevent duplicate email registration', async ({ page }) => {
    await page.goto('/register');
    
    // Use existing email
    await page.fill('input[name="email"]', 'existing@example.com');
    await page.fill('input[name="username"]', 'newuser');
    await page.fill('input[name="password"]', 'SecureP@ssw0rd123');
    await page.fill('input[name="confirmPassword"]', 'SecureP@ssw0rd123');
    
    await page.click('button[type="submit"]');
    
    // Should show error message
    await expect(page.locator('text=/email.*already.*exists/i')).toBeVisible();
  });
});

test.describe('Login Flow (BACKEND REQUIRED)', () => {
  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Fill login form
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
    
    // Should show user info
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[name="email"]', 'wrong@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    
    await page.click('button[type="submit"]');
    
    // Should show error
    await expect(page.locator('text=/invalid.*credentials/i')).toBeVisible();
    
    // Should stay on login page
    await expect(page).toHaveURL(/\/login/);
  });

  test('should persist session after page reload', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Reload page
    await page.reload();
    
    // Should still be logged in
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });
});
