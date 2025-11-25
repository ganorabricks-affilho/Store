const { test, expect } = require('@playwright/test');

test.describe('Mobile Navigation', () => {
  test.use({ viewport: { width: 375, height: 667 } }); // iPhone size

  test('should show hamburger menu on mobile', async ({ page }) => {
    await page.goto('/');
    
    // Hamburger should be visible
    const hamburger = page.locator('.hamburger');
    await expect(hamburger).toBeVisible();
    
    // Navigation menu should be hidden initially
    const navMenu = page.locator('nav ul');
    await expect(navMenu).not.toBeVisible();
  });

  test('should toggle menu when hamburger is clicked', async ({ page }) => {
    await page.goto('/');
    
    const hamburger = page.locator('.hamburger');
    const navMenu = page.locator('nav ul');
    
    // Click hamburger to open menu
    await hamburger.click();
    
    // Menu should be visible
    await expect(navMenu).toBeVisible();
    await expect(page.locator('nav')).toHaveClass(/active/);
    
    // Menu items should be visible
    const legoPartsLink = page.locator('nav a[href="lego-parts.html"]');
    await expect(legoPartsLink).toBeVisible();
  });

  test('should close menu when navigation link is clicked', async ({ page }) => {
    await page.goto('/');
    
    const hamburger = page.locator('.hamburger');
    await hamburger.click();
    
    // Click a navigation link
    const legoPartsLink = page.locator('nav a[href="lego-parts.html"]');
    await legoPartsLink.click();
    
    // Wait for navigation
    await page.waitForURL(/lego-parts\.html/);
    
    // Menu should be closed on new page
    const nav = page.locator('nav');
    await expect(nav).not.toHaveClass(/active/);
  });

  test('should have responsive layout', async ({ page }) => {
    await page.goto('/');
    
    // Check that hero section stacks vertically
    const hero = page.locator('.hero');
    await expect(hero).toBeVisible();
    
    // Logo should be smaller on mobile
    const logo = page.locator('nav .logo-container img');
    const logoBox = await logo.boundingBox();
    expect(logoBox.width).toBeLessThanOrEqual(50);
  });

  test('should have full-width buttons in mobile menu', async ({ page }) => {
    await page.goto('/');
    
    const hamburger = page.locator('.hamburger');
    await hamburger.click();
    
    // Get the first button
    const button = page.locator('nav ul li a.btn-stud').first();
    const buttonBox = await button.boundingBox();
    const viewportWidth = page.viewportSize().width;
    
    // Button should be close to full width (accounting for padding)
    expect(buttonBox.width).toBeGreaterThan(viewportWidth * 0.8);
  });
});

test.describe('Mobile Responsive Design', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('should have readable text on mobile', async ({ page }) => {
    await page.goto('/');
    
    const heroTitle = page.locator('.hero-text h1');
    await expect(heroTitle).toBeVisible();
    
    // Title should be visible and not overflow
    const titleBox = await heroTitle.boundingBox();
    const viewportWidth = page.viewportSize().width;
    expect(titleBox.width).toBeLessThanOrEqual(viewportWidth);
  });

  test('should display cards in single column on mobile', async ({ page }) => {
    await page.goto('/3dprints.html');
    
    const cards = page.locator('.card');
    const firstCard = cards.first();
    const secondCard = cards.nth(1);
    
    await expect(firstCard).toBeVisible();
    await expect(secondCard).toBeVisible();
    
    // Get positions
    const firstBox = await firstCard.boundingBox();
    const secondBox = await secondCard.boundingBox();
    
    // Second card should be below first card (not side by side)
    expect(secondBox.y).toBeGreaterThan(firstBox.y + firstBox.height - 10);
  });

  test('should have appropriate spacing on mobile', async ({ page }) => {
    await page.goto('/');
    
    // Check body has appropriate padding
    const body = page.locator('body');
    const bodyStyles = await body.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        paddingTop: styles.paddingTop,
        paddingBottom: styles.paddingBottom,
      };
    });
    
    // Should have padding for fixed header and footer
    expect(parseInt(bodyStyles.paddingTop)).toBeGreaterThan(50);
    expect(parseInt(bodyStyles.paddingBottom)).toBeGreaterThan(50);
  });
});
