import lighthouse from 'lighthouse';
import { launch } from 'chrome-launcher';
import fs from 'node:fs';

const label = process.argv[2] || 'before';
const CHECK_CODE = '600ffc66-7afa-5aac-9ecc-966d8a4de219';
const screens = {
  checks: 'http://127.0.0.1:8000/projects/01c63086-9307-41ec-9223-1c8073f232b2/checks/',
  details: `http://127.0.0.1:8000/checks/${CHECK_CODE}/details/`,
};

const storage = JSON.parse(fs.readFileSync('tests/e2e/.auth/user.json', 'utf8'));
const cookie = storage.cookies.map((c) => `${c.name}=${c.value}`).join('; ');

fs.mkdirSync('evidence/phase9', { recursive: true });
const chrome = await launch({
  chromePath: '/usr/bin/google-chrome',
  chromeFlags: ['--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
});

const summary = [`# Lighthouse report (${label})`, '', '| Screen | Accessibility | Best practices | SEO |', '|---|---|---|---|'];
try {
  for (const [name, url] of Object.entries(screens)) {
    const result = await lighthouse(url, {
      port: chrome.port,
      output: 'json',
      logLevel: 'error',
      onlyCategories: ['accessibility', 'best-practices', 'seo'],
      extraHeaders: { cookie },
      formFactor: 'desktop',
      screenEmulation: { mobile: false, width: 1280, height: 800, deviceScaleFactor: 1, disabled: false },
    });
    fs.writeFileSync(`evidence/phase9/lighthouse-${label}-${name}.json`, result.report);
    const report = JSON.parse(result.report);
    const score = (key) => Math.round((report.categories[key]?.score ?? 0) * 100);
    summary.push(`| ${name} | ${score('accessibility')} | ${score('best-practices')} | ${score('seo')} |`);

    const audits = Object.values(report.audits)
      .filter((a) => a.score !== null && a.score < 1 && a.scoreDisplayMode !== 'informative')
      .map((a) => `- ${a.id} (${Math.round((a.score ?? 0) * 100)}): ${a.title}`);
    fs.writeFileSync(`evidence/phase9/lighthouse-${label}-${name}.md`, [`# Lighthouse: ${name} (${label})`, '', `URL: ${url}`, '', ...audits].join('\n') + '\n');
  }
} finally {
  await chrome.kill();
}

fs.writeFileSync(`evidence/phase9/lighthouse-${label}-summary.md`, `${summary.join('\n')}\n`);
console.log(summary.join('\n'));
