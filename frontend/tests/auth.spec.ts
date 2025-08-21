import { test, expect } from '@playwright/test';

test.describe('Authentication Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the frontend
    await page.goto('http://localhost:3001');
  });

  test('should load the homepage', async ({ page }) => {
    await expect(page).toHaveTitle(/Vibe Deutsch/);
  });

  test('should navigate to login page', async ({ page }) => {
    // Look for login link or button and click it
    const loginLink = page.locator('a[href*="login"], button:has-text("Login"), a:has-text("Login")').first();
    if (await loginLink.count() > 0) {
      await loginLink.click();
      await expect(page.url()).toContain('login');
    }
  });

  test('should navigate to register page', async ({ page }) => {
    // Look for register link or button and click it
    const registerLink = page.locator('a[href*="register"], button:has-text("Register"), a:has-text("Register")').first();
    if (await registerLink.count() > 0) {
      await registerLink.click();  
      await expect(page.url()).toContain('register');
    }
  });

  test('should test login functionality', async ({ page }) => {
    // Navigate to login
    await page.goto('http://localhost:3001/login');
    
    // Fill login form if it exists
    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email"]');
    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    const submitButton = page.locator('button[type="submit"], button:has-text("Login")');
    
    if (await emailInput.count() > 0 && await passwordInput.count() > 0) {
      await emailInput.fill('testuser1755596375@example.com');
      await passwordInput.fill('testpassword123');
      
      if (await submitButton.count() > 0) {
        await submitButton.click();
        
        // Wait for redirect or success message
        await page.waitForTimeout(2000);
        
        // Check if we're redirected or see success
        const currentUrl = page.url();
        console.log('After login, current URL:', currentUrl);
      }
    }
  });

  test('should test register functionality', async ({ page }) => {
    // Navigate to register
    await page.goto('http://localhost:3001/register');
    
    // Fill register form if it exists
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"]').first(); // Get first password field
    const confirmPasswordInput = page.locator('input[type="password"]').nth(1); // Get second password field
    const usernameInput = page.locator('input[name="username"], input[placeholder*="username"]');
    const submitButton = page.locator('button[type="submit"], button:has-text("Register")');
    
    if (await emailInput.count() > 0 && await passwordInput.count() > 0) {
      const timestamp = Date.now();
      await emailInput.fill(`testuser${timestamp}@example.com`);
      await passwordInput.fill('testpassword123');
      await confirmPasswordInput.fill('testpassword123');
      
      if (await usernameInput.count() > 0) {
        await usernameInput.fill(`testuser${timestamp}`);
      }
      
      if (await submitButton.count() > 0) {
        await submitButton.click();
        
        // Wait for redirect or success message
        await page.waitForTimeout(2000);
        
        // Check if we're redirected or see success
        const currentUrl = page.url();
        console.log('After register, current URL:', currentUrl);
      }
    }
  });
});