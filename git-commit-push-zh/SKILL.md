---
name: git-commit-push-zh
description: Use when reviewing Git changes and creating a Chinese commit message. Covers intentional staging, commit verification, optional push, and user-requested PR creation.
disable-model-invocation: true
---

# Git Commit Push

## Overview

Flow: review changes → compose Chinese commit log → commit → confirm push → optional PR.

## When to Use

Use this skill when the user explicitly requests a Chinese Git commit workflow.

## Instructions

## Step 1: Review Changes

Run `git status` and `git diff --staged` (or `git diff` if nothing is staged).

Completion criterion: all changed files and their intent identified.

### Safety Checks

Block before proceeding if:
- Sensitive files present (`.env`, `credentials`, private keys, tokens) → warn user, do not stage
- Diff exceeds 2000 lines → suggest splitting
- Unresolved merge conflict markers exist → abort and notify

## Step 2: Compose Commit Log

Format: `type: 中文描述`

Infer the best-matching type from the changes:

| type | 含义 |
|------|------|
| feat | 新功能 |
| fix | 缺陷修复 |
| refactor | 重构，不改变外部行为 |
| docs | 文档 |
| style | 格式、排版、无逻辑变化 |
| test | 测试 |
| chore | 构建、依赖、脚手架、杂项 |
| perf | 性能优化 |
| ci | CI/CD 配置 |
| build | 构建系统或依赖管理 |

Rules:
- Description in Chinese, concise, max 50 characters
- Multiple changes of the same type → single commit
- Changes spanning types → split into separate commits, one type each
- If body is needed, add a blank line then explain reason/impact in Chinese

Completion criterion: log composed and shown to user for confirmation.

## Step 3: Commit

After user confirms the log:
1. Stage relevant files (`git add` specific files, never `-A`)
2. Run `git commit`
3. Run `git status` to verify success

Forbidden:
- `--no-verify` to skip hooks
- `--amend` on already-pushed commits
- Staging files user has not confirmed

Completion criterion: `git log -1` shows the correct commit.

## Step 4: Confirm Push

After successful commit, ask user whether to push.

- User confirms → `git push` (or `git push -u origin <branch>` if no upstream)
- User declines → stop, do not push

Forbidden:
- `--force` or `--force-with-lease` to main/master
- Pushing without explicit user confirmation

## Step 5: PR (only when user requests)

Only execute when user explicitly asks to create a PR. Never suggest proactively.

1. Ask for target branch (default: main)
2. Create with `gh pr create`, title reuses commit log, body describes changes in Chinese
3. Return PR URL to user

Completion criterion: PR URL shown to user.
