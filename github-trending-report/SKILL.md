---
name: github-trending-report
description: Fetch GitHub Trending repositories and push structured daily morning reports or weekly trend summaries to messaging channels like Feishu. Trigger when the user mentions GitHub Trending daily/weekly report, Feishu/Slack push, morning/weekly technical newsletters.
---

# GitHub Trending Report

Generate and push technical briefings from GitHub Trending to messaging channels.

## Overview
This skill fetches GitHub Trending repositories (daily/weekly), constructs a high-density technical summary, cleans the content to keep it clear and professional, and pushes it to messaging channels. 

## When to Use
Use this skill when:
- The user requests a daily morning technical report or weekly trend summary from GitHub.
- The user wants to push GitHub Trending highlights to channels like Feishu, Slack, etc.
- A scheduled automation task triggers to compile technical reports.

## Instructions

### 1. First-Run Configuration Setup
Before fetching or sending any report, check if the local configuration file `.trending-report-config.json` exists in the workspace root.
- **If it does not exist**:
  1. Interactively prompt the user to provide the configuration parameters.
  2. Ask for `push_channel` (options: `feishu`, `slack`, etc. Default: `feishu`).
  3. Ask for the credentials required by the chosen channel:
     - For `feishu`: Webhook URL and Signing Secret.
  4. Ask for `timezone` (default: `Asia/Shanghai`).
  5. Write the configuration to `.trending-report-config.json` in the workspace root.
  6. Recommend adding `.trending-report-config.json` to `.gitignore` to prevent credential leakage.
- **If it exists**:
  - Read and use the configurations from it.

### 2. Report Modes & Content Generation
Fetch the trending list according to the mode:
- **Daily Report (`daily`)**:
  - Source: `https://github.com/trending?since=daily` (fallback to search if page is down).
  - Title: `GitHub Trending 晨报 · YYYY-MM-DD` (use the date in the configured timezone).
  - Structure:
    1. **趋势判断 (Trend Analysis)**: 1-2 sentences summarizing the day's main technical directions (e.g., AI agents, infrastructure, dev tools). Do not use generic statements like "Here is today's trending list".
    2. **热门仓库 (Hot Repositories)**: Exactly 5 most noteworthy repositories.
    3. **Rust 小工具 (Rust Dev Tools)**: 2-3 practical Rust-based CLI/dev tools (e.g., ripgrep, fd, zoxide, bat, eza, dust, delta) or newly trending Rust projects, with utility explanations.
- **Weekly Report (`weekly`)**:
  - Source: `https://github.com/trending?since=weekly`.
  - Title: `GitHub Trending 周报 · YYYY-MM-DD`.
  - Structure:
    1. **本周判断 (Weekly Trend Analysis)**: 2-3 sentences summarizing weekly movements and observation timeframe (e.g., "Observation window: Last Friday to today's execution").
    2. **热门仓库 (Hot Repositories)**: Exactly 8 most noteworthy repositories.
    3. **值得复盘 (Retrospective)**: 3 key underlying developer needs/industry changes reflected by the trends.
    4. **Rust 小工具 (Rust Dev Tools)**: 2-3 practical Rust tools.

### 3. Content Rules & Formatting
To ensure readability and bypass rendering issues on mobile interfaces:
- **Repository format**:
  `**No. [owner/repo](GitHub URL)**  ·  语言  ·  ⭐ 今日/本周星数`
  `一句话推荐理由`
- **Rust Tool format**:
  `[工具名](GitHub URL)`：用途和推荐理由
- **Cleaning & Rewriting**:
  - Translate descriptions and reasons into natural, concise Chinese (~60 chars for daily, ~70 chars for weekly).
  - Remove page noise (Sponsor/Star buttons, login info, HTML entities).
  - If trending stars are missing, write "热度见 Trending" instead of fabricating numbers.

### 4. Push Delivery Dispatch
1. Read the `push_channel` from config.
2. Load the corresponding channel specifications from `references/<push_channel>.md` (e.g., `references/feishu.md` for Feishu).
3. Build the payload according to the specifications.
4. Send the payload via POST request.
5. If the request fails, retry once. If it continues to fail, fallback to a plaintext format, or log the failure reason.

## Scheduling Hint
This skill executes actions on demand. To schedule automation, users should configure triggers using:
- **Codex Automation**: Add the automation flow with a specific time (e.g., UTC 02:18 for Beijing 10:18) using the provided prompt.
- **Claude Code**: Use the `/schedule` command or system-level schedulers (Task Scheduler / cron) calling `claude -p "github-trending-report <mode>"`.
