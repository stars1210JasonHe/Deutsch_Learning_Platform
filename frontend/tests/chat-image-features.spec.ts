import { test, expect } from '@playwright/test';

test.describe('Chat and Image Generation Features', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
    
    // Login
    await page.fill('input[type="email"]', 'heyeqiu1210@gmail.com');
    await page.fill('input[type="password"]', '123456');
    await page.click('button[type="submit"]');
    
    // Wait for login to complete
    await page.waitForURL('**/dashboard', { timeout: 10000 });
  });

  test('should test chat feature with word "nehmen"', async ({ page }) => {
    // Search for the word "nehmen"
    await page.fill('input[placeholder*="search" i]', 'nehmen');
    await page.press('input[placeholder*="search" i]', 'Enter');
    
    // Wait for search results
    await page.waitForSelector('[data-testid="word-result"], .bg-white.rounded-lg.shadow-md', { timeout: 10000 });
    
    // Look for the chat button (💬) and click it
    const chatButton = page.locator('button[title="Chat about this word"], button:has-text("💬")').first();
    await expect(chatButton).toBeVisible({ timeout: 5000 });
    await chatButton.click();
    
    // Wait for chat modal to open
    await page.waitForSelector('text=Chat about: nehmen', { timeout: 5000 });
    
    // Verify chat modal elements
    await expect(page.locator('text=Chat about: nehmen')).toBeVisible();
    await expect(page.locator('text=Ask me anything about "nehmen"!')).toBeVisible();
    
    // Type a test message
    const messageInput = page.locator('textarea[placeholder*="Ask me about this word"]');
    await expect(messageInput).toBeVisible();
    await messageInput.fill('What does nehmen mean and how do I conjugate it?');
    
    // Send the message
    await page.click('button:has-text("Send")');
    
    // Wait for response (this might take a moment with OpenAI)
    await page.waitForSelector('text=What does nehmen mean', { timeout: 3000 });
    
    // Wait for AI response (look for assistant message)
    const assistantResponse = page.locator('.bg-gray-100.text-gray-900').first();
    await expect(assistantResponse).toBeVisible({ timeout: 30000 });
    
    // Verify response contains useful information
    const responseText = await assistantResponse.textContent();
    expect(responseText).toContain('nehmen');
    
    // Test download functionality
    await page.click('button[title="Download conversation"]');
    
    // Test copy functionality  
    await page.click('button[title="Copy conversation"]');
    
    // Close the chat modal
    await page.click('button:has-text("✕")');
    await expect(page.locator('text=Chat about: nehmen')).not.toBeVisible();
  });

  test('should test image generation feature with word "nehmen"', async ({ page }) => {
    // Search for the word "nehmen"
    await page.fill('input[placeholder*="search" i]', 'nehmen');
    await page.press('input[placeholder*="search" i]', 'Enter');
    
    // Wait for search results
    await page.waitForSelector('[data-testid="word-result"], .bg-white.rounded-lg.shadow-md', { timeout: 10000 });
    
    // Look for the image button (🎨) and click it
    const imageButton = page.locator('button[title="Generate image for this word"], button:has-text("🎨")').first();
    await expect(imageButton).toBeVisible({ timeout: 5000 });
    await imageButton.click();
    
    // Wait for image modal to open
    await page.waitForSelector('text=Image for: nehmen', { timeout: 5000 });
    
    // Verify image modal elements
    await expect(page.locator('text=Image for: nehmen')).toBeVisible();
    await expect(page.locator('text=Generate Educational Image')).toBeVisible();
    
    // Verify settings controls
    await expect(page.locator('select').first()).toBeVisible(); // Model selector
    await expect(page.locator('select').nth(1)).toBeVisible(); // Size selector
    
    // Test changing settings
    await page.selectOption('select >> nth=0', 'dall-e-2'); // Select DALL-E 2
    await page.selectOption('select >> nth=1', '512x512'); // Select size
    
    // Select image style
    await page.click('input[value="cartoon"]');
    
    // Generate image
    await page.click('button:has-text("Generate Image")');
    
    // Wait for generation to start
    await page.waitForSelector('text=Creating...', { timeout: 5000 });
    await expect(page.locator('text=Creating...')).toBeVisible();
    
    // Wait for image generation to complete (this might take 30+ seconds)
    await page.waitForSelector('img[alt*="Generated image"], .text-center img', { timeout: 60000 });
    
    // Verify image is displayed
    const generatedImage = page.locator('img[alt*="Generated image"], .text-center img').first();
    await expect(generatedImage).toBeVisible();
    
    // Verify image details are shown
    await expect(page.locator('text=Prompt:')).toBeVisible();
    await expect(page.locator('text=Model:')).toBeVisible();
    await expect(page.locator('text=Size:')).toBeVisible();
    
    // Test regenerate button
    await page.click('button:has-text("🔄 Regenerate")');
    await page.waitForSelector('text=Creating...', { timeout: 5000 });
    
    // Wait a moment then cancel by clearing
    await page.waitForTimeout(2000);
    await page.click('button:has-text("🗑️ Clear")');
    
    // Verify we're back to initial state
    await expect(page.locator('text=Generate Educational Image')).toBeVisible();
    
    // Close the image modal
    await page.click('button:has-text("✕")');
    await expect(page.locator('text=Image for: nehmen')).not.toBeVisible();
  });

  test('should test settings persistence', async ({ page }) => {
    // Search for the word "nehmen"
    await page.fill('input[placeholder*="search" i]', 'nehmen');
    await page.press('input[placeholder*="search" i]', 'Enter');
    
    // Wait for search results
    await page.waitForSelector('[data-testid="word-result"], .bg-white.rounded-lg.shadow-md', { timeout: 10000 });
    
    // Open image modal
    const imageButton = page.locator('button[title="Generate image for this word"], button:has-text("🎨")').first();
    await imageButton.click();
    
    // Change settings
    await page.selectOption('select >> nth=0', 'dall-e-3');
    await page.selectOption('select >> nth=1', '1024x1024');
    await page.click('input[value="realistic"]');
    
    // Close modal
    await page.click('button:has-text("✕")');
    
    // Open modal again
    await imageButton.click();
    
    // Verify settings were saved
    const modelSelect = page.locator('select >> nth=0');
    const sizeSelect = page.locator('select >> nth=1');
    const realisticRadio = page.locator('input[value="realistic"]');
    
    await expect(modelSelect).toHaveValue('dall-e-3');
    await expect(sizeSelect).toHaveValue('1024x1024');
    await expect(realisticRadio).toBeChecked();
    
    // Close modal
    await page.click('button:has-text("✕")');
  });
});