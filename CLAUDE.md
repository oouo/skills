# CLAUDE.md

## Project Overview

This is a personal AI agent skills repository. It contains reusable skill modules, each following the open `SKILL.md` standard format. Skills are placed as **top-level directories** in the repo root for easy URL-based sharing.

## Repository Structure

- `<skill-name>/` — Each skill is a top-level directory at the repo root
- `skills/_template/` — Canonical template for creating new skills
- `.agents/` — Agent configuration and meta-skills for this repo

## Key Conventions

- Each skill is a self-contained directory at the repo root: `<skill-name>/SKILL.md`
- Every skill MUST have a `SKILL.md` with YAML frontmatter (`name`, `description` required)
- The `name` field in frontmatter MUST match the directory name
- Skill body should be < 500 lines; use `references/` for deep documentation
- `description` should be < 100 tokens and action-oriented (starts with "Use when...")
- Use imperative language in instructions ("Always do X", not "X is preferred")

## Install Pattern

Users paste a GitHub URL into any AI CLI to install:

```
https://github.com/oouo/skills/tree/main/<skill-name>
```

The AI reads the SKILL.md content and creates the skill locally.

## Commands

```bash
# List all skills (top-level dirs with SKILL.md)
find . -maxdepth 2 -name "SKILL.md" ! -path "./skills/*" ! -path "./.agents/*"

# Validate frontmatter
find . -maxdepth 2 -name "SKILL.md" ! -path "./skills/*" -exec head -5 {} \;
```

## Common Gotchas

- Do NOT create skills inside `skills/` — that directory only holds `_template`
- Do NOT use `skills/_template` directly — always copy it first
- Frontmatter `description` is the ONLY part loaded at agent startup for routing — make it descriptive and keyword-rich
- Files in `references/` are loaded on-demand; files in the skill root are always loaded
