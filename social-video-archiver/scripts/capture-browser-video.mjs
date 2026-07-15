import { createHash } from 'node:crypto';
import { existsSync } from 'node:fs';
import { mkdir, readdir, rename, stat, unlink, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { basename, extname } from 'node:path';
import { spawn, spawnSync } from 'node:child_process';

const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require('playwright'));
} catch {
  console.error('Playwright is required. Set NODE_PATH to a Node modules directory containing playwright.');
  process.exit(3);
}

const targetUrl = process.argv[2];
const outputDir = process.argv[3] || 'downloads/social-videos';
const headless = process.env.HEADLESS !== '0';
const loginWaitMs = Number(process.env.LOGIN_WAIT_MS || 0);
const mediaWaitMs = Number(process.env.MEDIA_WAIT_MS || 25_000);
if (!targetUrl) {
  console.error('Usage: node capture-browser-video.mjs <video-url> [output-dir]');
  process.exit(2);
}

const chromePath = process.env.CHROME_PATH
  || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const executablePath = existsSync(chromePath) ? chromePath : undefined;
const userAgent = process.env.USER_AGENT
  || 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
  + '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

const platformRules = [
  {
    name: 'douyin',
    pageHosts: ['douyin.com', 'iesdouyin.com'],
    mediaHosts: [/douyinvod\.com$/i, /bytevdn\.com$/i, /bytedance\.com$/i],
    imageHosts: [/douyinpic\.com$/i, /byteimg\.com$/i],
  },
  {
    name: 'xiaohongshu',
    pageHosts: ['xiaohongshu.com', 'xhslink.com'],
    mediaHosts: [/xhscdn\.com$/i, /xhscdn\.net$/i],
    imageHosts: [/xhscdn\.com$/i, /xhscdn\.net$/i],
  },
];

function platformFor(url) {
  try {
    const host = new URL(url).hostname.toLowerCase();
    return platformRules.find(rule => rule.pageHosts
      .some(suffix => host === suffix || host.endsWith(`.${suffix}`)));
  } catch {
    return undefined;
  }
}

function isAllowedMedia(rule, url) {
  try {
    const host = new URL(url).hostname.toLowerCase();
    return rule.mediaHosts.some(pattern => pattern.test(host));
  } catch {
    return false;
  }
}

function isAllowedImage(rule, url) {
  try {
    const host = new URL(url).hostname.toLowerCase();
    return rule.imageHosts?.some(pattern => pattern.test(host));
  } catch {
    return false;
  }
}

function safeId(url, platform) {
  const parsed = new URL(url);
  const raw = basename(parsed.pathname).replace(/[^a-zA-Z0-9_-]/g, '');
  const hash = createHash('sha1').update(url).digest('hex').slice(0, 10);
  return `${platform}-${raw || hash}`;
}

function candidateScore(candidate) {
  const path = new URL(candidate.url).pathname.toLowerCase();
  const format = path.endsWith('.mp4') || /video\/mp4/i.test(candidate.contentType)
    ? 60
    : path.endsWith('.m3u8') || /mpegurl/i.test(candidate.contentType) ? 30 : 10;
  const origin = candidate.fromVideoElement ? 100 : 0;
  return origin + format + Math.min(candidate.contentLength || 0, 100_000_000) / 10_000_000;
}

function imageCandidateScore(candidate) {
  const area = (candidate.width || 0) * (candidate.height || 0);
  const origin = candidate.fromDom ? 1000 : 0;
  return origin + Math.min(area, 6_000_000) / 10_000
    + Math.min(candidate.contentLength || 0, 10_000_000) / 100_000;
}

