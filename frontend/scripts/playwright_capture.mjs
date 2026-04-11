import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';

const ROOT = path.resolve(process.cwd(), '..');
const mediaDir = path.join(ROOT, 'docs', 'media');
fs.mkdirSync(mediaDir, { recursive: true });

const frontendUrl = process.env.FRONTEND_URL || 'http://127.0.0.1:5173';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: {
    dir: mediaDir,
    size: { width: 1280, height: 720 },
  },
});

const page = await context.newPage();

try {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle', timeout: 60000 });
  await page.screenshot({ path: path.join(mediaDir, '01-login-page.png'), fullPage: true });

  await page.fill('input[type="email"]', 'student@example.com');
  await page.fill('input[type="password"]', 'testpass123');
  await page.click('button[type="submit"]');

  await page.waitForURL('**/dashboard', { timeout: 20000 });
  await page.waitForTimeout(1800);
  await page.screenshot({ path: path.join(mediaDir, '02-dashboard-page.png'), fullPage: true });

  await page.goto(`${frontendUrl}/progress`, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(mediaDir, '03-progress-page.png'), fullPage: true });

  await page.goto(`${frontendUrl}/learn/1`, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(mediaDir, '04-learning-page.png'), fullPage: true });

  const videoPath = await page.video().path();
  const targetVideoPath = path.join(mediaDir, '05-app-demo.webm');
  fs.copyFileSync(videoPath, targetVideoPath);
  console.log(`Saved video: ${targetVideoPath}`);
} finally {
  await context.close();
  await browser.close();
}

console.log('Playwright capture completed. Media saved to docs/media');
