const { test, expect } = require('@playwright/test');

test.use({ viewport: { width: 1280, height: 720 } });

test.describe('Navigation', () => {
  test('should navigate to LEGO Parts page', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('nav a[href$="lego-parts.html"]');
    await page.click('nav a[href$="lego-parts.html"]');
    await expect(page).toHaveURL(/lego-parts\.html/);
    await expect(page).toHaveTitle(/LEGO.*Parts/);
  });

  test('should navigate to 3D Prints page', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('nav a[href$="3dprints.html"]');
    await page.click('nav a[href$="3dprints.html"]');
    await expect(page).toHaveURL(/3dprints\.html/);
    await expect(page).toHaveTitle(/3D Print/);
  });

  test('should navigate to part highlights page', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('nav a[href$="part-highlights.html"]');
    await page.click('nav a[href$="part-highlights.html"]');
    await expect(page).toHaveURL(/part-highlights\.html/);
    await expect(page.locator('.empty-gallery')).toBeVisible();
  });

  test('should navigate back to home via logo', async ({ page }) => {
    await page.goto('/lego-parts.html', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('nav .logo-container');
    await page.click('nav .logo-container');
    await expect(page).toHaveURL(/index\.html/);
  });
});

test.describe('LEGO Parts Page', () => {
  test('should display store links', async ({ page }) => {
    await page.goto('/lego-parts.html');
    
    const brickLinkButton = page.locator('a[href*="bricklink.com"]');
    await expect(brickLinkButton).toBeVisible();
    await expect(brickLinkButton).toHaveAttribute('href', /#\/shop/);
    
    const brickOwlButton = page.locator('a[href*="brickowl.com"]');
    await expect(brickOwlButton).toBeVisible();
  });

  test('should link to the part photo gallery', async ({ page }) => {
    await page.goto('/lego-parts.html');
    const highlights = page.locator('section a[href$="part-highlights.html"]');
    await expect(highlights.first()).toBeVisible();
  });
});

test.describe('3D Prints Page', () => {
  test('should display product cards without prices', async ({ page }) => {
    await page.goto('/3dprints.html');
    
    const cards = page.locator('.product-card');
    await expect(cards.first()).toBeVisible();
    await expect(page.locator('#products-cards')).not.toContainText('$');
    await expect(cards).toHaveCount(6);
  });

  test('should have view details buttons', async ({ page }) => {
    await page.goto('/3dprints.html');
    
    const detailsButtons = page.locator('a.btn-stud', { hasText: 'See details' });
    const count = await detailsButtons.count();
    expect(count).toBeGreaterThan(0);
  });
});
