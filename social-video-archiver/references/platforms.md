# Platform Branches

Read only the target platform section. Platform pages and extractors change, so
verify the runtime instead of treating historical support as a guarantee.

## Common Preflight

```bash
yt-dlp --version
yt-dlp --list-extractors | rg -i 'douyin|xiaohongshu|youtube'
ffmpeg -version
ffprobe -version
node -e "require('playwright')"
```

Use `yt-dlp` for mature extractors, playlists, resuming, subtitles, and
metadata. Use Playwright for page scrolling, short-link redirects, and media
actually played by the page. Use `ffmpeg` for YouTube stream merging and HLS.

## Douyin

- For one `/video/<id>` or image-post URL, try `yt-dlp`; the entry point falls
  back to browser capture when extraction fails.
- Browser capture saves a Douyin image post as `<output>/<post-id>/001.<ext>`,
  `<output>/<post-id>/002.<ext>`, and `<post-id>.json`.
- For `/user/<sec_uid>`, run `scripts/download-douyin-profile.mjs`. It scrolls
  the profile, collects video links, and captures media from each video page.
- Resolve share links before classifying them. Do not mix search results,
  recommendations, or related posts into the profile archive.
- Compare the profile work count with `video-urls.txt`. If no total is visible,
  report the result as "items visible to the authorized web session."

Tune with `MAX_SCROLLS`, `WAIT_MS`, `LIMIT`, `COLLECT_ONLY=1`,
`VIDEO_LIST_FILE`, or `PROFILE_MARKER`.

## Xiaohongshu

- For one video note at `/explore/<id>` or `/discovery/item/<id>`, use the
  `XiaoHongShu` `yt-dlp` extractor.
- For a profile, collect note links with `collect-xiaohongshu-profile.mjs`, then run
  `yt-dlp` for each note. Preserve an explicit `type=normal|video` marker.
- Treat browser exit code `4` as a skipped image-only note only when the URL says
  `type=normal`. Keep unknown types in the failure record rather than risking a
  silent video omission.
- Preserve `xsec_token` query parameters on URLs that require them.
- Fall back to `capture-browser-video.mjs` when extraction fails for one visible
  video note.

## YouTube

- Send videos, Shorts, playlists, channels, and profile pages to `yt-dlp`.
- Enumerate profile and playlist URLs first, then download each item separately
  so `failed-urls.txt` records every failed item.
- Prefer explicit `/videos`, `/shorts`, or playlist URLs to control channel
  scope.
- Do not load cookies for public videos. For owned age-restricted, private, or
  account-visible videos, use an authorized cookie source.
- Keep subtitle options enabled. Missing requested-language subtitles do not
  make the media download a failure.
- Upgrade `yt-dlp` and verify a supported JavaScript runtime when YouTube serves
  a JavaScript challenge. Do not bypass CAPTCHA or account-security checks.

## Authentication and Secrets

- Use cookies only for content the user is authorized to access.
- Prefer direct browser-cookie access over exporting a complete cookie jar.
- Store any necessary cookie or Playwright state file outside the repository,
  restrict its permissions, and never print or commit it.
- Keep signed media URLs out of metadata and logs because they contain temporary
  authorization parameters.

## Failure Classification

- **No profile links:** Verify the page, then restore authentication or update
  the exact post-link pattern.
- **HTTP 401 or 403:** Refresh the normal browser session and rerun. Do not
  reuse an expired signed URL.
- **Links but no media:** Complete normal verification, start playback, and
  inspect the media-response host.
- **Tiny or broken file:** Remove that failed file and retry with a complete
  MP4 or HLS stream through `ffmpeg`.
- **Profile count is low:** Increase `MAX_SCROLLS` and `WAIT_MS`, then resume.
