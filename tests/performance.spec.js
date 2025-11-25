const { test, expect } = require('@playwright/test');

test.describe('Performance', () => {
  test('should load home page quickly', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    const loadTime = Date.now() - startTime;
    
    // Page should load in under 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should not have console errors', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Filter out known acceptable errors (like missing favicon)
    const criticalErrors = consoleErrors.filter(
      error => !error.includes('favicon') && !error.includes('404')
    );
    
    expect(criticalErrors).toHaveLength(0);
  });

  test('should have no broken images', async ({ page }) => {
    await page.goto('/');
    
    const images = await page.locator('img').all();
    
    for (const img of images) {
      const src = await img.getAttribute('src');
      if (src && !src.startsWith('http')) {
        // Check if image loaded successfully
        const naturalWidth = await img.evaluate((el) => el.naturalWidth);
        expect(naturalWidth).toBeGreaterThan(0);
      }
    }
  });

  test('should load all CSS and JS files', async ({ page }) => {
    const failedRequests = [];
    
    page.on('requestfailed', (request) => {
      failedRequests.push(request.url());
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Filter out known missing resources
    const criticalFailures = failedRequests.filter(
      url => url.endsWith('.css') || url.endsWith('.js')
    );
    
    expect(criticalFailures).toHaveLength(0);
  });
});
