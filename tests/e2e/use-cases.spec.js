import { test, expect } from '@playwright/test';

test.use({ storageState: 'tests/e2e/.auth/user.json' });

const RW_KEY = 'hcw_A1b2C3d4E5f6G7h8I9j0K1l2M3n4';
const UP_CODE = 'bf225b09-ae43-5e8d-9df9-d8fdcf7ad0ad';
const NEW_CODE = '9290bc20-a556-5aa9-a24d-7d0053ea9754';

async function openAddCheck(page) {
  await page.goto('/');
  await page.getByRole('link', { name: /SQE Test Project/ }).first().click();
  await page.getByRole('button', { name: 'Add Check' }).first().click();
  await page.locator('#add-check-modal').waitFor({ state: 'visible' });
}

test('UC1 alt: cron schedule check is created and read back', async ({ page, request }) => {
  const name = 'e2e-cron';
  await openAddCheck(page);
  await page.locator('#add-check-name').fill(name);
  await page.locator('#add-check-modal input[name="kind"][value="cron"]').check();
  await page.locator('#add-check-schedule').fill('*/5 * * * *');
  await page.locator('#add-check-submit').click();
  await page.getByText(name, { exact: true }).first().waitFor();

  const response = await request.get('/api/v3/checks/', { headers: { 'X-Api-Key': RW_KEY } });
  const check = (await response.json()).checks.find((item) => item.name === name);
  expect(check.schedule).toBe('*/5 * * * *');
});

test('UC1 alt: suggested slug is accepted', async ({ page }) => {
  const name = 'e2e-suggested-slug';
  await openAddCheck(page);
  await page.locator('#add-check-name').fill(name);
  await page.locator('#add-check-name').press('Tab');
  await page.locator('#add-check-modal .use-suggested-slug').click();
  const slug = await page.locator('#add-check-slug').inputValue();
  expect(slug.length).toBeGreaterThan(0);
  await page.locator('#add-check-submit').click();
  await page.getByText(name, { exact: true }).first().waitFor();
});

test('UC1 exception: out-of-range timeout is rejected by the API', async ({ request }) => {
  const response = await request.post('/api/v3/checks/', {
    headers: { 'X-Api-Key': RW_KEY, 'Content-Type': 'application/json' },
    data: JSON.stringify({ name: 'e2e-invalid', timeout: 59, grace: 60 }),
  });
  expect(response.status()).toBe(400);
});

test('UC2 alt: pause is idempotent and the button becomes disabled', async ({ page, request }) => {
  const url = `/api/v3/checks/${UP_CODE}/pause`;
  const first = await request.post(url, { headers: { 'X-Api-Key': RW_KEY }, data: '' });
  const second = await request.post(url, { headers: { 'X-Api-Key': RW_KEY }, data: '' });
  expect(first.status()).toBe(200);
  expect(second.status()).toBe(200);

  await page.goto(`/checks/${UP_CODE}/details/`);
  await expect(page.locator('#pause-btn')).toBeDisabled();
  await expect(page.locator('#current-status-text')).toContainText('This check is paused.');
});

test('UC2 exception: resume of a non-paused check returns 409', async ({ request }) => {
  const url = `/api/v3/checks/${NEW_CODE}/resume`;
  const response = await request.post(url, { headers: { 'X-Api-Key': RW_KEY }, data: '' });
  expect(response.status()).toBe(409);
  expect(await response.text()).toContain('check is not paused');
});
