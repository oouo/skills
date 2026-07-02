# General Troubleshooting Guide

This guide details common issues and resolutions when running the GitHub Trending Report automation.

## 1. Timezone and Scheduling Offsets
- **Symptom**: Reports are executed or timestamps are off by exactly 8 hours (or timezone difference).
- **Cause**: Dual timezone conversion. The host system's scheduler or the parsing layer might interpret local time as UTC, or execute local inputs relative to another zone.
- **Solution**:
  - Always specify schedules using absolute UTC time.
    - Example: 10:18 Asia/Shanghai -> 02:18 UTC.
  - When generating dates and times in report text/titles, enforce conversion explicitly (e.g. `TZ=Asia/Shanghai` or matching library parameters) to output the target timezone date, ignoring the running runner's timezone.

## 2. Scraping and Page Layout Changes
- **Symptom**: Page structure fails to parse, descriptions are empty, or script fails.
- **Cause**: GitHub Trending is a scraped page (no direct JSON API is officially supported). Changes in classes, tag structure, or authentication walls can break parsing.
- **Solution**:
  - If parsing fails, fall back to searching GitHub's API or using real-time search queries for "GitHub daily trending" or "GitHub weekly trending".
  - Gracefully handle cases where the programming language or star counts are missing. Fall back to standard defaults instead of crashing or generating fake data (e.g., use "热度见 Trending").

## 3. Formatting and Rendering Failures
- **Symptom**: Feishu message card fails with a "Bad Request", or renders raw Markdown tags on mobile clients.
- **Cause**: Feishu `lark_md` blocks do not support all standard GFM (GitHub Flavored Markdown) features (such as nested HTML tables or specific inline code styling) or the payload size exceeded 20 KB.
- **Solution**:
  - Keep descriptions concise. Keep each repository review to ~60-70 characters.
  - Avoid using backticks (`` ` ``) for formatting stars or language tags within elements on mobile interfaces.
  - Double check nested lists and escaped characters in URLs. If card fails, log the full response error and fall back to plain text.
