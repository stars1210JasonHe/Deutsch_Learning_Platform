import { test, expect } from '@playwright/test';

test.describe('Debug Äpfel Search Error', () => {
  test('should test Äpfel search and capture the exact error', async ({ page }) => {
    // Enable detailed logging
    page.on('console', msg => {
      console.log(`BROWSER CONSOLE [${msg.type()}]:`, msg.text());
    });
    
    page.on('request', request => {
      if (request.url().includes('translate/word')) {
        console.log(`→ REQUEST: ${request.method()} ${request.url()}`);
        console.log(`  Headers:`, request.headers());
        console.log(`  Body:`, request.postData());
      }
    });
    
    page.on('response', async response => {
      if (response.url().includes('translate/word')) {
        console.log(`← RESPONSE: ${response.status()} ${response.url()}`);
        try {
          const responseBody = await response.text();
          console.log(`  Response Body:`, responseBody);
        } catch (e) {
          console.log(`  Could not read response body:`, e);
        }
      }
    });
    
    // Navigate to login and login
    console.log('1. Logging in...');
    await page.goto('http://localhost:3002/login');
    await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
    await page.fill('input[type="password"]', '123456');
    await page.click('button[type="submit"]');
    
    // Wait for successful login
    await page.waitForURL('http://localhost:3002/', { timeout: 10000 });
    console.log('✅ Login successful');
    
    // Take screenshot before search
    await page.screenshot({ path: 'tests/screenshots/before-apfel-search.png' });
    
    // Find the search input
    console.log('2. Finding search input...');
    const searchInput = page.locator('input[type="text"]').first();
    await expect(searchInput).toBeVisible();
    
    // Type Äpfel
    console.log('3. Typing Äpfel...');
    await searchInput.fill('Äpfel');
    
    // Take screenshot showing the typed word
    await page.screenshot({ path: 'tests/screenshots/apfel-typed.png' });
    
    // Submit the search
    console.log('4. Submitting search...');
    await searchInput.press('Enter');
    
    // Wait for response (either success or error)
    console.log('5. Waiting for response...');
    await page.waitForTimeout(5000);
    
    // Take screenshot of result
    await page.screenshot({ path: 'tests/screenshots/apfel-result.png' });
    
    // Check for error message
    const errorMessage = page.locator('.text-red-600, .error, [class*="error"], .alert-error');
    if (await errorMessage.isVisible()) {
      const errorText = await errorMessage.textContent();
      console.log('❌ ERROR FOUND:', errorText);
      
      // Take screenshot of error
      await page.screenshot({ path: 'tests/screenshots/apfel-error-state.png' });
    } else {
      console.log('✅ No visible error message found');
    }
    
    // Check if any results appeared
    const results = page.locator('[class*="result"], .word-result, .search-result');
    const resultCount = await results.count();
    console.log(`Found ${resultCount} result elements`);
    
    if (resultCount > 0) {
      console.log('✅ Search results appeared');
      for (let i = 0; i < Math.min(resultCount, 3); i++) {
        const resultText = await results.nth(i).textContent();
        console.log(`  Result ${i + 1}:`, resultText?.substring(0, 100));
      }
    } else {
      console.log('❌ No search results found');
    }
    
    // Check the page content for any clues
    const pageContent = await page.textContent('body');
    if (pageContent?.includes('Äpfel')) {
      console.log('✅ Äpfel appears in page content');
    } else {
      console.log('❌ Äpfel does not appear in page content');
    }
    
    if (pageContent?.includes('Internal server error')) {
      console.log('❌ Internal server error found in page');
    }
    
    if (pageContent?.includes('error')) {
      console.log('⚠️ Some error text found in page');
    }
  });
  
  test('should test different German words with special characters', async ({ page }) => {
    console.log('Testing multiple German words with umlauts...');
    
    // Login first
    await page.goto('http://localhost:3002/login');
    await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
    await page.fill('input[type="password"]', '123456');
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:3002/', { timeout: 10000 });
    
    const testWords = ['Äpfel', 'Apfel', 'Schön', 'Größe', 'Mädchen', 'Jäger'];
    
    for (const word of testWords) {
      console.log(`\n--- Testing word: ${word} ---`);
      
      const searchInput = page.locator('input[type="text"]').first();
      
      // Clear and type the word
      await searchInput.fill('');
      await searchInput.fill(word);
      await searchInput.press('Enter');
      
      // Wait for response
      await page.waitForTimeout(3000);
      
      // Check for errors
      const errorVisible = await page.locator('.text-red-600, [class*="error"]').isVisible();
      const hasResults = await page.locator('[class*="result"]').count() > 0;
      
      console.log(`  ${word}: Error=${errorVisible}, HasResults=${hasResults}`);
      
      if (errorVisible) {
        const errorText = await page.locator('.text-red-600, [class*="error"]').first().textContent();
        console.log(`    Error: ${errorText}`);
      }
      
      // Take screenshot for each word
      await page.screenshot({ path: `tests/screenshots/test-${word.replace(/[^a-zA-Z0-9]/g, '_')}.png` });
    }
  });
});