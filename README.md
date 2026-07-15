# 🧠 Skills

> Personal collection of AI agent skills — reusable knowledge modules for coding assistants.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Design Philosophy

1. **Single Responsibility** — Each skill does one thing well, with a clear trigger boundary.
2. **Progressive Disclosure** — `SKILL.md` frontmatter is loaded for routing, the body loads after activation, and `references/` load only when needed.
3. **Composability** — Skills are self-contained directories that can be mixed, linked, and shared across projects without side effects.
4. **Zero-Friction Sharing** — Skills live at the repo root so you can paste a GitHub URL into any AI CLI and say "install this".

## Repository Structure

```
skills/
├── <skill-name>/               ← Each skill is a top-level directory
│   ├── SKILL.md                  (required)
│   ├── scripts/                  (optional)
│   ├── references/               (optional)
│   ├── resources/                (optional)
│   └── tests/                    (optional)
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── LICENSE
└── .gitignore
```

## Available Skills

| Skill | Purpose |
| --- | --- |
| [`codebase-reader`](codebase-reader/) | Find the real entry, execution spine, and reading order of an unfamiliar codebase. |
| [`git-commit-push-zh`](git-commit-push-zh/) | Review changes, create Chinese commit messages, and optionally push or open a PR. |
| [`github-trending-report`](github-trending-report/) | Produce daily or weekly GitHub Trending reports for console or Feishu. |
| [`social-video-archiver`](social-video-archiver/) | Archive authorized Douyin image posts plus Douyin, Xiaohongshu, and YouTube videos. |
| [`video-to-cover-brief`](video-to-cover-brief/) | Turn family-travel or dog-centered videos into evidence-grounded Douyin cover briefs. |

## Quick Start

### Install a skill

Paste the GitHub URL into any AI CLI (Claude Code, Cursor, Gemini CLI, etc.):

```
https://github.com/oouo/skills/tree/main/<skill-name>
```

Then say: **"帮我安装这个 skill"** — the AI reads the SKILL.md and installs it locally.

Other install methods also work:

```bash
# Via npx CLI
npx skills add https://github.com/oouo/skills/tree/main/<skill-name>

# Via git submodule
git submodule add git@github.com:oouo/skills.git .agents/skills
```

### Create a new skill

Create a new top-level directory with a `SKILL.md`:

```bash
mkdir <new-skill-name>
# Edit <new-skill-name>/SKILL.md
```

## Skill Anatomy

Every skill is a directory containing at minimum a `SKILL.md`:

```
my-skill/
├── SKILL.md          # Required: YAML frontmatter + instructions (< 500 lines)
├── scripts/          # Optional: Executable helpers (Python, Bash, etc.)
├── examples/         # Optional: Reference implementations
├── references/       # Optional: Deep docs loaded on-demand (saves tokens)
├── resources/        # Optional: Templates, configs, static assets
└── tests/            # Optional: Self-contained checks and fixtures
```

### SKILL.md Format

```markdown
---
name: my-skill
description: >
  Use when [trigger scenario]. Covers [capability X] and [capability Y].
---

# My Skill

## Overview
Brief summary of what this skill does.

## When to Use
- Scenario A
- Scenario B

## Instructions
Step-by-step procedures...
```

**Key rules:**
- `name` must match the directory name
- `description` should be < 100 tokens, keyword-rich (it's the only part loaded at startup)
- Body should be < 500 lines; move deep docs to `references/`

## Writing Good Skills

| Principle | Do ✅ | Don't ❌ |
|-----------|----------|-----------|
| **Trigger clarity** | `"Use when generating React components with TypeScript"` | `"React helper"` |
| **Imperative tone** | `"Always use named exports"` | `"Named exports are preferred"` |
| **Progressive disclosure** | Put API schemas in `references/` | Inline 200-line schemas in `SKILL.md` |
| **Testable instructions** | `"Run pnpm test before committing"` | `"Make sure tests pass"` |
| **Single responsibility** | One skill per domain boundary | One mega-skill for everything |

## Contributing

1. Create a new top-level directory: `<your-skill-name>/`
2. Add a `SKILL.md` with valid YAML frontmatter (`name`, `description`)
3. Add supporting files to the appropriate subdirectory
4. Run any skill-local tests
5. Ensure the skill name in frontmatter matches the directory name
6. Keep `SKILL.md` under 500 lines

## License

[MIT](LICENSE)
