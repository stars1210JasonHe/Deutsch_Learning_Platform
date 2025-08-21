import { test, expect } from '@playwright/test';

test('Simple Äpfel character encoding test', async ({ page }) => {
  // Go to the home page
  await page.goto('/');
  
  // Wait for page to load
  await expect(page.getByText('Welcome to the Universe')).toBeVisible();
  
  // Find the search input field (there should be one in the main interface)
  const searchInput = page.locator('input[type="text"]').first();
  await expect(searchInput).toBeVisible();
  
  // Type "Äpfel" in the search field
  await searchInput.fill('Äpfel');
  
  // Take a screenshot before clicking
  await page.screenshot({ path: 'tests/screenshots/before-search.png' });
  
  // Click the launch button (the button, not the label)
  const launchButton = page.getByRole('button', { name: /Launch/ });
  await launchButton.click();
  
  // Wait a bit for the request to process
  await page.waitForTimeout(5000);
  
  // Take a screenshot after the search attempt
  await page.screenshot({ path: 'tests/screenshots/after-search.png' });
  
  // Check for various possible outcomes
  const internalError = page.getByText('Internal server error');
  const notFound = page.getByText('Not Found');
  const notAuthenticated = page.getByText('Not authenticated');
  const loginMessage = page.getByText('Please login to use search features');
  
  // Print what we found
  const hasInternalError = await internalError.isVisible();
  const hasNotFound = await notFound.isVisible();
  const hasNotAuth = await notAuthenticated.isVisible();
  const hasLoginMsg = await loginMessage.isVisible();
  
  console.log('Test Results:');
  console.log(`- Internal Error: ${hasInternalError}`);
  console.log(`- Not Found: ${hasNotFound}`);
  console.log(`- Not Authenticated: ${hasNotAuth}`);
  console.log(`- Login Message: ${hasLoginMsg}`);
  
  // Get the page content for debugging
  const bodyText = await page.textContent('body');
  console.log('Page content (first 500 chars):', bodyText?.substring(0, 500));
  
  // The main test: we should NOT get an "Internal server error" 
  // We might get "Not authenticated" or other messages, but not internal error
  if (hasInternalError) {
    throw new Error('Got Internal server error - character encoding issue still exists');
  }
  
  console.log('✅ No internal server error detected');
});