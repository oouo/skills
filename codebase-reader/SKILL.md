---
name: codebase-reader
description: >-
  Use when a user needs a fast, source-grounded orientation to an unfamiliar
  repository. Finds the real entry and initialization path, traces one
  representative execution spine, identifies must-read symbols, and gives a
  reading order. Use a deeper analysis workflow for exhaustive documentation,
  architecture review, or refactoring.
compatibility: >-
  Works with Codex and Claude Code. Python 3.9+ is needed only for the optional
  standard-library Python inventory script.
---

# Codebase Reader

## Overview

Find the shortest reliable route from “unknown repository” to “I know where to
read next.” Trace behavior from source rather than summarizing the README or
reciting the file tree.

Keep business source, configuration, tests, and dependencies unchanged. Answer
in chat by default. Write a guide only when the user explicitly requests a file.
Apply the same process to any language; language names are clues, not a whitelist.

## Instructions

### 1. Frame the Reading Question

- Infer the user's immediate goal: general orientation, a subsystem, or a named
  behavior. Use the narrowest scope that answers it.
- Record the repository root, Git branch and commit when available, dirty state,
  primary languages, build system, test entry, and likely executable or library
  entries.
- Treat documentation as a lead and source as evidence. Record environment
  variable names and read sites without exposing values.

Completion criterion: the scope and candidate entries are explicit, with gaps
marked `Unknown`.

### 2. Find the Real Entry and Assembly Path

- Verify how control enters: executable, framework bootstrap, route, command,
  worker subscription, callback, public API, or host integration.
- Follow initialization through configuration, dependency assembly,
  registration, and the handoff to runtime behavior.
- When decorators, dependency injection, registries, events, generated code,
  macros, plugins, runtime boundaries, or concurrency hide an edge, read
  [`references/runtime-mechanisms.md`](references/runtime-mechanisms.md).
- For a Python-heavy scope, optionally run the read-only helper from the skill
  directory:

  ```text
  <python-3-interpreter> scripts/python_inventory.py <repository-root> --json
  ```

  Treat AST calls as candidates, not a runtime call graph.

Completion criterion: one source-backed entry-to-runtime chain is established;
unresolved framework or dynamic edges remain `Unknown`.

### 3. Trace One Execution Spine

Trace the representative path most relevant to the question:

```text
trigger -> selection -> core behavior -> state/effects -> return or termination
```

- Name each transition and cite its source location.
- Add a failure, retry, concurrency, cancellation, or cleanup branch only when it
  changes the reader's understanding of this spine or the user asks for it.
- Separate imports, type relationships, and static candidates from confirmed
  runtime invocation.
- Use `Confirmed`, `Runtime verified`, `Inferred`, or `Unknown` for material
  claims. Run only checks already shown to be side-effect free.

Completion criterion: the spine has a trigger, ordered transitions, important
state or effects, and a return or termination point.

### 4. Select the Must-Read Units

- Put symbols needed to reconstruct the spine in **Must read**.
- Put adapters, validation, serialization, storage, and other context in
  **Supporting** only when they clarify the spine.
- For each must-read unit, give its location, current role, upstream trigger,
  downstream transition, and material state or side effects.
- Partition a large file by real responsibilities and control transitions. Read
  the relevant span end to end rather than slicing it by line count.

Completion criterion: a reader can follow the spine using the must-read list
without first exploring unrelated modules.

### 5. Deliver the Reading Map

Answer in Simplified Chinese and preserve code symbols. Default to:

1. one-paragraph conclusion
2. real entry and initialization
3. representative execution spine
4. must-read and supporting units
5. recommended source reading order
6. unknowns that materially limit the explanation

Include state, side effects, failure, concurrency, or lifecycle as compact
subsections only when they matter to the traced path. If the user explicitly
requests a persistent or fuller guide, read
[`references/report-format.md`](references/report-format.md) and write only that
report.

Before finishing, verify that every material claim has evidence, the reading
order follows execution rather than filenames, and the answer contains current
behavior rather than redesign or refactoring advice.

Completion criterion: the user gets a concise source-backed route through the
code, and no repository file changed unless a report was explicitly requested.
