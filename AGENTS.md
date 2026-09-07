# AGENTS.md

## Project Context

This is a personal AI agent skills repository (`oouo/skills`). All skills follow
the open `SKILL.md` standard and live in **top-level directories** in the repo
root (for example, `git-commit-push-zh/SKILL.md`). Keep `AGENTS.md` as the
canonical repository rulebook and `CLAUDE.md` as a thin compatibility entry
point; do not duplicate the full rules across both files.

## Rules

### Repository Boundary

- When creating or updating skills, write only inside this repository.
- Never copy, sync, install, or mirror repository changes into active agent
  directories such as `~/.cc-switch/skills`, `~/.codex/skills`,
  `~/.claude/skills`, or equivalent CLI-managed locations.
- The user owns all CC Switch and agent-CLI synchronization. If a loaded skill
  is stale, report that fact without modifying the loaded copy.

### Skill Creation

- Place new skills at the **repo root**: `<skill-name>/SKILL.md`.
- This keeps GitHub URLs short and shareable. Compatible AI CLIs can install
  `https://github.com/oouo/skills/tree/main/<skill-name>` directly.
- The directory name and the `name` field in `SKILL.md` frontmatter MUST be
  identical, using lowercase kebab-case (for example, `code-review`).
- Every `SKILL.md` MUST begin with valid YAML frontmatter containing at minimum
  `name` and `description`.

### Skill Quality

- `description` must be action-oriented and < 100 tokens. Pattern:
  `"Use when [trigger]. Covers [X] and [Y]."`
- Skill body must be < 500 lines. Move supplementary material to `references/`.
- Use imperative, specific instructions: `"Run pnpm lint before committing"`
  not `"Linting is recommended"`.
- Include concrete code snippets over prose when possible.

### File Organization

- `agents/` — Client-specific metadata only (for example, `agents/openai.yaml`).
- `scripts/` — Executable helpers only (Python, Bash, PowerShell).
- `evals/` — Evaluation prompts, fixtures, and expected outcomes.
- `examples/` — Reference implementations the agent can study.
- `references/` — Deep documentation loaded on-demand (progressive disclosure).
- `assets/` — Binary or visual assets used directly by the skill.
- `resources/` — Templates, configs, and static data.
- `tests/` — Self-contained skill checks and fixtures; avoid network access by default.
- Do NOT add empty subdirectories. Only create them when you have content.

### Style

- Write all skill documentation in English; output specifications such as commit
  formats or report templates may use the target language.
- Use Markdown headings (`##`) to structure `SKILL.md` sections: Overview, When
  to Use, Instructions.
- Prefer bullet lists and tables over paragraphs.
- Keep lines under 100 characters where practical.
- Use imperative language in instructions ("Always do X", not "X is preferred").

### Validation

- Run every validator documented by the changed skill.
- Run skill-local tests when present:
  `python3 -m unittest discover -s "<skill-name>/tests" -p "test_*.py"`.
- Run `git diff --check` before committing.

### Git

- Commit messages: `feat(skill-name): description` or `fix(skill-name): description`.
- One skill per commit when creating new skills.

### Common Gotchas

- Frontmatter `name` and `description` load during discovery. Make `description`
  descriptive and keyword-rich because it drives routing.
- Keep the core workflow in `SKILL.md` and supporting detail in `references/`.
  Follow the progressive-disclosure model described in `README.md`.
