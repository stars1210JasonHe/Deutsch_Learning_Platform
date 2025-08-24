import { test, expect } from '@playwright/test';

test('Test chat and image with nehmen on port 3002', async ({ page }) => {
  // Go to the current frontend port
  await page.goto('http://localhost:3002/');
  
  console.log('=== Testing Chat and Image Features with "nehmen" ===');
  
  // Take initial screenshot
  await page.screenshot({ path: 'test-start.png' });
  
  // Check if we need to login or if there's a direct search
  const hasLoginButton = await page.locator('text=Login, button:has-text("Login")').count() > 0;
  const hasLaunchButton = await page.locator('button:has-text("Launch"):not([disabled])').count() > 0;
  const hasSearchInput = await page.locator('input[placeholder*="search" i]').count() > 0;
  
  console.log('Has login button:', hasLoginButton);
  console.log('Has enabled launch button:', hasLaunchButton);
  console.log('Has search input:', hasSearchInput);
  
  // Try to get to the search interface
  if (hasSearchInput) {
    console.log('Found search input directly');
  } else if (hasLaunchButton) {
    console.log('Clicking Launch button...');
    await page.click('button:has-text("Launch"):not([disabled])');
    await page.waitForTimeout(2000);
  } else if (hasLoginButton) {
    console.log('Going to login...');
    await page.click('text=Login');
    await page.waitForTimeout(1000);
    
    // Fill login form
    await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
    await page.fill('input[type="password"]', '123456');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
  }
  
  // Look for search input again
  const searchInput = page.locator('input[placeholder*="search" i]').first();
  await expect(searchInput).toBeVisible({ timeout: 10000 });
  
  console.log('✅ Found search input, testing word lookup...');
  
  // Search for "nehmen"
  await searchInput.fill('nehmen');
  await searchInput.press('Enter');
  
  // Wait for results
  await page.waitForTimeout(5000);
  
  // Look for word result container
  const wordResult = page.locator('.bg-white.rounded-lg.shadow-md, [data-testid="word-result"]').first();
  await expect(wordResult).toBeVisible({ timeout: 10000 });
  
  console.log('✅ Found word result for "nehmen"');
  
  // Take screenshot of results
  await page.screenshot({ path: 'test-word-result.png' });
  
  // Test Chat Feature
  console.log('🔍 Looking for chat button...');
  const chatButton = page.locator('button:has-text("💬"), button[title*="Chat"]').first();
  
  if (await chatButton.count() > 0) {
    console.log('✅ Found chat button, testing...');
    await chatButton.click();
    
    // Wait for chat modal
    await page.waitForSelector('text=Chat about', { timeout: 5000 });
    console.log('✅ Chat modal opened');
    
    // Send test message
    const messageInput = page.locator('textarea[placeholder*="Ask"]');
    if (await messageInput.count() > 0) {
      await messageInput.fill('What does nehmen mean in English?');
      await page.click('button:has-text("Send")');
      console.log('✅ Message sent');
      
      // Wait for AI response (max 30 seconds)
      try {
        await page.waitForSelector('.bg-gray-100.text-gray-900', { timeout: 30000 });
        console.log('✅ Got AI response!');
        
        const responseText = await page.locator('.bg-gray-100.text-gray-900').first().textContent();
        console.log('Response preview:', responseText?.substring(0, 100) + '...');
      } catch (e) {
        console.log('❌ No AI response received within 30 seconds');
      }
      
      // Close chat modal
      await page.click('button:has-text("✕")');
      console.log('✅ Chat modal closed');
    }
  } else {
    console.log('❌ Chat button not found');
  }
  
  // Test Image Generation Feature
  console.log('🔍 Looking for image button...');
  const imageButton = page.locator('button:has-text("🎨"), button[title*="image"]').first();
  
  if (await imageButton.count() > 0) {
    console.log('✅ Found image button, testing...');
    await imageButton.click();
    
    // Wait for image modal
    await page.waitForSelector('text=Image for', { timeout: 5000 });
    console.log('✅ Image modal opened');
    
    // Check settings
    const modelSelect = page.locator('select').first();
    if (await modelSelect.count() > 0) {
      await modelSelect.selectOption('dall-e-2'); // Use faster model for testing
      console.log('✅ Selected DALL-E 2 model');
    }
    
    // Generate image
    const generateButton = page.locator('button:has-text("Generate Image")');
    if (await generateButton.count() > 0) {
      await generateButton.click();
      console.log('✅ Started image generation...');
      
      // Wait for "Creating..." text
      try {
        await page.waitForSelector('text=Creating', { timeout: 5000 });
        console.log('✅ Image generation started');
        
        // Wait for image to appear (max 60 seconds)
        await page.waitForSelector('img[alt*="Generated image"], .text-center img', { timeout: 60000 });
        console.log('✅ Image generated successfully!');
        
        // Take screenshot of the generated image
        await page.screenshot({ path: 'test-generated-image.png' });
        
      } catch (e) {
        console.log('❌ Image generation failed or timed out');
      }
      
      // Close image modal
      await page.click('button:has-text("✕")');
      console.log('✅ Image modal closed');
    }
  } else {
    console.log('❌ Image button not found');
  }
  
  // Final screenshot
  await page.screenshot({ path: 'test-final.png' });
  console.log('=== Test completed ===');
});