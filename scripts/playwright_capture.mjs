import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';

const ROOT = '/Users/nathanbrown-bennett/Documents/Abokar/mentra';
const mediaDir = path.join(ROOT, 'docs', 'media');
const videoDir = path.join(mediaDir, 'playwright-video');
fs.mkdirSync(mediaDir, { recursive: true });
fs.mkdirSync(videoDir, { recursive: true });

const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:3000';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: {
    dir: videoDir,
    size: { width: 1280, height: 720 },
  },
});

const page = await context.newPage();
const video = page.video();

try {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle', timeout: 60000 });
  await page.screenshot({ path: path.join(mediaDir, '01-login-page.png'), fullPage: true });

  await page.fill('input[type="text"]', 'caseystudent@example.com');
  await page.fill('input[type="password"]', 'password123');
  await page.click('button[type="submit"]');

  await page.waitForURL('**/dashboard', { timeout: 20000 });
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(mediaDir, '02-dashboard-page.png'), fullPage: true });

  await page.getByRole('button', { name: 'Logout' }).hover();
  await page.getByRole('link', { name: 'Progress' }).click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(mediaDir, '03-progress-page.png'), fullPage: true });

  await page.getByRole('link', { name: 'Communities' }).click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(mediaDir, '04-communities-page.png'), fullPage: true });

  await page.getByRole('link', { name: 'Profile' }).click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(mediaDir, '05-profile-page.png'), fullPage: true });

  await page.getByRole('link', { name: 'Dashboard' }).click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);

  const practiceButton = page.getByRole('button', { name: 'Practice' }).first();
  await practiceButton.click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(mediaDir, '06-learning-page.png'), fullPage: true });

  const firstOption = page.locator('input[type="radio"]').first();
  if (await firstOption.count()) {
    await firstOption.check();
    await page.getByRole('button', { name: 'Submit Answer' }).click();
    await page.waitForTimeout(1600);
    await page.screenshot({ path: path.join(mediaDir, '07-feedback-page.png'), fullPage: true });
  }

  await page.getByRole('button', { name: /Next Question|Switch to next-best topic/ }).first().click().catch(() => {});
  await page.waitForTimeout(1000);
} finally {
  await context.close();
  await browser.close();
}

const recordedVideoPath = await video?.path();
if (recordedVideoPath) {
  console.log(`Playwright capture completed. Video saved to ${recordedVideoPath}`);
} else {
  console.log('Playwright capture completed. Video was not available.');
}
