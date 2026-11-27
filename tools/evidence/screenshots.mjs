import { chromium } from '@playwright/test';
import fs from 'node:fs';

fs.mkdirSync('evidence/screenshots', { recursive: true });
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const ownerContext = await browser.newContext({
  baseURL: 'http://127.0.0.1:8000',
  storageState: 'tests/e2e/.auth/user.json',
});
const page = await ownerContext.newPage();

await page.goto('/');
await page.getByRole('link', { name: /SQE Test Project/ }).first().click();
await page.screenshot({ path: 'evidence/screenshots/a11y-checks-after.png' });

await page.getByRole('button', { name: 'Add Check' }).first().click();
await page.locator('#add-check-name').fill('screenshot-check');
await page.locator('#add-check-slug').fill('screenshot-check');
await page.locator('#add-check-submit').click();
await page.getByText('screenshot-check', { exact: true }).first().waitFor();
await page.screenshot({ path: 'evidence/screenshots/check-created.png' });

await page.getByRole('button', { name: 'Add Check' }).first().click();
const period = page.locator('#add-check-period');
await period.fill('366');
await period.press('Tab');
const validationMessage = await period.evaluate((element) => element.validationMessage);
fs.writeFileSync('evidence/screenshots/br01-validation.txt', `${validationMessage}\n`);
await page.screenshot({ path: 'evidence/screenshots/br01-rejection.png' });

await page.goto('/checks/600ffc66-7afa-5aac-9ecc-966d8a4de219/details/');
await page.screenshot({ path: 'evidence/screenshots/a11y-details-after.png' });
await ownerContext.close();

const roContext = await browser.newContext({
  baseURL: 'http://127.0.0.1:8000',
  storageState: { cookies: [], origins: [] },
});
const roPage = await roContext.newPage();
await roPage.goto('/accounts/login/');
await roPage.locator('input[name="email"]').fill('member-ro@example.com');
await roPage.locator('input[name="password"]').fill('sqe-test-pass-2026');
await roPage.locator('button[type="submit"]').first().click();
await roPage.getByRole('link', { name: /SQE Test Project/ }).first().click();
await roPage.screenshot({ path: 'evidence/screenshots/access-denied.png' });
await roContext.close();
await browser.close();
console.log('screenshots written');
