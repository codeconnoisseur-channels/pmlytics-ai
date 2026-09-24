import { test, expect } from '@playwright/test';

test.describe('Investigations E2E Journeys', () => {
  test('Journey A: Landing -> sample decision brief', async ({ page }) => {
    await page.goto('/');

    const sampleLink = page.getByRole('link', { name: /view a sample brief/i }).first();
    await expect(sampleLink).toBeVisible();
    await sampleLink.click();

    await expect(page).toHaveURL(/\/investigations\/inv_p12a_scenario_1$/);
    await expect(
      page.getByRole('heading', { name: /why are customers reporting a surge in failed transfers/i })
    ).toBeVisible();
  });

  test('Journey C: Investigations -> select existing investigation -> workspace', async ({ page }) => {
    await page.goto('/investigations');

    const listSection = page.getByRole('region', { name: /recent investigations/i });
    await expect(listSection).toBeVisible();

    // Either an investigation link is present or the empty state is shown
    const firstLink = listSection.getByRole('link').first();
    const emptyState = page.getByText(/no recent investigations/i);

    // Wait for either condition (with generous timeout for API round-trip)
    await expect(firstLink.or(emptyState)).toBeVisible({ timeout: 10000 });

    if (await firstLink.isVisible()) {
      const href = await firstLink.getAttribute('href');
      expect(href).toMatch(/\/investigations\/inv_/);

      await firstLink.click();
      await expect(page).toHaveURL(new RegExp(href!), { timeout: 10000 });

      // Workspace page loaded. The <main> element always exists.
      // The workspace renders either in-flight progress or the completed result;
      // both are valid states. Simply verify we landed on the workspace route.
      const mainEl = page.getByRole('main');
      await expect(mainEl).toBeVisible({ timeout: 15000 });
    } else {

      // Empty state is valid
      await expect(
        page.getByText(/no recent investigations/i)
      ).toBeVisible();
    }
  });

  test('Direct question entry enables submission', async ({ page }) => {
    await page.goto('/investigations');

    const textarea = page.getByPlaceholder(/why did checkout conversion drop/i);
    const submitBtn = page.getByRole('button', { name: /start investigation/i });

    // Initially disabled
    await expect(submitBtn).toBeDisabled();

    await textarea.fill('Why did user verification drop off at the identity upload step for new signups?');

    // Textarea populated and button enabled
    await expect(textarea).toHaveValue(
      'Why did user verification drop off at the identity upload step for new signups?'
    );
    await expect(submitBtn).toBeEnabled();
    await expect(page.getByText(/\d+ \/ 2000/)).toBeVisible();
  });

  test('Mobile viewport: composer usability, list readability, no horizontal overflow', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/investigations');

    // Check headings and controls are visible
    await expect(
      page.getByRole('heading', { name: /what would you like to investigate/i })
    ).toBeVisible();
    const textarea = page.getByPlaceholder(/why did checkout conversion drop/i);
    await expect(textarea).toBeVisible();

    const submitBtn = page.getByRole('button', { name: /start investigation/i });
    await expect(submitBtn).toBeVisible();

    // Check no horizontal scrollbar
    const hasHorizontalOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });
    expect(hasHorizontalOverflow).toBe(false);
  });

  // Journey B: Real backend integration. Desktop Chrome only to avoid duplicate LLM runs.
  test('Journey B: Launchpad -> submit real inquiry -> workspace -> live progress', async ({
    page,
  }) => {
    test.setTimeout(240000); // Allow up to 4 minutes for multi-agent DAG

    // Skip on mobile viewport. This test intentionally hits the live backend once.
    if ((page.viewportSize()?.width ?? 1440) < 768) {
      test.skip();
    }

    await page.goto('/investigations');

    const textarea = page.getByPlaceholder(/why did checkout conversion drop/i);
    const submitBtn = page.getByRole('button', { name: /start investigation/i });

    const testQuery = 'Why did mobile wallet checkout fail for Android users after release v2.4?';
    await textarea.fill(testQuery);
    await expect(submitBtn).toBeEnabled();

    // Intercept POST /api/v1/investigations before clicking
    const [response] = await Promise.all([
      page.waitForResponse(
        (res) =>
          res.url().includes('/api/v1/investigations') &&
          res.request().method() === 'POST'
      ),
      submitBtn.click(),
    ]);

    // Verify 202 Accepted
    expect(response.status()).toBe(202);
    const responseJson = await response.json();
    const newInvestigationId = responseJson.investigation_id;
    expect(newInvestigationId).toMatch(/^inv_/);

    // Verify navigation to workspace
    await page.waitForURL(new RegExp(`/investigations/${newInvestigationId}`), { timeout: 15000 });
    await expect(page).toHaveURL(`/investigations/${newInvestigationId}`);

    // Workspace renders in-flight progress: accept either the progress indicator
    // (in-flight) or the completed workspace header (fast completion)
    const inFlightIndicator = page.getByText(/investigation in progress/i);
    const completedHeading = page.getByRole('heading', { name: testQuery });

    await expect(
      inFlightIndicator.or(completedHeading)
    ).toBeVisible({ timeout: 20000 });

    // Verify a status indicator is visible
    const statusIndicator = page.getByText(
      /planning|gathering evidence|synthesizing|reviewing|revising|completed/i
    ).first();
    await expect(statusIndicator).toBeVisible({ timeout: 20000 });
  });
});
