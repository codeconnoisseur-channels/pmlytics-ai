import { expect, test } from '@playwright/test';

test.describe('Hydration and authentication UX', () => {
  test('scenario period hydrates without a server/client mismatch', async ({ page }) => {
    const hydrationErrors: string[] = [];
    page.on('console', (message) => {
      if (message.type() === 'error' && /hydration|server rendered text/i.test(message.text())) {
        hydrationErrors.push(message.text());
      }
    });
    page.on('pageerror', (error) => {
      if (/hydration|server rendered text/i.test(error.message)) {
        hydrationErrors.push(error.message);
      }
    });

    await page.goto('/investigations/inv_p12a_scenario_3');
    await expect(page.getByText('Period: 5 Aug 2026 to 18 Aug 2026')).toBeVisible();
    expect(hydrationErrors).toEqual([]);
  });

  test('auth pages use concise copy and explain the password policy', async ({ page }) => {
    await page.goto('/auth/signin');
    await expect(page.getByText('Continue to your investigations and decision briefs.')).toHaveCount(0);

    await page.goto('/auth/signup');
    await expect(page.getByText('Save investigations securely and return to them at any time.')).toHaveCount(0);
    await expect(page.getByText('8 or more characters')).toBeVisible();
    await expect(page.getByText('One uppercase letter')).toBeVisible();
    await expect(page.getByText('One lowercase letter')).toBeVisible();
    await expect(page.getByText('One number')).toBeVisible();
  });
});
