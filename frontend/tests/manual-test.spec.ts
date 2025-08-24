import { test, expect } from '@playwright/test';

test('Manual test - just check if everything loads', async ({ page }) => {
  console.log('Testing basic functionality...');
  
  // Go to frontend
  await page.goto('http://localhost:3002/');
  await page.waitForTimeout(2000);
  
  // Take screenshot to see what we have
  await page.screenshot({ path: 'current-page.png' });
  
  const title = await page.title();
  console.log('Page title:', title);
  
  const url = page.url();
  console.log('Current URL:', url);
  
  // Look for any form or input elements
  const inputs = await page.locator('input').count();
  const buttons = await page.locator('button').count();
  const links = await page.locator('a').count();
  
  console.log('Found elements:');
  console.log('- Inputs:', inputs);
  console.log('- Buttons:', buttons);
  console.log('- Links:', links);
  
  // List all visible text on the page
  const bodyText = await page.locator('body').textContent();
  console.log('Page content (first 300 chars):', bodyText?.substring(0, 300));
  
  // Check if we can find login, register, launch, or search elements
  const hasLogin = await page.locator('text=Login, [href*="login"]').count() > 0;
  const hasRegister = await page.locator('text=Register, [href*="register"]').count() > 0;
  const hasLaunch = await page.locator('button:has-text("Launch"), button:has-text("launch")').count() > 0;
  const hasSearch = await page.locator('input[type="search"], input[placeholder*="search"]').count() > 0;
  
  console.log('Navigation elements:');
  console.log('- Login:', hasLogin);
  console.log('- Register:', hasRegister);  
  console.log('- Launch:', hasLaunch);
  console.log('- Search:', hasSearch);
  
  // Try clicking launch button first if available
  if (hasLaunch) {
    console.log('Clicking Launch button...');
    await page.click('button:has-text("Launch")');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'after-launch-click.png' });
    
    // Check what happened after launch
    const searchAfterLaunch = await page.locator('input[type="search"], input[placeholder*="search"]').count() > 0;
    console.log('Search available after launch:', searchAfterLaunch);
    
    if (searchAfterLaunch) {
      console.log('✅ Launch led to search interface');
    } else {
      // Maybe we need to login first
      const needsLogin = await page.locator('input[type="email"], text=Login').count() > 0;
      console.log('Needs login after launch:', needsLogin);
    }
  }
  
  // If we find a login link/button, try clicking it
  if (hasLogin) {
    console.log('Clicking login...');
    await page.click('text=Login');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'after-login-click.png' });
    
    // Check for login form
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    
    if (await emailInput.count() > 0 && await passwordInput.count() > 0) {
      console.log('Found login form, filling it...');
      await emailInput.fill('heyeqiu1210@gmail.com');
      await passwordInput.fill('123456');
      
      const submitButton = page.locator('button[type="submit"], button:has-text("Login")');
      if (await submitButton.count() > 0) {
        await submitButton.click();
        console.log('Submitted login form');
        await page.waitForTimeout(3000);
        await page.screenshot({ path: 'after-login-submit.png' });
        
        // Now check if we can find search
        const searchAfterLogin = await page.locator('input[type="search"], input[placeholder*="search"]').count() > 0;
        console.log('Search available after login:', searchAfterLogin);
        
        if (searchAfterLogin) {
          console.log('Testing word search...');
          const searchInput = page.locator('input[type="search"], input[placeholder*="search"]').first();
          await searchInput.fill('nehmen');
          await searchInput.press('Enter');
          await page.waitForTimeout(5000);
          await page.screenshot({ path: 'after-search.png' });
          
          // Check for word results
          const hasResults = await page.locator('.bg-white, .word-result, [data-testid*="result"]').count() > 0;
          console.log('Has search results:', hasResults);
          
          if (hasResults) {
            // Look for our chat and image buttons
            const hasChatButton = await page.locator('button:has-text("💬")').count() > 0;
            const hasImageButton = await page.locator('button:has-text("🎨")').count() > 0;
            
            console.log('Chat button found:', hasChatButton);
            console.log('Image button found:', hasImageButton);
            
            if (hasChatButton || hasImageButton) {
              console.log('✅ SUCCESS: Found our new chat/image buttons!');
            } else {
              console.log('❌ New buttons not found in search results');
            }
          }
        }
      }
    }
  }
  
  console.log('Manual test completed');
});