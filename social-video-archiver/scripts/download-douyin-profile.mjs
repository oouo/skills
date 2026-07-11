import { mkdir, readFile, rename, stat, unlink, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { basename } from 'node:path';
import { spawnSync } from 'node:child_process';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const profileUrl = process.argv[2];
const outputDir = process.argv[3] || 'downloads/douyin-profile';
const maxScrolls = Number(process.env.MAX_SCROLLS || 80);
const waitMs = Number(process.env.WAIT_MS || 1800);
const collectOnly = process.env.COLLECT_ONLY === '1';
const limit = Number(process.env.LIMIT || 0);
const profileMarker = process.env.PROFILE_MARKER || '';
const videoListFile = process.env.VIDEO_LIST_FILE || '';
const headless = process.env.HEADLESS !== '0';
const loginWaitMs = Number(process.env.LOGIN_WAIT_MS || 0);

if (!profileUrl) {
  console.error('Usage: node download-douyin-profile.mjs <douyin-profile-url> [output-dir]');
  process.exit(2);
}

const systemChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const executablePath = process.env.CHROME_PATH
  || (existsSync(systemChromePath) ? systemChromePath : undefined);
const userAgent =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
  + '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

function videoIdFromUrl(url) {
  return url.match(/\/video\/(\d+)/)?.[1] || basename(new URL(url).pathname);
}

function cleanTitle(title) {
  return (title || '')
    .replace(/\s+-\s+抖音\s*$/, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function validateVideoFile(path) {
  const result = spawnSync('ffmpeg', [
    '-v', 'error',
    '-xerror',
    '-i', path,
    '-map', '0:v:0',
    '-f', 'null',
    '-',
  ], { stdio: 'ignore' });
  if (result.error?.code === 'ENOENT') {
    throw new Error('ffmpeg is required to validate downloaded media.');
  }
  if (result.status !== 0) {
    throw new Error('Downloaded media failed full ffmpeg decode validation.');
  }
}

async function collectVideoUrls(page) {
  const found = new Map();
  let quietRounds = 0;

  for (let i = 0; i < maxScrolls; i += 1) {
    const { urls, expectedCount } = await page.evaluate(() => {
      const bodyText = document.body?.innerText || '';
      const worksMatch = bodyText.match(/作品\s+(\d+)\s+推荐\s+喜欢/);
      const start = bodyText.indexOf('最新作品');
      const end = start >= 0 ? bodyText.indexOf('暂时没有更多了', start) : -1;
      const worksText = start >= 0 ? bodyText.slice(start, end >= 0 ? end : bodyText.length) : '';
      const urls = Array.from(document.querySelectorAll('a[href]'), anchor => ({
        href: anchor.href,
        text: anchor.innerText.trim(),
      }))
        .map(anchor => {
          const normalizedText = anchor.text.replace(/\s+/g, ' ').trim();
          if (!normalizedText || !worksText.replace(/\s+/g, ' ').includes(normalizedText)) {
            return null;
          }
          const url = new URL(anchor.href, location.href);
          if (
            url.hostname !== 'www.douyin.com'
            || !/^\/video\/\d+$/.test(url.pathname)
            || url.searchParams.has('source')
          ) {
            return null;
          }
          return `${url.origin}${url.pathname}`;
        })
        .filter(Boolean);
      return {
        urls,
        expectedCount: worksMatch ? Number(worksMatch[1]) : null,
      };
    });

    const before = found.size;
    for (const url of urls) {
      found.set(videoIdFromUrl(url), url);
    }

    if (found.size === before) {
      quietRounds += 1;
    } else {
      quietRounds = 0;
      console.log(JSON.stringify({ event: 'collected', count: found.size }));
    }

    if (quietRounds >= 6) {
      break;
    }
    if (expectedCount && found.size >= expectedCount) {
      break;
    }

    await page.mouse.wheel(0, 2600);
    await page.waitForTimeout(waitMs);
  }

  return Array.from(found.values());
}

async function getVideoSource(page, videoPageUrl) {
  const resourceUrls = [];
  const onResponse = response => {
    const url = response.url();
    const contentType = response.headers()['content-type'] || '';
    if (
      response.status() < 400
      && (/video\/mp4/i.test(contentType) || /douyinvod\.com|bytevdn\.com|bytedance.*video/i.test(url))
    ) {
      resourceUrls.push(url);
    }
  };

  page.on('response', onResponse);
  await page.goto(videoPageUrl, { waitUntil: 'domcontentloaded', timeout: 45_000 });
  await page.waitForTimeout(6_000);
  try {
    await page.waitForFunction(() => Array.from(document.querySelectorAll('video'))
      .some(video => video.currentSrc && video.readyState >= 1), null, { timeout: 35_000 });
    await page.waitForTimeout(2_000);

    const source = await page.evaluate(() => {
      const video = Array.from(document.querySelectorAll('video'))
        .find(item => item.currentSrc && item.readyState >= 1);
      return {
        pageUrl: location.href,
        title: document.title,
        videoUrl: video?.currentSrc || '',
        duration: Number.isFinite(video?.duration) ? video.duration : null,
      };
    });

    return {
      ...source,
      videoResourceUrl: resourceUrls[0] || '',
    };
  } finally {
    page.off('response', onResponse);
  }
}

async function downloadVideo(context, page, videoPageUrl, index, total) {
  const videoId = videoIdFromUrl(videoPageUrl);
  const mp4Path = `${outputDir}/${videoId}.mp4`;
  const jsonPath = `${outputDir}/${videoId}.json`;

  if (existsSync(mp4Path) && existsSync(jsonPath)) {
    const existing = await stat(mp4Path);
    if (existing.size > 1024) {
      try {
        validateVideoFile(mp4Path);
        console.log(JSON.stringify({ event: 'skip-existing', index, total, videoId, bytes: existing.size }));
        return;
      } catch {
        console.error(JSON.stringify({ event: 'replace-invalid-existing', index, total, videoId }));
      }
    }
  }

  const source = await getVideoSource(page, videoPageUrl);
  const downloadableUrl = source.videoUrl?.startsWith('blob:')
    ? source.videoResourceUrl
    : source.videoUrl || source.videoResourceUrl;

  if (!downloadableUrl) {
    throw new Error(`No playable video source found for ${videoPageUrl}`);
  }

  const response = await context.request.get(downloadableUrl, {
    headers: {
      referer: source.pageUrl,
      'user-agent': userAgent,
    },
    timeout: 120_000,
  });

  if (!response.ok()) {
    throw new Error(`Video download failed for ${videoId}: HTTP ${response.status()}`);
  }

  const body = await response.body();
  const contentType = response.headers()['content-type'] || '';
  if (!/^video\//i.test(contentType) && !/octet-stream/i.test(contentType)) {
    throw new Error(`Video download returned unexpected content type for ${videoId}: ${contentType || 'missing'}`);
  }
  if (body.length <= 1024) {
    throw new Error(`Video download returned an undersized file for ${videoId}: ${body.length} bytes`);
  }

  const temporaryPath = `${mp4Path}.part`;
  await unlink(temporaryPath).catch(() => {});
  await writeFile(temporaryPath, body);
  validateVideoFile(temporaryPath);
  await rename(temporaryPath, mp4Path);
  await writeFile(jsonPath, JSON.stringify({
    id: videoId,
    pageUrl: source.pageUrl,
    title: cleanTitle(source.title),
    duration: source.duration,
    bytes: body.length,
  }, null, 2));

  console.log(JSON.stringify({
    event: 'downloaded',
    index,
    total,
    videoId,
    bytes: body.length,
    title: cleanTitle(source.title),
  }));
}

await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ headless, executablePath });

try {
  const context = await browser.newContext({
    locale: 'zh-CN',
    userAgent,
    viewport: { width: 1365, height: 900 },
    storageState: process.env.PLAYWRIGHT_STORAGE_STATE || undefined,
  });
  const page = await context.newPage();

  let videoUrls;
  if (videoListFile) {
    videoUrls = (await readFile(videoListFile, 'utf8')).split(/\r?\n/).map(line => line.trim()).filter(Boolean);
  } else {
    await page.goto(profileUrl, { waitUntil: 'domcontentloaded', timeout: 45_000 });
    if (!headless && loginWaitMs > 0) {
      console.log(JSON.stringify({ event: 'login-wait', milliseconds: loginWaitMs }));
      await page.waitForTimeout(loginWaitMs);
    }
    await page.waitForTimeout(8_000);
    await page.waitForFunction(marker => {
      const text = document.body?.innerText || '';
      return (!marker || text.includes(marker)) && text.includes('最新作品');
    }, profileMarker, { timeout: 30_000 }).catch(() => {});
    await page.waitForFunction(() => Array.from(document.querySelectorAll('a[href]'))
      .some(anchor => {
        const text = anchor.innerText.trim();
        if (!text) {
          return false;
        }
        const url = new URL(anchor.href, location.href);
        return url.hostname === 'www.douyin.com'
          && /^\/video\/\d+$/.test(url.pathname)
          && !url.searchParams.has('source');
      }), null, { timeout: 30_000 }).catch(() => {});

    const visibleText = await page.locator('body').innerText({ timeout: 10_000 }).catch(() => '');
    if (/登录后即可搜索更多精彩视频|扫码登录/.test(visibleText) && /search/.test(page.url())) {
      throw new Error('Douyin search requires login. Please provide the direct profile URL.');
    }

    videoUrls = await collectVideoUrls(page);
  }
  await writeFile(`${outputDir}/video-urls.txt`, `${videoUrls.join('\n')}\n`);

  console.log(JSON.stringify({
    event: 'profile-collected',
    profileUrl: page.url(),
    total: videoUrls.length,
    listPath: `${outputDir}/video-urls.txt`,
  }));

  if (!videoUrls.length) {
    throw new Error('No video URLs found. The profile may be private, empty, or require login.');
  }

  if (!collectOnly) {
    const failures = [];
    const selectedUrls = limit > 0 ? videoUrls.slice(0, limit) : videoUrls;
    for (const [i, url] of selectedUrls.entries()) {
      try {
        await downloadVideo(context, page, url, i + 1, selectedUrls.length);
      } catch (error) {
        failures.push({
          url,
          index: i + 1,
          error: error.message,
        });
        console.error(JSON.stringify({
          event: 'failed',
          index: i + 1,
          total: selectedUrls.length,
          videoId: videoIdFromUrl(url),
          error: error.message,
        }));
      }
      await page.waitForTimeout(900);
    }

    if (failures.length) {
      await writeFile(`${outputDir}/failed.json`, JSON.stringify(failures, null, 2));
      process.exitCode = 1;
    } else {
      await unlink(`${outputDir}/failed.json`).catch(() => {});
    }
  }
} finally {
  await browser.close();
}
