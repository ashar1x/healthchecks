import { test, expect } from '@playwright/test';
import fs from 'node:fs';

test.use({ storageState: 'tests/e2e/.auth/user.json' });

const CHECK_CODE = 'bf225b09-ae43-5e8d-9df9-d8fdcf7ad0ad';
const RW_KEY = 'hcw_A1b2C3d4E5f6G7h8I9j0K1l2M3n4';
const RO_KEY = 'hcr_Z9y8X7w6V5u4T3s2R1q0P9o8N7m6';

test('access matrix: two roles across both workflows', async ({ page, browser, request }) => {
  const decisions = [];
  const before = await request.get('/api/v3/checks/', { headers: { 'X-Api-Key': RW_KEY } });
  const target = (await before.json()).checks.find((item) => item.name === 'seed-up');
  if (target.status === 'paused') {
    await request.post(`/api/v3/checks/${CHECK_CODE}/resume`, { headers: { 'X-Api-Key': RW_KEY }, data: '' });
  }

  await page.goto('/');
  await page.getByRole('link', { name: /SQE Test Project/ }).first().click();
  const ownerAddVisible = await page.getByRole('button', { name: 'Add Check' }).first().isVisible();
  decisions.push({ role: 'owner (rw)', surface: 'dashboard', action: 'open Add Check', expected: 'allowed', observed: ownerAddVisible ? 'allowed' : 'denied', passed: ownerAddVisible });
  expect(ownerAddVisible).toBe(true);

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
  await roPage.locator('#checks-table').waitFor({ state: 'visible' });
  const roAddCount = await roPage.getByRole('button', { name: 'Add Check' }).count();
  decisions.push({ role: 'read-only member', surface: 'dashboard', action: 'open Add Check', expected: 'denied', observed: roAddCount === 0 ? 'denied' : 'allowed', passed: roAddCount === 0 });
  expect(roAddCount).toBe(0);

  const rwResponse = await request.post(`/api/v3/checks/${CHECK_CODE}/pause`, { headers: { 'X-Api-Key': RW_KEY }, data: '' });
  decisions.push({ role: 'rw API key', surface: 'API', action: 'pause check', expected: '200', observed: String(rwResponse.status()), passed: rwResponse.status() === 200 });
  expect(rwResponse.status()).toBe(200);

  const roResponse = await request.post(`/api/v3/checks/${CHECK_CODE}/pause`, { headers: { 'X-Api-Key': RO_KEY }, data: '' });
  decisions.push({ role: 'ro API key', surface: 'API', action: 'pause check', expected: '401', observed: String(roResponse.status()), passed: roResponse.status() === 401 });
  expect(roResponse.status()).toBe(401);

  await roPage.goto(`/checks/${CHECK_CODE}/details/`);
  const pauseCount = await roPage.locator('#pause-btn').count();
  decisions.push({ role: 'read-only member', surface: 'dashboard', action: 'pause check button', expected: 'denied', observed: pauseCount === 0 ? 'denied' : 'allowed', passed: pauseCount === 0 });
  expect(pauseCount).toBe(0);

  await roContext.close();

  fs.mkdirSync('evidence/security', { recursive: true });
  fs.writeFileSync('evidence/security/access-matrix.json', JSON.stringify(decisions, null, 2) + '\n');
  const lines = ['# Access decisions (Playwright)', '', '| Role | Surface | Action | Expected | Observed | Result |', '|---|---|---|---|---|---|'];
  for (const d of decisions) lines.push(`| ${d.role} | ${d.surface} | ${d.action} | ${d.expected} | ${d.observed} | ${d.passed ? 'PASS' : 'FAIL'} |`);
  fs.writeFileSync('evidence/security/access-matrix.md', `${lines.join('\n')}\n`);
});
