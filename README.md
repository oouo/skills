# 🧠 Skills

> Personal collection of AI agent skills — reusable knowledge modules for coding assistants.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Design Philosophy

1. **Single Responsibility** — Each skill does one thing well, with a clear trigger boundary.
2. **Progressive Disclosure** — `name` and `description` load for discovery, the
   body loads after activation, and `references/` load only when needed.
3. **Composability** — Skills are self-contained directories that can be mixed,
   linked, and shared across projects without side effects.
4. **Zero-Friction Sharing** — Skills live at the repo root, so a compatible AI
   CLI can install one directly from its GitHub URL.

## Repository Structure

```
skills/
├── <skill-name>/               ← Each skill is a top-level directory
│   ├── SKILL.md                  (required)
│   ├── agents/                   (optional client metadata)
│   ├── scripts/                  (optional)
│   ├── evals/                    (optional)
│   ├── examples/                 (optional)
│   ├── references/               (optional)
│   ├── assets/                   (optional binary or visual assets)
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
| [`ai-learning-coach`](ai-learning-coach/) | Guide staged learning from goal alignment to evidence-based mastery checks. |
| [`china-travel-planner`](china-travel-planner/) | Plan evidence-grounded China trips and render WeChat cards plus static H5 roadbooks. |
| [`codebase-reader`](codebase-reader/) | Find the real entry, execution spine, and reading order of an unfamiliar codebase. |
| [`full-bleed-icon-creator`](full-bleed-icon-creator/) | Create validated opaque full-bleed module icon sources and PNG/SVG pairs. |
| [`git-commit-push-zh`](git-commit-push-zh/) | Review changes, create Chinese commit messages, and optionally push or open a PR. |
| [`github-trending-report`](github-trending-report/) | Produce daily or weekly GitHub Trending reports for console or Feishu. |
| [`java-best-practices`](java-best-practices/) | Write and review Java with Google formatting, defensive coding, and project-compatible language features. |
| [`session-cleanup`](session-cleanup/) | Clean one task's temporary files on explicit invocation, preserving outputs and backups. |
| [`social-video-archiver`](social-video-archiver/) | Archive authorized Douyin image posts plus Douyin, Xiaohongshu, and YouTube videos. |
| [`video-to-cover-brief`](video-to-cover-brief/) | Build source-frame-first Douyin covers with an approved original-illustration fallback, deterministic Chinese typography, and staged release QA. |

## Quick Start

### Install a skill

Paste the GitHub URL into a compatible AI CLI (Claude Code, Cursor, Gemini CLI, etc.):

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

### Use Java Best Practices

After installing or syncing `java-best-practices` through your usual client workflow:

- **Manual:** in Codex, use `$java-best-practices` or select it in the skill picker, followed by
  the task, for example: `Use $java-best-practices to review OrderService.java for concurrency bugs.`
- **Automatic:** its description targets Java implementation, refactoring, tests, debugging,
  and review. Relevant `.java` files can establish the language even when the request omits "Java".
  Documentation-only or non-Java tasks fall outside that boundary.
- **Codex policy:** `agents/openai.yaml` explicitly allows implicit invocation. This permits
  model selection; it does not install a file watcher or guarantee activation on every Java edit.

For stronger project guidance, add a rule to that project's `AGENTS.md` after installation:

```text
Before writing, modifying, or reviewing Java source or tests, load and apply java-best-practices.
```

Keep mandatory formatting and static checks in the project's build or CI. Skill selection is
model-driven, so use manual invocation when you need to make the choice explicit.
See the [Codex skills documentation](https://learn.chatgpt.com/docs/build-skills) for invocation behavior.

The skill draws on the **Google Java Style Guide** and the **Alibaba Java Development Manual
(Taishan / Huangshan editions)** (《阿里巴巴 Java 开发手册（泰山版/黄山版）》), with the
linked Alibaba Cloud article providing practical examples. It follows the project's configured
Java release and existing contracts; it does not require a JDK upgrade or convert every model
to a record.
See its [source notes](java-best-practices/references/source-notes.md) for attribution and
interpretations of the two guides, the companion article, and JDK contracts.

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
├── agents/           # Optional: client-specific metadata
├── scripts/          # Optional: Executable helpers (Python, Bash, etc.)
├── evals/            # Optional: Evaluation prompts and expected outcomes
├── examples/         # Optional: Reference implementations
├── references/       # Optional: Deep docs loaded on-demand (saves tokens)
├── assets/           # Optional: Binary or visual assets
├── resources/        # Optional: Templates, configs, static data
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
- `description` should be < 100 tokens and keyword-rich; it drives discovery-time routing
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
