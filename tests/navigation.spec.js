const { test, expect } = require('@playwright/test');

test.describe('Navigation', () => {
  test('should navigate to LEGO Parts page', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('nav a[href="lego-parts.html"]');
    await page.click('nav a[href="lego-parts.html"]');
    await expect(page).toHaveURL(/lego-parts\.html/);
    await expect(page).toHaveTitle(/LEGO.*Parts/);
  });

  test('should navigate to 3D Prints page', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('nav a[href="3dprints.html"]');
    await page.click('nav a[href="3dprints.html"]');
    await expect(page).toHaveURL(/3dprints\.html/);
    await expect(page).toHaveTitle(/3D Print/);
  });

  test('should navigate to PAB Service page', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('nav a[href="pab-service.html"]');
    await page.click('nav a[href="pab-service.html"]');
    await expect(page).toHaveURL(/pab-service\.html/);
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
    
    const brickOwlButton = page.locator('a[href*="brickowl.com"]');
    await expect(brickOwlButton).toBeVisible();
  });

  test('should have tabs for Sets and Parts', async ({ page }) => {
    await page.goto('/lego-parts.html');
    
    const setsTab = page.locator('.tab-btn', { hasText: 'Sets' });
    const partsTab = page.locator('.tab-btn', { hasText: 'Clean Parts' });
    
    await expect(setsTab).toBeVisible();
    await expect(partsTab).toBeVisible();
  });

  test('should switch between tabs', async ({ page }) => {
    await page.goto('/lego-parts.html');
    
    // Click Parts tab
    const partsTab = page.locator('.tab-btn', { hasText: 'Clean Parts' });
    await partsTab.click();
    
    // Check if Parts tab is active
    await expect(partsTab).toHaveClass(/active/);
    
    // Check if parts content is visible
    const partsContent = page.locator('#parts-tab');
    await expect(partsContent).toHaveClass(/active/);
  });
});

test.describe('3D Prints Page', () => {
  test('should display product cards', async ({ page }) => {
    await page.goto('/3dprints.html');
    
    const cards = page.locator('.card');
    await expect(cards.first()).toBeVisible();
  });

  test('should have view details buttons', async ({ page }) => {
    await page.goto('/3dprints.html');
    
    const detailsButtons = page.locator('a.btn-stud', { hasText: 'View Details' });
    const count = await detailsButtons.count();
    expect(count).toBeGreaterThan(0);
  });
});
