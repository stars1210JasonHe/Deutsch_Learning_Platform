import { test, expect } from '@playwright/test';

test.describe('Check Login State', () => {
  test('should check current login state and CORS issues', async ({ page }) => {
    // Enable request/response logging
    page.on('console', msg => console.log('BROWSER:', msg.text()));
    page.on('request', request => console.log('→', request.method(), request.url()));
    page.on('response', response => {
      const status = response.status();
      const statusIcon = status >= 200 && status < 300 ? '✅' : '❌';
      console.log('←', statusIcon, status, response.url());
    });
    
    console.log('=== Checking Login State ===');
    
    // Step 1: Go to login page
    console.log('1. Loading login page...');
    await page.goto('http://localhost:3002/login');
    
    // Step 2: Take screenshot of login page
    await page.screenshot({ path: 'tests/screenshots/01-login-page.png' });
    
    // Step 3: Fill form but don't submit yet
    console.log('2. Filling form...');
    await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
    await page.fill('input[type="password"]', '123456');
    await page.screenshot({ path: 'tests/screenshots/02-form-filled.png' });
    
    // Step 4: Test API directly from browser console
    console.log('3. Testing API directly...');
    const apiTest = await page.evaluate(async () => {
      try {
        const response = await fetch('http://localhost:8000/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: 'heyeqiu1210@gmail.com',
            password: '123456',
            remember_me: false
          })
        });
        
        return {
          success: response.ok,
          status: response.status,
          data: response.ok ? await response.json() : await response.text()
        };
      } catch (error) {
        return {
          success: false,
          error: error.message
        };
      }
    });
    
    console.log('API Test Result:', apiTest);
    
    if (apiTest.success) {
      console.log('✅ API call successful - CORS is working!');
      
      // Step 5: Now try the actual form submission
      console.log('4. Submitting form...');
      await page.click('button[type="submit"]');
      
      // Wait a bit to see what happens
      await page.waitForTimeout(5000);
      
      const currentUrl = page.url();
      console.log('Current URL after submit:', currentUrl);
      
      if (currentUrl === 'http://localhost:3002/') {
        console.log('✅ LOGIN SUCCESS!');
        await page.screenshot({ path: 'tests/screenshots/03-login-success.png' });
        
        // Test a search
        console.log('5. Testing search...');
        const searchInput = page.locator('input[type="text"]').first();
        if (await searchInput.isVisible()) {
          await searchInput.fill('Kfz');
          await searchInput.press('Enter');
          await page.waitForTimeout(3000);
          await page.screenshot({ path: 'tests/screenshots/04-search-results.png' });
          console.log('✅ Search test completed');
        }
        
      } else {
        console.log('❌ LOGIN FAILED - Still on login page');
        await page.screenshot({ path: 'tests/screenshots/03-login-failed.png' });
        
        // Check for error messages
        const errorMsg = await page.textContent('.text-red-600, .error, [class*="error"]');
        if (errorMsg) {
          console.log('Error message:', errorMsg);
        }
      }
      
    } else {
      console.log('❌ API call failed - CORS issue still exists');
      console.log('Error:', apiTest.error);
      
      console.log('\n📝 To fix this:');
      console.log('1. Make sure backend server is running on port 8000');
      console.log('2. Restart the backend server to apply CORS fix');
      console.log('3. Backend should allow http://localhost:3002');
    }
    
    // Final state screenshot
    await page.screenshot({ path: 'tests/screenshots/05-final-state.png' });
  });
});