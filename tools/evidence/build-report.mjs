import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from '@playwright/test';

const root = process.cwd();
const htmlPath = path.join(root, 'report', 'final-report.html');
const pdfPath = path.resolve(root, '..', 'Project_24I-3072_24I-3052_24I-3102_C.pdf');

execFileSync('pandoc', ['-f', 'markdown', '-t', 'html5', '--standalone', '-o', htmlPath, 'report/final-report.md'], { cwd: root });

const cover = `<div class="cover"><h1>SE3002 Software Quality Engineering</h1><h2>Final Project Report</h2><p>Ashar Ahmed (24i-3072) &middot; Taimoor Khaliq (24i-3052) &middot; Ali Haider (24i-3102)</p><p>Section C &middot; 29 November 2026</p><p>https://github.com/ashar1x/healthchecks</p></div>`;
const style = `<style>@page{size:A4;margin:18mm}body{font-family:Arial,sans-serif;font-size:10pt;line-height:1.35}h1,h2{color:#174a7e}table{border-collapse:collapse;width:100%;font-size:8.5pt}th,td{border:1px solid #999;padding:3px 5px;vertical-align:top}th{background:#e8eef5}.cover{page-break-after:always;text-align:center;padding-top:60mm}.cover h1{font-size:24pt}.cover h2{font-size:18pt}a{color:#174a7e}</style>`;
let html = fs.readFileSync(htmlPath, 'utf8');
html = html.replace('</head>', `${style}</head>`).replace(/<body[^>]*>/, (match) => `${match}${cover}`);
fs.writeFileSync(htmlPath, html);

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage();
await page.setContent(html, { waitUntil: 'load' });
await page.pdf({ path: pdfPath, format: 'A4', printBackground: true });
await browser.close();
console.log(`PDF: ${pdfPath}`);
