import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'evidence/phase9/playwright-report', open: 'never' }],
  ],
  globalSetup: './tests/e2e/auth.setup.js',
  use: {
    baseURL: 'http://127.0.0.1:8000',
    channel: 'chrome',
    headless: true,
    viewport: { width: 1280, height: 800 },
    trace: 'off',
  },
  webServer: {
    command: 'bash scripts/start.sh',
    url: 'http://127.0.0.1:8000/accounts/login/',
    reuseExistingServer: true,
    timeout: 120_000,
    env: { SECRET_KEY: 'dummy-key', ALLOWED_HOSTS: '127.0.0.1,localhost' },
  },
});
