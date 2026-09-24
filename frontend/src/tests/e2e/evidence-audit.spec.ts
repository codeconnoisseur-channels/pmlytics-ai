import { expect, test } from '@playwright/test';

test.describe('Evidence audit layer', () => {
  test('expands, filters, and searches supporting source records without exposing raw IDs', async ({
    page,
  }) => {
    const consoleErrors: string[] = [];
    page.on('console', (message) => {
      if (message.type() === 'error' && !message.text().includes('404')) {
        consoleErrors.push(message.text());
      }
    });

    await page.goto('/investigations/inv_p12a_scenario_1');
    await page.getByRole('button', { name: /view evidence from/i }).click();

    const drawer = page.getByRole('dialog', { name: /evidence ledger drawer/i });
    await expect(drawer).toBeVisible();
    await expect(drawer.getByText('Evidence from 3 sources')).toBeVisible();

    await drawer.getByRole('button', { name: /view records/i }).first().click();
    await expect(drawer.getByText('Customer conversation #1', { exact: true })).toBeVisible();
    await expect(drawer.getByText('Customer conversation #12', { exact: true })).toBeVisible();

    const search = drawer.getByRole('searchbox', { name: /search evidence records/i });
    await search.fill('Customer conversation #6');
    await expect(drawer.getByText('Customer conversation #6', { exact: true })).toBeVisible();
    await expect(drawer.getByText('Customer conversation #1', { exact: true })).toHaveCount(0);
    await expect(drawer.getByText('[EV-002]')).toHaveCount(0);

    await search.fill('');
    await drawer.getByRole('tab', { name: /product analytics/i }).click();
    await drawer.getByRole('button', { name: /view records/i }).click();
    await expect(drawer.getByText('Bank A confirmation time')).toBeVisible();
    await expect(drawer.getByText('Overall transfer outcomes')).toBeVisible();

    await expect(drawer).not.toContainText(/distinct_id|transaction_id|requester_id|failure_code/i);
    expect(consoleErrors).toEqual([]);
  });
});
