import { test, expect } from '@playwright/test';

test.describe('PMLytics AI Landing Page & Smoke Tests', () => {
  test('root route / loads successfully with no console errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      // Filter out browser favicon 404 or resource probe errors
      if (msg.type() === 'error' && !msg.text().includes('404')) {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');
    await expect(page).toHaveTitle(/PMLytics AI/i);
    expect(consoleErrors).toEqual([]);
  });

  test('hero section renders approved headline and Scenario 1 preview', async ({ page }) => {
    await page.goto('/');

    // Hero Heading
    await expect(
      page.getByRole('heading', {
        name: /turn scattered product signals into a clear next move/i,
      })
    ).toBeVisible();

    // Curated Scenario 1 Preview
    const productHero = page.locator('#product');
    await expect(
      productHero.getByRole('heading', {
        name: /why are customers reporting a surge in failed transfers this week/i,
      })
    ).toBeVisible();

    // Validated metrics & status pill
    await expect(productHero.getByText('Completed', { exact: true })).toBeVisible();
    await expect(productHero.getByText('98.5s')).toBeVisible();
    await expect(
      productHero.getByRole('region', { name: /recommendation preview/i }).getByText('High', { exact: true })
    ).toBeVisible();
    await expect(productHero.getByText('12 Records', { exact: true })).toBeVisible();

    // Canonical citation pills
    await expect(productHero.getByText('[EV-002]').first()).toBeVisible();
  });

  test('primary hero actions are visible in the opening desktop viewport', async ({ page }) => {
    if ((page.viewportSize()?.width ?? 0) < 768) return;

    await page.goto('/');
    const createAccount = page.getByRole('link', { name: 'Create Account' }).first();
    const sampleBrief = page.getByRole('link', { name: 'View a Sample Brief' }).first();

    await expect(createAccount).toBeVisible();
    await expect(sampleBrief).toBeVisible();

    const [createBox, sampleBox] = await Promise.all([
      createAccount.boundingBox(),
      sampleBrief.boundingBox(),
    ]);
    expect(createBox).not.toBeNull();
    expect(sampleBox).not.toBeNull();
    expect((createBox?.y ?? 1000) + (createBox?.height ?? 0)).toBeLessThanOrEqual(900);
    expect((sampleBox?.y ?? 1000) + (sampleBox?.height ?? 0)).toBeLessThanOrEqual(900);
  });

  test('landing header remains visible while the page scrolls', async ({ page }) => {
    await page.goto('/');
    const header = page.getByRole('banner');
    await expect(header).toBeVisible();
    await page.evaluate(() => window.scrollTo(0, 1800));
    await expect(header).toBeVisible();
    const box = await header.boundingBox();
    expect(box).not.toBeNull();
    expect(Math.abs(box?.y ?? 100)).toBeLessThanOrEqual(1);
  });

  test('landing page renders all major approved sections', async ({ page }) => {
    await page.goto('/');

    // Problem section
    await expect(
      page.getByRole('heading', { name: /your evidence is scattered. your decision shouldn.t be/i })
    ).toBeVisible();

    // Workflow section
    await expect(
      page.getByRole('heading', { name: /from product question to confident next step/i })
    ).toBeVisible();

    // Evidence section
    await expect(
      page.getByRole('heading', { name: /every recommendation is traceable/i })
    ).toBeVisible();

    // Epistemic discipline section
    await expect(
      page.getByRole('heading', { name: /see what the evidence proves/i })
    ).toBeVisible();

    // Example scenarios section
    await expect(
      page.getByRole('heading', { name: /explore completed product investigations/i })
    ).toBeVisible();

    await expect(page.getByRole('heading', { name: /pricing that scales with your product practice/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /what to know before your first investigation/i })).toBeVisible();

    // Final CTA section
    await expect(
      page.getByRole('heading', { name: /bring your next product question/i })
    ).toBeVisible();

    // Footer
    await expect(page.getByRole('contentinfo')).toBeVisible();
    await expect(page.getByText('© 2026 PMLytics AI. All rights reserved.')).toBeVisible();
  });

  test('navigation links are present on desktop', async ({ page }) => {
    const isDesktop = (page.viewportSize()?.width ?? 1000) >= 768;
    if (!isDesktop) return;

    await page.goto('/');
    const nav = page.getByRole('navigation', { name: /primary navigation/i });
    await expect(nav).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Product' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'How It Works' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Pricing' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Sample Investigations' })).toHaveCount(0);
  });

  test('mobile navigation toggle opens menu and Escape closes it', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');

    const toggleBtn = page.getByRole('button', { name: /toggle navigation menu/i });
    await expect(toggleBtn).toBeVisible();
    await expect(toggleBtn).toHaveAttribute('aria-expanded', 'false');

    // Click to open
    await toggleBtn.click();
    await expect(toggleBtn).toHaveAttribute('aria-expanded', 'true');
    const mobileMenu = page.getByRole('dialog', { name: /mobile navigation menu/i });
    await expect(mobileMenu).toBeVisible();

    // Press Escape to close
    await page.keyboard.press('Escape');
    await expect(toggleBtn).toHaveAttribute('aria-expanded', 'false');
    await expect(mobileMenu).not.toBeVisible();
  });

  test('mobile viewport does not introduce horizontal overflow on /', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');

    const hasHorizontalScrollbar = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });

    expect(hasHorizontalScrollbar).toBe(false);
  });

  test('public sample decision brief loads from the landing-page route', async ({ page }) => {
    await page.goto('/investigations/inv_p12a_scenario_1');
    await expect(
      page.getByRole('heading', { name: /why are customers reporting a surge in failed transfers/i })
    ).toBeVisible();
    await expect(page.getByRole('button', { name: /view evidence from/i })).toBeVisible();
  });
});