function imageExtension(contentType, url) {
  const type = contentType.toLowerCase();
  if (/png/.test(type)) {
    return 'png';
  }
  if (/webp/.test(type)) {
    return 'webp';
  }
  if (/gif/.test(type)) {
    return 'gif';
  }
  const extension = extname(new URL(url).pathname).replace(/^\./, '').toLowerCase();
  if (['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(extension)) {
    return extension === 'jpeg' ? 'jpg' : extension;
  }
  return 'jpg';
}

function imageKey(url) {
  const parsed = new URL(url);
  return `${parsed.origin}${parsed.pathname}`;
}

function uniqueByFirst(items, keyFunction) {
  const found = new Map();
  for (const item of items) {
    const key = keyFunction(item);
    if (!found.has(key)) {
      found.set(key, item);
    }
  }
  return Array.from(found.values());
}

function isDouyinNotePage(url) {
  try {
    return platformFor(url)?.name === 'douyin' && new URL(url).pathname.startsWith('/note/');
  } catch {
    return false;
  }
}

function isPrimaryPostImage(rule, candidate) {
  if (rule.name !== 'douyin') {
    return true;
  }
  try {
    const parsed = new URL(candidate.url);
    const markerText = `${parsed.pathname} ${parsed.search}`;
    return /biz_tag=aweme_images|tplv-dy-aweme-images-v2|PackSourceEnum_AWEME_DETAIL/.test(markerText)
      && !/pcweb_cover|WEBPC_RELATED_AWEME|aweme-avatar/.test(markerText);
  } catch {
    return false;
  }
}

function hasFfmpeg() {
  return spawnSync('ffmpeg', ['-version'], { stdio: 'ignore' }).status === 0;
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
    throw new Error('ffmpeg is required to validate captured media.');
  }
  if (result.status !== 0) {
    throw new Error('Captured media failed full ffmpeg decode validation.');
  }
}

class NonVideoNoteError extends Error {}
class ExistingMediaError extends Error {}
class CompletedMediaError extends Error {}

async function downloadWithFfmpeg(mediaUrl, headers, outputPath) {
  const headerBlock = Object.entries(headers)
    .map(([name, value]) => `${name}: ${value}`)
    .join('\r\n') + '\r\n';

  await new Promise((resolve, reject) => {
    const child = spawn('ffmpeg', [
      '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
      '-headers', headerBlock,
      '-i', mediaUrl,
      '-c', 'copy',
      outputPath,
    ], { stdio: ['ignore', 'ignore', 'pipe'] });
    let errorText = '';
    child.stderr.on('data', chunk => {
      errorText += chunk.toString();
      if (errorText.length > 4000) {
        errorText = errorText.slice(-4000);
      }
    });
    child.on('error', reject);
    child.on('close', code => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`ffmpeg failed with exit code ${code}: ${errorText.trim()}`));
      }
    });
  });
}

async function hasExistingImageSet(directory, jsonPath) {
  if (!existsSync(directory) || !existsSync(jsonPath) || process.env.OVERWRITE === '1') {
    return false;
  }
  const files = await readdir(directory).catch(() => []);
  return files.some(file => /^\d{3}\.(?:jpe?g|png|webp|gif)$/i.test(file));
}

