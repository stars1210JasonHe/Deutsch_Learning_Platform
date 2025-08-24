import { test, expect } from '@playwright/test';

test('debug frontend loading', async ({ page }) => {
  console.log('Navigating to frontend...');
  await page.goto('/');
  
  // Take a screenshot to see what's on the page
  await page.screenshot({ path: 'frontend-debug.png' });
  
  // Print page title and URL
  console.log('Page title:', await page.title());
  console.log('Page URL:', page.url());
  
  // Check what's visible on the page
  const bodyText = await page.locator('body').textContent();
  console.log('Page content preview:', bodyText?.substring(0, 500));
  
  // Look for common elements
  const hasLoginForm = await page.locator('form, input[type="email"], input[type="password"]').count() > 0;
  console.log('Has login form:', hasLoginForm);
  
  const hasAppContent = await page.locator('h1, .container, #app').count() > 0;
  console.log('Has app content:', hasAppContent);
  
  // Check for error messages
  const errorText = await page.locator('text=/error|Error|fail|Fail|404|500/i').count();
  console.log('Error indicators found:', errorText);
  
  // If no login form, maybe we're already logged in or on dashboard
  if (!hasLoginForm) {
    // Look for navigation elements to get to the right page
    const hasLogin = await page.locator('text=Login, a[href*="login"], button:has-text("Login")').count() > 0;
    const hasRegister = await page.locator('text=Register, a[href*="register"], button:has-text("Register")').count() > 0;
    const hasLaunch = await page.locator('button:has-text("Launch"), a:has-text("Launch")').count() > 0;
    
    console.log('Has login link:', hasLogin);
    console.log('Has register link:', hasRegister);
    console.log('Has launch button:', hasLaunch);
    
    // Try clicking launch or login button
    if (hasLaunch) {
      console.log('Clicking Launch button...');
      await page.click('button:has-text("Launch")');
      await page.waitForTimeout(2000);
    } else if (hasLogin) {
      console.log('Clicking Login...');
      await page.click('text=Login');
      await page.waitForTimeout(2000);
    }
    
    const hasSearch = await page.locator('input[placeholder*="search" i], input[type="search"]').count() > 0;
    console.log('Has search input:', hasSearch);
    
    if (hasSearch) {
      console.log('Found search - testing word lookup directly');
      
      // Try searching for "nehmen"
      await page.fill('input[placeholder*="search" i]', 'nehmen');
      await page.press('input[placeholder*="search" i]', 'Enter');
      
      // Wait a moment and check results
      await page.waitForTimeout(3000);
      
      // Look for word results
      const hasResults = await page.locator('.bg-white.rounded-lg.shadow-md, [data-testid="word-result"]').count() > 0;
      console.log('Has search results:', hasResults);
      
      if (hasResults) {
        // Look for our new buttons
        const hasChatButton = await page.locator('button:has-text("💬"), button[title*="Chat"]').count() > 0;
        const hasImageButton = await page.locator('button:has-text("🎨"), button[title*="image"]').count() > 0;
        
        console.log('Has chat button:', hasChatButton);
        console.log('Has image button:', hasImageButton);
        
        if (hasChatButton) {
          console.log('Testing chat button...');
          await page.click('button:has-text("💬")');
          await page.waitForTimeout(2000);
          
          const hasChatModal = await page.locator('text=Chat about').count() > 0;
          console.log('Chat modal opened:', hasChatModal);
          
          if (hasChatModal) {
            // Try sending a message
            const messageInput = page.locator('textarea[placeholder*="Ask"]');
            if (await messageInput.count() > 0) {
              await messageInput.fill('What does nehmen mean?');
              await page.click('button:has-text("Send")');
              console.log('Message sent to chat');
              
              // Wait for response
              await page.waitForTimeout(5000);
              const hasResponse = await page.locator('.bg-gray-100.text-gray-900').count() > 0;
              console.log('Got chat response:', hasResponse);
            }
          }
        }
      }
    }
  }
  
  // Final screenshot
  await page.screenshot({ path: 'frontend-final.png' });
});