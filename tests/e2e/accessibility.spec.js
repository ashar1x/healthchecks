import { test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';

test.use({ storageState: 'tests/e2e/.auth/user.json' });

const label = process.env.AXE_LABEL || 'after';
const CHECK_CODE = '600ffc66-7afa-5aac-9ecc-966d8a4de219';

const screens = [
  ['checks', async (page) => { await page.goto('/'); await page.getByRole('link', { name: /SQE Test Project/ }).first().click(); }],
  ['add-check-modal', async (page) => {
    await page.goto('/');
    await page.getByRole('link', { name: /SQE Test Project/ }).first().click();
    await page.getByRole('button', { name: 'Add Check' }).first().click();
    await page.locator('#add-check-modal').waitFor({ state: 'visible' });
  }],
  ['details', async (page) => { await page.goto(`/checks/${CHECK_CODE}/details/`); }],
];

for (const [name, prepare] of screens) {
  test(`axe full scan: ${name} (${label})`, async ({ page }) => {
    await prepare(page);
    const results = await new AxeBuilder({ page }).analyze();

    fs.mkdirSync('evidence/phase9', { recursive: true });
    fs.writeFileSync(`evidence/phase9/axe-${label}-${name}.json`, JSON.stringify(results, null, 2));

    const lines = [`# axe-core scan: ${name} (${label})`, '', `URL: ${page.url()}`, `Violations: ${results.violations.length}`, `Passes: ${results.passes.length}`, ''];
    for (const violation of results.violations) {
      lines.push(`- **${violation.id}** (${violation.impact}) — ${violation.help}; nodes: ${violation.nodes.length}`);
    }
    if (results.violations.length === 0) lines.push('No violations detected.');
    fs.writeFileSync(`evidence/phase9/axe-${label}-${name}.md`, `${lines.join('\n')}\n`);
  });
}
