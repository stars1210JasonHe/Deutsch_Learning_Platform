import { test, expect } from '@playwright/test';

test.describe('Login Debug Test', () => {
  test('should test login functionality step by step', async ({ page }) => {
    // Enable console logging
    page.on('console', msg => console.log('CONSOLE:', msg.text()));
    page.on('request', request => console.log('REQUEST:', request.method(), request.url()));
    page.on('response', response => console.log('RESPONSE:', response.status(), response.url()));

    // Go to login page
    console.log('1. Navigating to login page...');
    await page.goto('http://localhost:3002/login');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check if login form is visible
    console.log('2. Checking if login form is visible...');
    await expect(page.locator('h2')).toContainText('Login');
    
    // Fill in email
    console.log('3. Filling email field...');
    await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
    
    // Fill in password
    console.log('4. Filling password field...');
    await page.fill('input[type="password"]', '123456');
    
    // Take screenshot before login
    await page.screenshot({ path: 'tests/screenshots/before-login.png' });
    
    // Click login button
    console.log('5. Clicking login button...');
    await page.click('button[type="submit"]');
    
    // Wait for navigation or error message
    console.log('6. Waiting for login response...');
    
    try {
      // Wait for either successful navigation to home or error message
      await Promise.race([
        page.waitForURL('http://localhost:3002/', { timeout: 10000 }),
        page.waitForSelector('.text-red-600', { timeout: 10000 })
      ]);
      
      // Check current URL
      const currentUrl = page.url();
      console.log('7. Current URL after login attempt:', currentUrl);
      
      // Take screenshot after login attempt
      await page.screenshot({ path: 'tests/screenshots/after-login.png' });
      
      if (currentUrl === 'http://localhost:3002/') {
        console.log('✅ LOGIN SUCCESS - Redirected to home page');
        
        // Check if user info is displayed
        const userInfo = await page.textContent('body');
        console.log('8. Page content contains user info:', userInfo?.includes('heyeqiu1210@gmail.com'));
        
      } else {
        console.log('❌ LOGIN FAILED - Still on login page');
        
        // Check for error message
        const errorElement = page.locator('.text-red-600');
        if (await errorElement.isVisible()) {
          const errorText = await errorElement.textContent();
          console.log('9. Error message:', errorText);
        }
        
        // Check browser console for errors
        const logs = await page.evaluate(() => {
          return console.log.toString();
        });
        console.log('10. Browser console state:', logs);
      }
      
    } catch (error) {
      console.log('❌ LOGIN TIMEOUT - No response within 10 seconds');
      console.log('Error:', error);
      
      // Take screenshot of timeout state
      await page.screenshot({ path: 'tests/screenshots/login-timeout.png' });
    }
    
    // Check network requests in browser dev tools
    const networkLogs = await page.evaluate(() => {
      const performanceEntries = performance.getEntriesByType('navigation');
      return performanceEntries;
    });
    console.log('11. Network performance:', networkLogs);
    
    // Check localStorage
    const localStorage = await page.evaluate(() => {
      return Object.keys(localStorage).reduce((acc, key) => {
        acc[key] = localStorage.getItem(key);
        return acc;
      }, {} as Record<string, string | null>);
    });
    console.log('12. localStorage after login:', localStorage);
  });
  
  test('should test API directly from browser', async ({ page }) => {
    console.log('Testing API directly from browser...');
    
    await page.goto('http://localhost:3002');
    
    // Test API call directly
    const apiResult = await page.evaluate(async () => {
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
        
        const data = await response.json();
        
        return {
          status: response.status,
          ok: response.ok,
          data: data
        };
      } catch (error) {
        return {
          error: error.message
        };
      }
    });
    
    console.log('Direct API test result:', apiResult);
    
    if (apiResult.ok) {
      console.log('✅ Direct API call successful');
    } else {
      console.log('❌ Direct API call failed');
    }
  });
});