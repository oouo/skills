# 🧠 Skills

> Personal collection of AI agent skills — reusable knowledge modules for coding assistants.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Design Philosophy

1. **Single Responsibility** — Each skill does one thing well, with a clear trigger boundary.
2. **Progressive Disclosure** — `SKILL.md` frontmatter is loaded at startup for routing; the body and `references/` are loaded on-demand, minimizing token waste.
3. **Composability** — Skills are self-contained directories that can be mixed, linked, and shared across projects without side effects.
4. **Zero-Friction Sharing** — Skills live at the repo root so you can paste a GitHub URL into any AI CLI and say "install this".

## Repository Structure

```
skills/
├── <skill-name>/               ← Each skill is a top-level directory
│   ├── SKILL.md                  (required)
│   ├── scripts/                  (optional)
│   ├── references/               (optional)
│   └── resources/                (optional)
├── skills/
│   └── _template/              ← Canonical template (copy to start)
├── .agents/                    ← Agent config & meta-skills
│   ├── AGENTS.md
│   └── skills/skill-creator/
├── CLAUDE.md
├── README.md
├── LICENSE
└── .gitignore
```

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
npx -y skills add oouo/skills --skill <skill-name>

# Via git submodule
git submodule add git@github.com:oouo/skills.git .agents/skills

# Via skills.json reference
echo '{"entries": [{"path": "/path/to/this/repo"}]}' > .agents/skills.json
```

### Create a new skill

**Option A — Use the `skill-creator` meta-skill (recommended):**

Already installed at `.agents/skills/skill-creator/`. Just tell your agent:

> *"Help me create a skill for X"*

**Option B — Copy the template:**

```bash
cp -r skills/_template <new-skill-name>
# Edit <new-skill-name>/SKILL.md
```

**Option C — `npx` CLI:**

```bash
npx -y skills init <new-skill-name>
```

## Skill Anatomy

Every skill is a directory containing at minimum a `SKILL.md`:

```
my-skill/
├── SKILL.md          # Required: YAML frontmatter + instructions (< 500 lines)
├── scripts/          # Optional: Executable helpers (Python, Bash, etc.)
├── examples/         # Optional: Reference implementations
├── references/       # Optional: Deep docs loaded on-demand (saves tokens)
└── resources/        # Optional: Templates, configs, static assets
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

1. Copy `skills/_template` to a new top-level directory: `<your-skill-name>/`
2. Edit the `SKILL.md` frontmatter and body
3. Add supporting files to the appropriate subdirectory
4. Ensure the skill name in frontmatter matches the directory name
5. Keep `SKILL.md` under 500 lines

## License

[MIT](LICENSE)
