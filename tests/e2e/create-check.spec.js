import { test, expect } from '@playwright/test';

test.use({ storageState: 'tests/e2e/.auth/user.json' });

async function openAddCheck(page) {
  await page.goto('/');
  await page.getByRole('link', { name: /SQE Test Project/ }).first().click();
  await page.getByRole('button', { name: 'Add Check' }).first().click();
  await expect(page.locator('#add-check-modal')).toBeVisible();
}

test('UC1: create a check with test data and read back the confirmation', async ({ page }) => {
  const name = 'e2e-create-ok';
  await openAddCheck(page);
  await page.locator('#add-check-name').fill(name);
  await page.locator('#add-check-slug').fill('e2e-create-ok');
  await page.locator('#add-check-period').fill('1');
  await page.locator('#add-check-submit').click();

  await expect(page).toHaveURL(/\/projects\/.*\/checks\//);
  await expect(page.getByText(name, { exact: true }).first()).toBeVisible();
});

test('UC1: BR-01 rejected period explains the correction, then succeeds', async ({ page }) => {
  const name = 'e2e-create-fixed';
  await openAddCheck(page);
  const period = page.locator('#add-check-period');

  await period.fill('366');
  await period.press('Tab');
  const message = await period.evaluate((el) => el.validationMessage);
  expect(message).toContain('Must not exceed 365 days');
  await expect(page.locator('#add-check-modal')).toBeVisible();

  await period.fill('1');
  await period.press('Tab');
  expect(await period.evaluate((el) => el.validationMessage)).toBe('');
  await page.locator('#add-check-name').fill(name);
  await page.locator('#add-check-slug').fill('e2e-create-fixed');
  await page.locator('#add-check-submit').click();

  await expect(page.getByText(name, { exact: true }).first()).toBeVisible();
});

test('UC1: keyboard navigation reaches required fields and submits the form', async ({ page }) => {
  const name = 'e2e-keyboard';
  await openAddCheck(page);
  await page.locator('#add-check-name').fill(name);
  await page.locator('#add-check-slug').fill('e2e-keyboard');

  await page.locator('#add-check-name').click();
  const focusOrder = [];
  for (let i = 0; i < 30; i += 1) {
    const id = await page.evaluate(() => document.activeElement?.id || '');
    focusOrder.push(id);
    if (id === 'add-check-submit') break;
    await page.keyboard.press('Tab');
  }

  expect(focusOrder).toContain('add-check-name');
  expect(focusOrder).toContain('add-check-slug');
  expect(focusOrder.indexOf('add-check-period')).toBeLessThan(focusOrder.indexOf('add-check-grace'));
  expect(focusOrder).toContain('add-check-submit');

  await page.keyboard.press('Enter');
  await expect(page.getByText(name, { exact: true }).first()).toBeVisible();
});
