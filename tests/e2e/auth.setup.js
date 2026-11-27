import { chromium } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';

export default async function globalSetup() {
  execFileSync('.venv/bin/python', ['scripts/seed.py'], {
    env: { ...process.env, SECRET_KEY: 'dummy-key' },
    stdio: 'ignore',
  });

  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const context = await browser.newContext({ baseURL: 'http://127.0.0.1:8000' });
  const page = await context.newPage();

  await page.goto('/accounts/login/');
  await page.locator('input[name="email"]').fill('owner@example.com');
  await page.locator('input[name="password"]').fill('sqe-test-pass-2026');
  await page.locator('button[type="submit"]').first().click();
  await page.waitForURL(/\/projects\/.*\/checks\//);

  fs.mkdirSync('tests/e2e/.auth', { recursive: true });
  await context.storageState({ path: 'tests/e2e/.auth/user.json' });
  await browser.close();
}
