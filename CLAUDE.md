# CLAUDE.md

## Project Overview

This is a personal AI agent skills repository. It contains reusable skill modules, each following the open `SKILL.md` standard format. Skills are placed as **top-level directories** in the repo root for easy URL-based sharing.

For full rules see `AGENTS.md`.

## Install Pattern

Users paste a GitHub URL into any AI CLI to install:

```
https://github.com/oouo/skills/tree/main/<skill-name>
```

The AI reads the SKILL.md content and creates the skill locally.

## Commands

```bash
# List all skills (top-level dirs with SKILL.md)
find . -maxdepth 2 -name "SKILL.md"

# Validate frontmatter
find . -maxdepth 2 -name "SKILL.md" -exec head -5 {} \;
```
