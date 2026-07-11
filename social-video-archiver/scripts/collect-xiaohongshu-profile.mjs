import { mkdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname } from 'node:path';

const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require('playwright'));
} catch {
  console.error('Playwright is required. Set NODE_PATH to a Node modules directory containing playwright.');
  process.exit(3);
}

const platform = 'xiaohongshu';
const profileUrl = process.argv[2];
const outputFile = process.argv[3];
const maxScrolls = Number(process.env.MAX_SCROLLS || 100);
const waitMs = Number(process.env.WAIT_MS || 1400);
const headless = process.env.HEADLESS !== '0';
const loginWaitMs = Number(process.env.LOGIN_WAIT_MS || 0);

if (!profileUrl || !outputFile) {
  console.error('Usage: node collect-xiaohongshu-profile.mjs <profile-url> <output-file>');
  process.exit(2);
}

const itemPattern = /^\/(?:explore|discovery\/item)\/[\da-f]+$/i;

const chromePath = process.env.CHROME_PATH
  || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const executablePath = existsSync(chromePath) ? chromePath : undefined;
const userAgent = process.env.USER_AGENT
  || 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
  + '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

function normalizeItemUrl(href, baseUrl) {
  try {
    const url = new URL(href, baseUrl);
    if (url.hostname !== 'xiaohongshu.com' && !url.hostname.endsWith('.xiaohongshu.com')) {
      return null;
    }
    if (!itemPattern.test(url.pathname)) {
      return null;
    }
    const normalized = new URL(`${url.origin}${url.pathname}`);
    for (const key of ['xsec_token', 'xsec_source', 'type']) {
      const value = url.searchParams.get(key);
      if (value && (key !== 'type' || ['normal', 'video'].includes(value))) {
        normalized.searchParams.set(key, value);
      }
    }
    return normalized.toString();
  } catch {
    return null;
  }
}

await mkdir(dirname(outputFile), { recursive: true });
const browser = await chromium.launch({ headless, executablePath });

try {
  const context = await browser.newContext({
    locale: 'zh-CN',
    userAgent,
    viewport: { width: 1365, height: 900 },
    storageState: process.env.PLAYWRIGHT_STORAGE_STATE || undefined,
  });
  const page = await context.newPage();
  await page.goto(profileUrl, { waitUntil: 'domcontentloaded', timeout: 45_000 });
  if (!headless && loginWaitMs > 0) {
    console.log(JSON.stringify({ event: 'login-wait', milliseconds: loginWaitMs }));
    await page.waitForTimeout(loginWaitMs);
  }
  await page.waitForTimeout(8_000);

  const found = new Map();
  let quietRounds = 0;
  let expectedCount = null;

  for (let i = 0; i < maxScrolls; i += 1) {
    const snapshot = await page.evaluate(() => {
      const text = document.body?.innerText || '';
      const countMatch = text.match(/(?:作品|视频)\s*[:：]?\s*(\d+)/);
      const preferredRoot = document.querySelector('main, [role="main"]');
      const preferredLinks = Array.from(preferredRoot?.querySelectorAll('a[href]') || [], a => a.href);
      const allLinks = Array.from(document.querySelectorAll('a[href]'), a => a.href);
      return {
        expectedCount: countMatch ? Number(countMatch[1]) : null,
        links: preferredLinks.length ? preferredLinks : allLinks,
      };
    });

    expectedCount ??= snapshot.expectedCount;
    const before = found.size;
    for (const href of snapshot.links) {
      const normalized = normalizeItemUrl(href, page.url());
      if (normalized) {
        found.set(new URL(normalized).pathname, normalized);
      }
    }

    quietRounds = found.size === before ? quietRounds + 1 : 0;
    if (found.size !== before) {
      console.log(JSON.stringify({ event: 'collected', platform, count: found.size }));
    }
    if ((expectedCount && found.size >= expectedCount) || quietRounds >= 8) {
      break;
    }

    await page.mouse.wheel(0, 2600);
    await page.waitForTimeout(waitMs);
  }

  const urls = Array.from(found.values());
  if (!urls.length) {
    throw new Error('No profile item links found. The page may require login or use a changed layout.');
  }

  await writeFile(outputFile, `${urls.join('\n')}\n`);
  await writeFile(`${outputFile}.json`, JSON.stringify({
    platform,
    requestedUrl: profileUrl,
    finalUrl: page.url(),
    expectedCount,
    collectedCount: urls.length,
  }, null, 2));
  console.log(JSON.stringify({
    event: 'profile-collected',
    platform,
    expectedCount,
    collectedCount: urls.length,
    outputFile,
  }));
} finally {
  await browser.close();
}