async function downloadImageSet(context, page, rule, id, pageInfo, imageCandidates) {
  const imageDir = `${outputDir}/${id}`;
  const jsonPath = `${imageDir}/${id}.json`;
  if (await hasExistingImageSet(imageDir, jsonPath)) {
    console.log(JSON.stringify({ event: 'skip-existing-image-set', platform: rule.name, id }));
    throw new ExistingMediaError();
  }

  await mkdir(imageDir, { recursive: true });
  const primaryCandidates = imageCandidates.filter(candidate => isPrimaryPostImage(rule, candidate));
  const sourceImages = primaryCandidates.length ? primaryCandidates : imageCandidates;
  const uniqueImages = uniqueByFirst(sourceImages
    .filter(candidate => /^https?:\/\//.test(candidate.url) && isAllowedImage(rule, candidate.url))
    .sort((a, b) => imageCandidateScore(b) - imageCandidateScore(a)), candidate => imageKey(candidate.url));

  if (!uniqueImages.length) {
    throw new Error('No downloadable image URLs were found for this image post.');
  }

  const downloaded = [];
  for (const [index, candidate] of uniqueImages.entries()) {
    const cookies = await context.cookies(candidate.url);
    const requestHeaders = {
      Referer: page.url(),
      'User-Agent': userAgent,
    };
    if (cookies.length) {
      requestHeaders.Cookie = cookies.map(cookie => `${cookie.name}=${cookie.value}`).join('; ');
    }

    const response = await context.request.get(candidate.url, {
      headers: requestHeaders,
      timeout: 120_000,
    });
    if (!response.ok()) {
      throw new Error(`Image download failed with HTTP ${response.status()}: ${candidate.url}`);
    }
    const body = await response.body();
    const contentType = response.headers()['content-type'] || candidate.contentType || '';
    if (!/^image\//i.test(contentType)) {
      throw new Error(`Image download returned unexpected content type: ${contentType || 'missing'}`);
    }
    if (body.length <= 1024) {
      throw new Error(`Image download returned an undersized file: ${body.length} bytes`);
    }

    const extension = imageExtension(contentType, candidate.url);
    const imagePath = `${imageDir}/${String(index + 1).padStart(3, '0')}.${extension}`;
    const temporaryPath = `${imagePath}.part`;
    await unlink(temporaryPath).catch(() => {});
    await writeFile(temporaryPath, body);
    await rename(temporaryPath, imagePath);
    downloaded.push({
      index: index + 1,
      path: imagePath,
      bytes: body.length,
      width: candidate.width || null,
      height: candidate.height || null,
    });
  }

  await writeFile(jsonPath, JSON.stringify({
    id,
    platform: rule.name,
    mediaType: 'image-set',
    requestedUrl: targetUrl,
    pageUrl: page.url(),
    title: pageInfo.title.replace(/\s+/g, ' ').trim(),
    imageCount: downloaded.length,
    images: downloaded,
  }, null, 2));

  console.log(JSON.stringify({
    event: 'downloaded-image-set',
    platform: rule.name,
    id,
    count: downloaded.length,
    output: imageDir,
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
  const candidates = [];
  const imageCandidates = [];

  page.on('response', response => {
    const url = response.url();
    const rule = platformFor(page.url()) || platformFor(targetUrl);
    if (!rule || response.status() >= 400) {
      return;
    }
    const headers = response.headers();
    const contentType = headers['content-type'] || '';
    const pathname = new URL(url).pathname.toLowerCase();
    if (isAllowedImage(rule, url) && (/^image\//i.test(contentType)
      || /\.(?:jpe?g|png|webp|gif)$/.test(pathname))) {
      imageCandidates.push({
        url,
        contentType,
        contentLength: Number(headers['content-length'] || 0),
        fromDom: false,
      });
      return;
    }
    if (!isAllowedMedia(rule, url)) {
      return;
    }
    if (!/^video\//i.test(contentType) && !/mpegurl/i.test(contentType)
      && !/\.(?:mp4|m3u8)$/.test(pathname)) {
      return;
    }
    if (/\.(?:m4s|ts)$/.test(pathname)) {
      return;
    }
    candidates.push({
      url,
      contentType,
      contentLength: Number(headers['content-length'] || 0),
      fromVideoElement: false,
    });
  });

  await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 45_000 });
  if (!headless && loginWaitMs > 0) {
    console.log(JSON.stringify({ event: 'login-wait', milliseconds: loginWaitMs }));
    await page.waitForTimeout(loginWaitMs);
  }
  await page.waitForTimeout(7_000);
  await page.waitForFunction(() => Array.from(document.querySelectorAll('video'))
    .some(video => video.currentSrc && video.readyState >= 1)
      || Array.from(document.querySelectorAll('main img, article img, [role="main"] img'))
        .some(image => image.naturalWidth >= 300 && image.naturalHeight >= 300),
  null, { timeout: mediaWaitMs }).catch(() => {});
  await page.waitForTimeout(4_000);

  const pageInfo = await page.evaluate(() => {
    const video = Array.from(document.querySelectorAll('video'))
      .find(item => item.currentSrc && item.readyState >= 1);
    const contentRoot = document.querySelector('main, article, [role="main"]') || document.body;
    const imageUrlsFromSourceSet = sourceSet => (sourceSet || '')
      .split(',')
      .map(item => item.trim().split(/\s+/)[0])
      .filter(Boolean);
    const normalizeUrl = value => {
      try {
        return new URL(value, location.href).href;
      } catch {
        return '';
      }
    };
    return {
      title: document.title,
      duration: Number.isFinite(video?.duration) ? video.duration : null,
      currentSrc: video?.currentSrc || '',
      hasVideoElement: Boolean(video),
      noteType: new URL(location.href).searchParams.get('type'),
      contentImageCount: Array.from(contentRoot?.querySelectorAll('img') || [])
        .filter(image => /(xhscdn\.(?:com|net)|douyinpic\.com|byteimg\.com)/i
          .test(image.currentSrc || image.src)
          && image.naturalWidth >= 300 && image.naturalHeight >= 300).length,
      images: Array.from(contentRoot?.querySelectorAll('img') || [])
        .flatMap(image => {
          const urls = [
            image.currentSrc,
            image.src,
            ...imageUrlsFromSourceSet(image.srcset),
            ...imageUrlsFromSourceSet(image.getAttribute('data-srcset')),
            image.getAttribute('data-src'),
          ].map(normalizeUrl).filter(Boolean);
          return urls.map(url => ({
            url,
            width: image.naturalWidth || image.width || null,
            height: image.naturalHeight || image.height || null,
            fromDom: true,
          }));
        })
        .filter(item => item.width >= 300 && item.height >= 300),
    };
  });
  imageCandidates.push(...pageInfo.images);

  const rule = platformFor(page.url()) || platformFor(targetUrl);
  if (!rule) {
    throw new Error('Unsupported page after redirect.');
  }
  const imageSetId = safeId(page.url(), rule.name);
  if (isDouyinNotePage(page.url()) && imageCandidates.some(candidate => isPrimaryPostImage(rule, candidate))) {
    await downloadImageSet(context, page, rule, imageSetId, pageInfo, imageCandidates);
    throw new CompletedMediaError();
  }
  if (/^https?:\/\//.test(pageInfo.currentSrc) && isAllowedMedia(rule, pageInfo.currentSrc)) {
    candidates.push({
      url: pageInfo.currentSrc,
      contentType: '',
      contentLength: 0,
      fromVideoElement: true,
    });
  }

  const unique = Array.from(new Map(candidates.map(item => [item.url, item])).values())
    .sort((a, b) => candidateScore(b) - candidateScore(a));
  const selected = unique[0];
  if (!selected) {
    if (rule.name === 'douyin' && pageInfo.contentImageCount > 0) {
      await downloadImageSet(context, page, rule, imageSetId, pageInfo, imageCandidates);
      throw new CompletedMediaError();
    }
    if (rule.name === 'xiaohongshu' && pageInfo.noteType === 'normal'
      && !pageInfo.hasVideoElement && pageInfo.contentImageCount > 0) {
      throw new NonVideoNoteError('The Xiaohongshu note contains images but no playable video.');
    }
    throw new Error('No playable media response was found. Login or a platform-specific update may be required.');
  }

  const id = safeId(page.url(), rule.name);
  const mp4Path = `${outputDir}/${id}.mp4`;
  const jsonPath = `${outputDir}/${id}.json`;
  if (existsSync(mp4Path) && existsSync(jsonPath) && process.env.OVERWRITE !== '1') {
    const existing = await stat(mp4Path);
    if (existing.size > 1024) {
      let validExisting = true;
      try {
        validateVideoFile(mp4Path);
      } catch {
        validExisting = false;
        console.error(JSON.stringify({ event: 'replace-invalid-existing', platform: rule.name, id }));
      }
      if (validExisting) {
        console.log(JSON.stringify({ event: 'skip-existing', platform: rule.name, id, bytes: existing.size }));
        throw new ExistingMediaError();
      }
    }
  }

  const cookies = await context.cookies(selected.url);
  const requestHeaders = {
    Referer: page.url(),
    'User-Agent': userAgent,
  };
  if (cookies.length) {
    requestHeaders.Cookie = cookies.map(cookie => `${cookie.name}=${cookie.value}`).join('; ');
  }

  const temporaryPath = `${mp4Path}.part.mp4`;
  await unlink(temporaryPath).catch(() => {});
  if (hasFfmpeg()) {
    await downloadWithFfmpeg(selected.url, requestHeaders, temporaryPath);
  } else if (!/m3u8|mpegurl/i.test(`${selected.url} ${selected.contentType}`)) {
    const response = await context.request.get(selected.url, {
      headers: requestHeaders,
      timeout: 120_000,
    });
    if (!response.ok()) {
      throw new Error(`Media request failed with HTTP ${response.status()}.`);
    }
    await writeFile(temporaryPath, await response.body());
  } else {
    throw new Error('ffmpeg is required for an HLS media response.');
  }

  const completed = await stat(temporaryPath);
  if (completed.size <= 1024) {
    throw new Error('Captured media is unexpectedly small.');
  }
  validateVideoFile(temporaryPath);
  await rename(temporaryPath, mp4Path);
  await writeFile(jsonPath, JSON.stringify({
    id,
    platform: rule.name,
    requestedUrl: targetUrl,
    pageUrl: page.url(),
    title: pageInfo.title.replace(/\s+/g, ' ').trim(),
    duration: pageInfo.duration,
    bytes: completed.size,
  }, null, 2));
  console.log(JSON.stringify({
    event: 'downloaded',
    platform: rule.name,
    id,
    bytes: completed.size,
    output: mp4Path,
  }));
} catch (error) {
  if (error instanceof NonVideoNoteError) {
    console.log(JSON.stringify({ event: 'skipped-non-video', reason: error.message }));
    process.exitCode = 4;
  } else if (!(error instanceof ExistingMediaError) && !(error instanceof CompletedMediaError)) {
    throw error;
  }
} finally {
  await browser.close();
}
