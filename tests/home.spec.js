const { test, expect } = require('@playwright/test');

test.describe('Home Page', () => {
  test('should load home page successfully', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Ganorabricks.*LEGO.*Parts.*3D Prints/);
  });

  test('should have navigation bar with logo', async ({ page }) => {
    await page.goto('/');
    
    // Check logo is visible
    const logo = page.locator('nav .logo-container img');
    await expect(logo).toBeVisible();
    
    // Check brand name
    const brandName = page.locator('nav .logo-container span');
    await expect(brandName).toHaveText('Ganorabricks');
  });

  test('should have all navigation links', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    
    // Wait for navbar to load
    await page.waitForSelector('nav ul', { timeout: 10000 });
    
    const legoPartsLink = page.locator('nav a[href="lego-parts.html"]');
    const printsLink = page.locator('nav a[href="3dprints.html"]');
    const pabLink = page.locator('nav a[href="pab-service.html"]');
    
    await expect(legoPartsLink).toContainText('LEGO');
    await expect(printsLink).toContainText('3D Prints');
    await expect(pabLink).toContainText('Pick a Brick');
  });

  test('should have hero section with content', async ({ page }) => {
    await page.goto('/');
    
    const heroTitle = page.locator('.hero-text h1');
    await expect(heroTitle).toBeVisible();
    await expect(heroTitle).toContainText('LEGO');
    
    const heroDescription = page.locator('.hero-text p');
    await expect(heroDescription).toBeVisible();
  });

  test('should have "What I Offer" section', async ({ page }) => {
    await page.goto('/');
    
    const offerSection = page.locator('.offer');
    await expect(offerSection).toBeVisible();
    
    const sectionTitle = page.locator('.section-title');
    await expect(sectionTitle.first()).toContainText('What I Offer');
  });

  test('should have footer', async ({ page }) => {
    await page.goto('/');
    
    const footer = page.locator('footer');
    await expect(footer).toBeVisible();
  });

  test('should have Google Analytics tracking', async ({ page }) => {
    await page.goto('/');
    
    // Check if GA script is loaded
    const gaScript = page.locator('script[src*="googletagmanager.com/gtag/js"]');
    await expect(gaScript).toHaveCount(1);
  });
});
