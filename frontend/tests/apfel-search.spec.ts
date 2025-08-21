import { test, expect } from '@playwright/test';

test.describe('Äpfel search functionality', () => {
  test('should handle German umlaut Ä in search', async ({ page }) => {
    // Go to the home page
    await page.goto('/');
    
    // Wait for page to load
    await expect(page.getByText('Welcome to the Universe')).toBeVisible();
    
    // Check if user is logged in, if not, try to login first
    const loginButton = page.getByText('Login');
    if (await loginButton.isVisible()) {
      await loginButton.click();
      
      // Fill in login form (you may need to adjust these selectors)
      await page.fill('[type="email"]', 'test@example.com');
      await page.fill('[type="password"]', 'password');
      await page.click('button[type="submit"]');
      
      // Wait for redirect back to home
      await page.waitForURL('/');
    }
    
    // Find the search input field
    const searchInput = page.locator('input[placeholder*="Äpfel"], input[placeholder*="word"], input[type="text"]').first();
    await expect(searchInput).toBeVisible();
    
    // Type "Äpfel" in the search field
    await searchInput.fill('Äpfel');
    
    // Click the launch/search button
    const launchButton = page.getByText('Launch').or(page.getByRole('button', { name: /launch|search/i }));
    await launchButton.click();
    
    // Wait for search results or error
    await page.waitForTimeout(3000);
    
    // Check if we get a valid result instead of "Internal server error"
    const errorMessage = page.getByText('Internal server error');
    const notFoundMessage = page.getByText('Not Found');
    
    // Take a screenshot for debugging
    await page.screenshot({ path: 'tests/screenshots/apfel-search-result.png' });
    
    // The test should either find the word or show proper "not found", not an internal error
    const hasError = await errorMessage.isVisible();
    const hasNotFound = await notFoundMessage.isVisible();
    
    if (hasError) {
      throw new Error('Internal server error occurred during Äpfel search - character encoding issue');
    }
    
    // Log what we found
    const pageContent = await page.textContent('body');
    console.log('Page content after search:', pageContent?.substring(0, 500));
    
    // If we get here without error, the character encoding is working
    expect(hasError).toBeFalsy();
  });
  
  test('should handle regular Apfel search as comparison', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to load
    await expect(page.getByText('Welcome to the Universe')).toBeVisible();
    
    // Find the search input field
    const searchInput = page.locator('input[placeholder*="Äpfel"], input[placeholder*="word"], input[type="text"]').first();
    await expect(searchInput).toBeVisible();
    
    // Type "Apfel" (without umlaut) in the search field  
    await searchInput.fill('Apfel');
    
    // Click the launch/search button
    const launchButton = page.getByText('Launch').or(page.getByRole('button', { name: /launch|search/i }));
    await launchButton.click();
    
    // Wait for search results
    await page.waitForTimeout(3000);
    
    // Take a screenshot for comparison
    await page.screenshot({ path: 'tests/screenshots/apfel-regular-search.png' });
    
    // Check that we don't get internal server error
    const errorMessage = page.getByText('Internal server error');
    expect(await errorMessage.isVisible()).toBeFalsy();
  });
});