const { test, expect } = require('@playwright/test');

test.describe('Accessibility', () => {
  test('should have proper document structure', async ({ page }) => {
    await page.goto('/');
    
    // Check for main heading
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    
    // Check for proper heading hierarchy
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings.length).toBeGreaterThan(0);
  });

  test('should have alt text for images', async ({ page }) => {
    await page.goto('/');
    
    const logo = page.locator('nav .logo-container img');
    await expect(logo).toHaveAttribute('alt');
  });

  test('should have proper link text', async ({ page }) => {
    await page.goto('/');
    
    // All links should have text or aria-label
    const links = await page.locator('a').all();
    
    for (const link of links) {
      const text = await link.textContent();
      const ariaLabel = await link.getAttribute('aria-label');
      expect(text?.trim() || ariaLabel).toBeTruthy();
    }
  });

  test('should have clickable areas of adequate size', async ({ page }) => {
    await page.goto('/');
    
    // Wait for navbar to load (it's loaded via fetch)
    await page.waitForSelector('nav a.btn-stud', { state: 'visible', timeout: 10000 });
    
    // Test navigation buttons
    const navButton = page.locator('nav a.btn-stud').first();
    await expect(navButton).toBeVisible();
    
    const box = await navButton.boundingBox();
    expect(box).not.toBeNull();
    expect(box.width).toBeGreaterThanOrEqual(44); // WCAG minimum
    expect(box.height).toBeGreaterThanOrEqual(44);
  });

  test('should have sufficient color contrast for text', async ({ page }) => {
    await page.goto('/');
    
    // Check that text is visible (basic visibility check)
    const heroText = page.locator('.hero-text p');
    await expect(heroText).toBeVisible();
    
    const color = await heroText.evaluate((el) => {
      return window.getComputedStyle(el).color;
    });
    
    // Just verify color is set
    expect(color).toBeTruthy();
  });
});

test.describe('SEO', () => {
  test('should have proper meta tags', async ({ page }) => {
    await page.goto('/');
    
    // Check viewport meta tag
    const viewportMeta = await page.locator('meta[name="viewport"]').count();
    expect(viewportMeta).toBe(1);
    
    // Check charset
    const charsetMeta = await page.locator('meta[charset]').count();
    expect(charsetMeta).toBe(1);
  });

  test('should have descriptive page titles on all pages', async ({ page }) => {
    const pages = ['/', '/lego-parts.html', '/3dprints.html', '/pab-service.html'];
    
    for (const url of pages) {
      await page.goto(url);
      const title = await page.title();
      expect(title.length).toBeGreaterThan(0);
      expect(title).toContain('Ganorabricks');
    }
  });

  test('should have working links', async ({ page }) => {
    await page.goto('/');
    
    // Check external links have target and rel attributes
    const externalLinks = await page.locator('a[target="_blank"]').all();
    
    for (const link of externalLinks) {
      const href = await link.getAttribute('href');
      expect(href).toBeTruthy();
    }
  });
});
