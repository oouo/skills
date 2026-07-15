---
name: social-video-archiver
description: >
  Use when downloading or archiving authorized videos or image posts from Douyin,
  Xiaohongshu, or YouTube. Covers single posts, profiles, channels,
  playlists, metadata, resumable downloads, and browser fallbacks.
---

# Social Video Archiver

## Overview

Treat each download as a resumable archive: establish the access boundary,
select the platform branch, preserve metadata, and verify every collected item.

## When to Use

Use this skill when the user wants to:

- download one authorized video from a supported platform
- download one authorized Douyin image post
- archive public videos from an owned or authorized profile
- back up a YouTube channel, playlist, or Shorts collection
- resume a partial social-video archive without downloading duplicates

Do not use this skill to bypass DRM, paywalls, private-account permissions, or
platform access controls.

## Instructions

### 1. Establish the Boundary

- Identify the target URL, single-item or profile scope, output directory, and
  authorization status.
- Resolve the absolute skill directory containing this `SKILL.md`; use it for
  every bundled-script command.
- Accept an ownership or permission statement the user already provided. Do not
  ask for it twice.
- Explain that profile downloads cover items visible to the authorized web
  session. Drafts and app-only private items require an official export or a
  separately authorized session.
- Request browser authentication only when public access is insufficient.

Completion criterion: platform, scope, output directory, and authorization are
all known.

### 2. Select the Platform Branch

Read only the target platform section in
[`references/platforms.md`](references/platforms.md). Verify extractor support
at runtime, then dry-run the unified entry point:

```bash
SKILL_DIR='<absolute path to social-video-archiver>'
DRY_RUN=1 "$SKILL_DIR/scripts/download-social.sh" '<url>' '<output-dir>'
```

Use these optional environment variables when required:

| Variable | Purpose |
| --- | --- |
| `MODE=single` or `MODE=profile` | Override URL-based scope detection. |
| `YTDLP_BIN=/path/to/yt-dlp` | Select the `yt-dlp` executable. |
| `NODE_BIN=/path/to/node` | Select the Node.js executable. |
| `BROWSER_COOKIES=chrome` | Let `yt-dlp` read an authorized browser session. |
| `COOKIES_FILE=/path/cookies.txt` | Supply an authorized Netscape cookie file. |
| `PLAYWRIGHT_STORAGE_STATE=/path/state.json` | Supply an authorized Playwright session. |
| `HEADLESS=0` | Show a browser for normal login or CAPTCHA completion. |
| `LOGIN_WAIT_MS=60000` | Keep the visible page open before collection. |
| `MEDIA_WAIT_MS=25000` | Tune how long browser capture waits for playback. |

If Playwright is not resolvable, discover an existing workspace runtime first.
Install dependencies only with explicit user approval.

Completion criterion: the dry run identifies a direct backend, or reports that
a short link must be resolved before routing.

### 3. Download

Run the unified entry point:

```bash
"$SKILL_DIR/scripts/download-social.sh" '<url>' '<output-dir>'
```

- Keep archive files and completed media so reruns skip existing items.
- Let profile jobs continue past individual failures and record failed URLs.
- Fall back to browser capture when a supported single-item extractor fails.
  Douyin single-item capture saves either an MP4 or an image-set directory.
- When login or CAPTCHA is required, rerun with `HEADLESS=0` and a sufficient
  `LOGIN_WAIT_MS`, then let the user complete the normal challenge.
- Never print cookie values, authorization headers, or signed media URLs.
- Never write cookie or Playwright state files into the repository.

Completion criterion: the command succeeds, or every failed item is recorded
after all remaining items have been attempted.

### 4. Verify the Archive

```bash
find '<output-dir>' -type f -size +1024c \
  \( -name '*.mp4' -o -name '*.webm' -o -name '*.mkv' \
    -o -name '*.jpg' -o -name '*.png' -o -name '*.webp' \) -print
find '<output-dir>' -type f -name '*.json' -print
du -sh '<output-dir>'
```

- Compare the collected profile-link count with the visible profile count when
  the platform exposes one.
- Check for undersized media, `failed.json`, `failed-urls.txt`, missing metadata,
  and duplicate IDs.
- Spot-check the first, middle, and final items for playback and account
  ownership.
- Increase `MAX_SCROLLS` or `WAIT_MS`, restore the authorized session, and rerun
  when the visible count is incomplete.

Completion criterion: every collected item has a nonempty media file or a
failure record, ownership spot-checks pass, and count differences are explained.

### 5. Report

Report the absolute output path, successful and failed counts, total size, and
the visibility boundary. List private, draft, or app-only items separately; do
not count them as completed downloads.
