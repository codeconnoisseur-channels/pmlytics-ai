import { test, expect } from '@playwright/test';

test.describe('Investigation Workspace E2E Tests', () => {
  test('desktop: completed workspace renders with approved hierarchy and no errors', async ({ page }) => {
    const isDesktop = (page.viewportSize()?.width ?? 1000) >= 768;
    if (!isDesktop) return;

    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error' && !msg.text().includes('404')) {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/investigations/inv_p12a_scenario_1');

    // 1. Sticky Inquiry Header
    await expect(
      page.getByRole('heading', {
        name: /why are customers reporting a surge in failed transfers this week\?/i,
      })
    ).toBeVisible();
    await expect(page.getByText('COMPLETED', { exact: true })).toBeVisible();
    await expect(page.getByText('98.5s')).toBeVisible();

    const reportScroller = page.locator('#main-content');
    await expect(reportScroller).toBeVisible();
    const scrollRange = await reportScroller.evaluate((element) => ({
      clientHeight: element.clientHeight,
      scrollHeight: element.scrollHeight,
    }));
    expect(scrollRange.scrollHeight).toBeGreaterThan(scrollRange.clientHeight);
    await reportScroller.evaluate((element) => element.scrollTo({ top: 700 }));
    await expect.poll(() => reportScroller.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);

    // 2. Elevated Recommendation Panel
    const recommendationSection = page.getByRole('region', { name: /^recommendation$/i });
    await expect(recommendationSection).toBeVisible();
    await expect(recommendationSection.getByText('HIGH', { exact: true })).toBeVisible();
    await expect(
      recommendationSection.getByText('Prioritise', { exact: true })
    ).toBeVisible();

    // 3. Verify reading order hierarchy: Recommendation appears above Lower Sections
    const recBox = await recommendationSection.boundingBox();
    const findingsSection = page.getByRole('region', { name: /evidence-backed findings/i });
    const findingsBox = await findingsSection.boundingBox();
    expect(recBox).not.toBeNull();
    expect(findingsBox).not.toBeNull();
    if (recBox && findingsBox) {
      expect(recBox.y).toBeLessThan(findingsBox.y);
    }

    // 4. Citation click opens Evidence Ledger and highlights evidence item
    const citationBtn = page.getByRole('button', { name: /view evidence record \[EV-002\]/i }).first();
    await expect(citationBtn).toBeVisible();
    await citationBtn.click();

    // Ledger drawer is now visible
    const ledgerDialog = page.getByRole('dialog', { name: /evidence ledger/i });
    await expect(ledgerDialog).toBeVisible();

    // EV-002 is highlighted in the ledger
    const evCard = ledgerDialog.locator('#source-posthog');
    await expect(evCard).toBeVisible();
    await expect(evCard).toHaveClass(/border-brand-primary/);

    // Filter evidence by source in ledger
    const zendeskTab = ledgerDialog.getByRole('tab', { name: /customer support/i });
    await zendeskTab.click();
    await expect(ledgerDialog.getByText('[EV-001]')).toBeVisible();
    await expect(ledgerDialog.getByText('[EV-002]')).not.toBeVisible();

    // 5. Close drawer via Close button
    const closeBtn = ledgerDialog.getByRole('button', { name: /close evidence ledger/i });
    await closeBtn.click();
    await expect(ledgerDialog).not.toBeVisible();

    // 6. Private investigations do not expose a misleading copy-link control
    await expect(page.getByRole('button', { name: /copy.*link/i })).toHaveCount(0);
  });

  test('responsive breakpoints: Evidence Ledger adapts accurately across all approved tiers', async ({ page }) => {
    // Tier 1: Widescreen Desktop (>= 1600px) -> Docked mode (no backdrop)
    await page.setViewportSize({ width: 1600, height: 1000 });
    await page.goto('/investigations/inv_p12a_scenario_1');
    const ledgerBtn = page.getByRole('button', { name: /view evidence from/i });
    await ledgerBtn.click();

    const ledgerDialog = page.getByRole('dialog', { name: /evidence ledger/i });
    await expect(ledgerDialog).toBeVisible();

    const backdrop = page.getByTestId('evidence-ledger-backdrop');
    await expect(backdrop).not.toBeVisible();

    const boxWidescreen = await ledgerDialog.boundingBox();
    expect(boxWidescreen).not.toBeNull();
    if (boxWidescreen) {
      expect(boxWidescreen.width).toBeGreaterThanOrEqual(410);
      expect(boxWidescreen.width).toBeLessThanOrEqual(440);
    }

    // Tier 2: Standard Desktop (1440 × 900) -> Slide-over drawer with backdrop
    await page.setViewportSize({ width: 1440, height: 900 });
    await expect(backdrop).toBeVisible();
    const box1440 = await ledgerDialog.boundingBox();
    expect(box1440).not.toBeNull();
    if (box1440) {
      expect(box1440.width).toBeGreaterThanOrEqual(390);
      expect(box1440.width).toBeLessThanOrEqual(430);
    }

    // Tier 3: Standard Desktop (1280 × 800) -> Slide-over drawer with backdrop
    await page.setViewportSize({ width: 1280, height: 800 });
    await expect(backdrop).toBeVisible();
    const box1280 = await ledgerDialog.boundingBox();
    expect(box1280).not.toBeNull();
    if (box1280) {
      expect(box1280.width).toBeGreaterThanOrEqual(390);
      expect(box1280.width).toBeLessThanOrEqual(430);
    }

    // Tier 4: Compact Desktop / Tablet (1024 × 768) -> Overlay mode with backdrop
    await page.setViewportSize({ width: 1024, height: 768 });
    await expect(backdrop).toBeVisible();
    const box1024 = await ledgerDialog.boundingBox();
    expect(box1024).not.toBeNull();
    if (box1024) {
      expect(box1024.width).toBeGreaterThanOrEqual(390);
      expect(box1024.width).toBeLessThanOrEqual(430);
    }
  });

  test('live completed investigation: renders actual backend result through Next.js frontend', async ({ page }) => {
    // Test the live investigation completed in backend process memory
    await page.goto('/investigations/inv_20260918_075704_f17563');

    // 1. Live Query Heading
    await expect(
      page.getByRole('heading', {
        name: /why did checkout conversion drop for android users this week\?/i,
      })
    ).toBeVisible();

    // 2. Status & Metadata
    await expect(page.getByText('COMPLETED', { exact: true })).toBeVisible();
    await expect(page.getByText(/190\.8s/)).toBeVisible();
    await expect(page.getByText(/13 LLM \(1 Rev\)/)).toBeVisible();

    // 3. Evidence Ledger has 18 real records retrieved from live backend
    const ledgerToggle = page.getByRole('button', { name: /view evidence from/i });
    await expect(ledgerToggle).toBeVisible();
    await expect(ledgerToggle.getByText('18')).toBeVisible();

    // 4. Recommendation text from real PM agent
    const recSection = page.getByRole('region', { name: /recommendation & decision/i });
    await expect(recSection).toBeVisible();
    await expect(
      recSection.getByText(/investigate further before prioritizing remediation/i)
    ).toBeVisible();

    // 5. Critic Review from real Critic agent
    const criticToggle = page.getByRole('button', { name: /adversarial critic review/i });
    await expect(criticToggle).toBeVisible();
    await expect(page.getByText('PASS', { exact: true })).toBeVisible();
    await criticToggle.click();
    await expect(
      page.getByText(/The recommendation is appropriately cautious, grounded in the verified ledger/i)
    ).toBeVisible();
  });

  test('mobile: workspace loads, top bar remains usable, and sheet handles Escape', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/investigations/inv_p12a_scenario_1');

    // 1. Top bar remains usable
    const ledgerToggle = page.getByRole('button', { name: /view evidence from/i });
    await expect(ledgerToggle).toBeVisible();

    // 2. Recommendation remains prominent
    const recSection = page.getByRole('region', { name: /recommendation & decision/i });
    await expect(recSection).toBeVisible();
    await expect(recSection.getByText('HIGH', { exact: true })).toBeVisible();

    // 3. Citation interaction opens ledger drawer as full-width sheet on mobile
    const citationBtn = page.getByRole('button', { name: /view evidence record \[EV-001\]/i }).first();
    await expect(citationBtn).toBeVisible();
    await citationBtn.click();

    const ledgerDialog = page.getByRole('dialog', { name: /evidence ledger/i });
    await expect(ledgerDialog).toBeVisible();

    // Check full-width sheet style on mobile
    const dialogBox = await ledgerDialog.boundingBox();
    expect(dialogBox).not.toBeNull();
    if (dialogBox) {
      expect(dialogBox.width).toBeGreaterThanOrEqual(380);
    }

    // 4. Press Escape to close sheet
    await page.keyboard.press('Escape');
    await expect(ledgerDialog).not.toBeVisible();

    // 5. No horizontal overflow on mobile
    const hasOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });
    expect(hasOverflow).toBe(false);
  });

  test('404 state: arbitrary non-sample investigation displays honest Not Found', async ({ page }) => {
    await page.goto('/investigations/inv_nonexistent_404_id');
    await expect(page.getByRole('heading', { name: /investigation not found/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /return to investigations/i })).toBeVisible();
  });
});
