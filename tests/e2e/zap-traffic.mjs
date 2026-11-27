import { chromium } from '@playwright/test';

const browser = await chromium.launch({
  channel: 'chrome',
  headless: true,
  proxy: { server: 'http://127.0.0.1:8090' },
});
const context = await browser.newContext({ baseURL: 'http://127.0.0.1:8000', ignoreHTTPSErrors: true });
const page = await context.newPage();

await page.goto('/accounts/login/');
await page.locator('input[name="email"]').fill('owner@example.com');
await page.locator('input[name="password"]').fill('sqe-test-pass-2026');
await page.locator('button[type="submit"]').first().click();
await page.waitForURL(/\/projects\/.*\/checks\//);

await page.getByRole('button', { name: 'Add Check' }).first().click();
await page.locator('#add-check-name').fill('zap-passive-flow');
await page.locator('#add-check-slug').fill('zap-passive-flow');
await page.locator('#add-check-submit').click();
await page.getByText('zap-passive-flow', { exact: true }).first().waitFor();

await page.goto('/checks/600ffc66-7afa-5aac-9ecc-966d8a4de219/details/');
await page.locator('#resume-btn').click();
await page.locator('#pause-btn').click();
await page.locator('#resume-btn').waitFor();

await page.waitForTimeout(5000);
await browser.close();
console.log('ZAP proxied workflows complete');
