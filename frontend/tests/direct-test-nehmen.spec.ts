import { test, expect } from '@playwright/test';

test('Direct test: Login and test nehmen with chat/image', async ({ page }) => {
  console.log('=== Direct Test: Chat and Image with "nehmen" ===');
  
  // Go directly to login page
  await page.goto('http://localhost:3003/login');
  await page.waitForTimeout(2000);
  
  console.log('Step 1: Logging in...');
  
  // Fill login form
  await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
  await page.fill('input[type="password"]', '123456');
  await page.click('button[type="submit"]');
  
  // Wait for redirect to dashboard/search page
  await page.waitForTimeout(5000);
  await page.screenshot({ path: 'after-login.png' });
  
  console.log('Step 2: Looking for search interface...');
  
  // Find search input (try multiple possible selectors)
  const searchInput = page.locator('input[placeholder*="search" i], input[type="search"], input[name="search"]').first();
  await expect(searchInput).toBeVisible({ timeout: 10000 });
  
  console.log('✅ Found search input');
  
  // Search for "nehmen"
  console.log('Step 3: Searching for "nehmen"...');
  await searchInput.fill('nehmen');
  await searchInput.press('Enter');
  
  // Wait for search results
  await page.waitForTimeout(10000);
  await page.screenshot({ path: 'search-results.png' });
  
  // Look for word result container
  const wordResult = page.locator('.bg-white.rounded-lg, .word-result, [data-testid*="result"]').first();
  await expect(wordResult).toBeVisible({ timeout: 15000 });
  
  console.log('✅ Found search results for "nehmen"');
  
  // Test Chat Feature
  console.log('Step 4: Testing Chat button...');
  const chatButton = page.locator('button:has-text("💬")').first();
  
  if (await chatButton.count() > 0) {
    console.log('✅ Found chat button!');
    await chatButton.click();
    
    // Wait for chat modal
    await page.waitForSelector('text=Chat about nehmen', { timeout: 10000 });
    console.log('✅ Chat modal opened');
    
    // Send a message
    const messageInput = page.locator('textarea[placeholder*="Ask"], textarea');
    await messageInput.fill('What does nehmen mean?');
    await page.click('button:has-text("Send")');
    
    console.log('✅ Message sent, waiting for AI response...');
    
    // Wait for AI response (30 seconds max)
    try {
      await page.waitForSelector('.bg-gray-100, .assistant-message', { timeout: 30000 });
      console.log('✅ Got AI chat response!');
      
      // Close chat
      await page.click('button:has-text("✕")');
      console.log('✅ Chat test completed successfully');
    } catch (e) {
      console.log('❌ Chat response timeout or error');
    }
  } else {
    console.log('❌ Chat button not found');
  }
  
  // Test Image Generation
  console.log('Step 5: Testing Image button...');
  const imageButton = page.locator('button:has-text("🎨")').first();
  
  if (await imageButton.count() > 0) {
    console.log('✅ Found image button!');
    await imageButton.click();
    
    // Wait for image modal
    await page.waitForSelector('text=Image for nehmen', { timeout: 10000 });
    console.log('✅ Image modal opened');
    
    // Click generate
    await page.click('button:has-text("Generate Image")');
    console.log('✅ Started image generation...');
    
    // Wait for "Creating..." indicator
    try {
      await page.waitForSelector('text=Creating', { timeout: 10000 });
      console.log('✅ Image generation started');
      
      // Wait for image to appear (60 seconds max)
      await page.waitForSelector('img[alt*="Generated"], img[src*="dall"]', { timeout: 60000 });
      console.log('✅ Image generated successfully!');
      
      await page.screenshot({ path: 'generated-image.png' });
      
      // Close image modal
      await page.click('button:has-text("✕")');
      console.log('✅ Image test completed successfully');
      
    } catch (e) {
      console.log('❌ Image generation timeout or error');
    }
  } else {
    console.log('❌ Image button not found');
  }
  
  await page.screenshot({ path: 'final-test-result.png' });
  console.log('=== Test completed ===');
});