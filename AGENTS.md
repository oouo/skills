# AGENTS.md

## Project Context

This is a personal AI agent skills repository (`oouo/skills`). All skills follow the open `SKILL.md` standard and are placed as **top-level directories** in the repo root (e.g., `git-commit-push-zh/SKILL.md`).

## Rules

### Skill Creation

- Place new skills at the **repo root**: `<skill-name>/SKILL.md`.
- This keeps GitHub URLs short and shareable: users paste `https://github.com/oouo/skills/tree/main/<skill-name>` into any AI CLI to install.
- The directory name and the `name` field in `SKILL.md` frontmatter MUST be identical, using lowercase kebab-case (e.g., `code-review`).
- Every `SKILL.md` MUST begin with valid YAML frontmatter containing at minimum `name` and `description`.

### Skill Quality

- `description` must be action-oriented and < 100 tokens. Pattern: `"Use when [trigger]. Covers [X] and [Y]."`
- Skill body must be < 500 lines. Move supplementary material to `references/`.
- Use imperative, specific instructions: `"Run pnpm lint before committing"` not `"Linting is recommended"`.
- Include concrete code snippets over prose when possible.

### File Organization

- `scripts/` — Executable helpers only (Python, Bash, PowerShell).
- `examples/` — Reference implementations the agent can study.
- `references/` — Deep documentation loaded on-demand (progressive disclosure).
- `resources/` — Templates, configs, static assets.
- Do NOT add empty subdirectories. Only create them when you have content.

### Style

- Write all skill documentation in English; output specifications (e.g. commit format, report template) may use target language.
- Use Markdown headings (`##`) to structure `SKILL.md` sections: Overview, When to Use, Instructions.
- Prefer bullet lists and tables over paragraphs.
- Keep lines under 100 characters where practical.
- Use imperative language in instructions ("Always do X", not "X is preferred").

### Git

- Commit messages: `feat(skill-name): description` or `fix(skill-name): description`.
- One skill per commit when creating new skills.

### Common Gotchas

- Frontmatter `description` is the ONLY part loaded at agent startup for routing — make it descriptive and keyword-rich.
- Files in `references/` are loaded on-demand; files in the skill root are always loaded.
