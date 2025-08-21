import { test, expect } from '@playwright/test';

test.describe('User Login Flow', () => {
  test('should login with heyeqiu1210@gmail.com and test full workflow', async ({ page }) => {
    // Step 1: Navigate to login page
    console.log('1. Navigating to login page...');
    await page.goto('http://localhost:3002/login');
    
    // Step 2: Verify login page loaded correctly
    await expect(page).toHaveTitle(/Vibe Deutsch/);
    await expect(page.locator('h2')).toContainText('Login');
    
    // Step 3: Fill login form with your credentials
    console.log('2. Filling login form...');
    await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
    await page.fill('input[type="password"]', '123456');
    
    // Step 4: Submit login form
    console.log('3. Submitting login...');
    await page.click('button[type="submit"]');
    
    // Step 5: Wait for successful login and redirect to home
    console.log('4. Waiting for login success...');
    await page.waitForURL('http://localhost:3002/', { timeout: 10000 });
    console.log('✅ Login successful - redirected to home page');
    
    // Step 6: Verify we're logged in by checking the page content
    await expect(page.locator('body')).toBeVisible();
    
    // Step 7: Test search functionality
    console.log('5. Testing search functionality...');
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('Kfz');
    await searchInput.press('Enter');
    
    // Wait for search results
    await page.waitForTimeout(2000);
    console.log('6. Search completed for "Kfz"');
    
    // Step 8: Test one of our newly imported nouns
    console.log('7. Testing newly imported noun "WG"...');
    await searchInput.fill('WG');
    await searchInput.press('Enter');
    
    // Wait for search results
    await page.waitForTimeout(2000);
    
    // Check if word result is displayed
    const wordResult = page.locator('.word-result, .enhanced-word-result, [class*="result"]').first();
    if (await wordResult.isVisible()) {
      console.log('✅ Search results displayed for WG');
      
      // Take screenshot of results
      await page.screenshot({ path: 'tests/screenshots/wg-search-results.png' });
    } else {
      console.log('ℹ️ No specific word result found, checking for any content...');
      await page.screenshot({ path: 'tests/screenshots/wg-search-general.png' });
    }
    
    // Step 9: Test another newly imported noun
    console.log('8. Testing "Lkw"...');
    await searchInput.fill('Lkw');
    await searchInput.press('Enter');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'tests/screenshots/lkw-search.png' });
    
    // Step 10: Test navigation to different sections
    console.log('9. Testing navigation...');
    
    // Try to find and click favorites if available
    const favoritesLink = page.locator('a[href*="favorites"], button:has-text("Favorites")').first();
    if (await favoritesLink.isVisible()) {
      await favoritesLink.click();
      await page.waitForTimeout(1000);
      console.log('✅ Navigated to favorites');
    }
    
    // Try to find and click search history if available
    const historyLink = page.locator('a[href*="history"], button:has-text("History")').first();
    if (await historyLink.isVisible()) {
      await historyLink.click();
      await page.waitForTimeout(1000);
      console.log('✅ Navigated to history');
    }
    
    // Step 11: Test logout functionality
    console.log('10. Testing logout...');
    const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")').first();
    if (await logoutButton.isVisible()) {
      await logoutButton.click();
      await page.waitForURL('http://localhost:3002/login', { timeout: 5000 });
      console.log('✅ Logout successful');
    } else {
      console.log('ℹ️ Logout button not found, checking for other auth indicators...');
    }
    
    // Final screenshot
    await page.screenshot({ path: 'tests/screenshots/final-state.png' });
    
    console.log('🎉 Complete user flow test finished!');
  });
  
  test('should test multiple noun searches from our Excel import', async ({ page }) => {
    // Login first
    await page.goto('http://localhost:3002/login');
    await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
    await page.fill('input[type="password"]', '123456');
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:3002/', { timeout: 10000 });
    
    // Test all our newly imported nouns
    const testWords = ['Kfz', 'EG', 'Lkw', 'WG'];
    
    for (const word of testWords) {
      console.log(`Testing search for: ${word}`);
      
      const searchInput = page.locator('input[type="text"]').first();
      await searchInput.fill(word);
      await searchInput.press('Enter');
      
      // Wait for results
      await page.waitForTimeout(3000);
      
      // Take screenshot
      await page.screenshot({ path: `tests/screenshots/search-${word.toLowerCase()}.png` });
      
      // Check for any content on page
      const pageContent = await page.textContent('body');
      if (pageContent?.includes(word)) {
        console.log(`✅ Found "${word}" in search results`);
      } else {
        console.log(`ℹ️ "${word}" not found in visible content`);
      }
    }
  });
  
  test('should test German word with multiple POS (if available)', async ({ page }) => {
    // Login
    await page.goto('http://localhost:3002/login');
    await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
    await page.fill('input[type="password"]', '123456');
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:3002/', { timeout: 10000 });
    
    // Test our multiple choice functionality with "essen" or "leben"
    console.log('Testing multiple choice functionality...');
    
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('essen');
    await searchInput.press('Enter');
    
    // Wait for results
    await page.waitForTimeout(3000);
    
    // Check if multiple choice selector appears
    const multipleChoice = page.locator('.multiple-choice-container, .choices-list, [class*="choice"]');
    if (await multipleChoice.isVisible()) {
      console.log('✅ Multiple choice interface detected!');
      await page.screenshot({ path: 'tests/screenshots/multiple-choice-essen.png' });
      
      // Try clicking the first choice
      const firstChoice = page.locator('.choice-item, [class*="choice"]:first-child').first();
      if (await firstChoice.isVisible()) {
        await firstChoice.click();
        await page.waitForTimeout(2000);
        console.log('✅ Selected first choice');
        await page.screenshot({ path: 'tests/screenshots/after-choice-selection.png' });
      }
    } else {
      console.log('ℹ️ No multiple choice interface found');
      await page.screenshot({ path: 'tests/screenshots/essen-single-result.png' });
    }
  });
});