import { test, expect } from '@playwright/test';

test.use({ storageState: 'tests/e2e/.auth/user.json' });

const CHECK_CODE = '600ffc66-7afa-5aac-9ecc-966d8a4de219';
const API_KEY = 'hcw_A1b2C3d4E5f6G7h8I9j0K1l2M3n4';

test('UC2: resume a paused check, then pause it again and verify the postcondition', async ({ page, request }) => {
  const status = page.locator('#current-status-text');
  await page.goto(`/checks/${CHECK_CODE}/details/`);

  await expect(status).toContainText('This check is paused, and will ignore pings until resumed.');
  await page.locator('#resume-btn').click();
  await expect(status).toContainText('This check is ready for pings.');
  await expect(page.locator('#pause-btn')).toBeEnabled();

  await page.locator('#pause-btn').click();
  await expect(status).toContainText('This check is paused, and will ignore pings until resumed.');
  await expect(page.locator('#resume-btn')).toBeVisible();

  const response = await request.get('/api/v3/checks/', { headers: { 'X-Api-Key': API_KEY } });
  expect(response.ok()).toBeTruthy();
  const checks = (await response.json()).checks;
  const check = checks.find((item) => item.name === 'seed-paused-manual');
  expect(check.status).toBe('paused');
});
