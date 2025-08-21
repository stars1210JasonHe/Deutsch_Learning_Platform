import { test, expect } from '@playwright/test';

test.describe('Full Äpfel search test with authentication', () => {
  test('should login and test Äpfel search thoroughly', async ({ page }) => {
    // Step 1: Go to home page
    console.log('Step 1: Loading home page...');
    await page.goto('/');
    await expect(page.getByText('Welcome to the Universe')).toBeVisible();
    console.log('✅ Home page loaded');

    // Step 2: Navigate to login page
    console.log('Step 2: Going to login page...');
    await page.click('a[href="/login"]');
    await page.waitForURL('/login');
    console.log('✅ Login page loaded');

    // Step 3: Login with test credentials
    console.log('Step 3: Attempting login...');
    await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
    await page.fill('input[type="password"]', '123456');
    
    // Listen for network requests to see what happens
    page.on('response', response => {
      if (response.url().includes('/auth/login')) {
        console.log(`Login response: ${response.status()} ${response.statusText()}`);
      }
      if (response.url().includes('/translate/word')) {
        console.log(`Word search response: ${response.status()} ${response.statusText()}`);
        response.text().then(body => {
          console.log(`Response body: ${body.substring(0, 200)}...`);
        }).catch(() => {});
      }
    });

    await page.click('button[type="submit"]');
    
    // Wait a bit and check what happened
    await page.waitForTimeout(3000);
    
    // Check if we're still on login page (failed login) or moved (successful login)
    const currentUrl = page.url();
    console.log(`Current URL after login attempt: ${currentUrl}`);
    
    if (currentUrl.includes('/login')) {
      console.log('⚠️ Still on login page, trying to register instead...');
      
      // Try to register a new account
      await page.click('a[href="/register"]');
      await page.waitForURL('/register');
      
      await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
      await page.fill('input[type="password"]', '123456');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(3000);
      
      // Check if registration worked
      if (page.url().includes('/register')) {
        console.log('⚠️ Registration also failed, proceeding without auth to test the error...');
        await page.goto('/');
      } else {
        console.log('✅ Registration successful');
      }
    } else {
      console.log('✅ Login successful');
    }

    // Step 4: Now test the Äpfel search
    console.log('Step 4: Testing Äpfel search...');
    
    // Make sure we're on home page
    await page.goto('/');
    await expect(page.getByText('Welcome to the Universe')).toBeVisible();
    
    // Find the search input
    const searchInput = page.locator('input[type="text"]').first();
    await expect(searchInput).toBeVisible();
    
    console.log('Step 5: Entering "Äpfel" in search...');
    await searchInput.fill('Äpfel');
    
    // Take screenshot before search
    await page.screenshot({ path: 'tests/screenshots/before-apfel-search.png' });
    
    // Click launch button
    console.log('Step 6: Clicking launch button...');
    const launchButton = page.getByRole('button', { name: /Launch/ });
    await launchButton.click();
    
    // Wait for response and capture what happens
    console.log('Step 7: Waiting for search response...');
    await page.waitForTimeout(5000);
    
    // Take screenshot after search
    await page.screenshot({ path: 'tests/screenshots/after-apfel-search.png' });
    
    // Check all possible error messages
    const internalError = page.getByText('Internal server error');
    const notFound = page.getByText('Not Found');
    const authError = page.getByText('Not authenticated');
    const loginMsg = page.getByText('Please login');
    
    const hasInternalError = await internalError.isVisible();
    const hasNotFound = await notFound.isVisible();
    const hasAuthError = await authError.isVisible();
    const hasLoginMsg = await loginMsg.isVisible();
    
    console.log('\n=== SEARCH RESULTS ===');
    console.log(`Internal Error: ${hasInternalError}`);
    console.log(`Not Found: ${hasNotFound}`);
    console.log(`Auth Error: ${hasAuthError}`);
    console.log(`Login Message: ${hasLoginMsg}`);
    
    // Get full page content for analysis
    const bodyText = await page.textContent('body');
    console.log('\n=== FULL PAGE CONTENT ===');
    console.log(bodyText?.substring(0, 1000));
    
    // Check network tab for failed requests
    const errors = await page.evaluate(() => {
      const entries = performance.getEntriesByType('navigation');
      return entries.map(entry => ({
        name: entry.name,
        status: (entry as any).responseStatus
      }));
    });
    console.log('\n=== NETWORK ENTRIES ===');
    console.log(errors);
    
    // The main assertion: if we get Internal Server Error, the bug still exists
    if (hasInternalError) {
      throw new Error('❌ ÄPFEL SEARCH STILL BROKEN: Internal server error detected');
    }
    
    console.log('✅ Test completed - no internal server error detected');
  });
  
  test('should test regular Apfel search for comparison', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Welcome to the Universe')).toBeVisible();
    
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('Apfel');
    
    const launchButton = page.getByRole('button', { name: /Launch/ });
    await launchButton.click();
    
    await page.waitForTimeout(5000);
    await page.screenshot({ path: 'tests/screenshots/regular-apfel-search.png' });
    
    const internalError = page.getByText('Internal server error');
    const hasInternalError = await internalError.isVisible();
    
    console.log(`Regular "Apfel" search - Internal Error: ${hasInternalError}`);
    
    if (hasInternalError) {
      throw new Error('❌ Even regular Apfel search has internal error');
    }
    
    console.log('✅ Regular Apfel search works without internal error');
  });
});