---
name: java-best-practices
description: >-
  Use when writing, modifying, debugging, or reviewing Java source or tests, or answering questions
  about Java behavior. Relevant .java files can establish the language when the request omits it.
  Covers Google Java formatting, JDK compatibility, and defensive coding. Skip build-only tasks.
---

# Java Best Practices

## Overview

Use the Google Java Style Guide for style, the Alibaba Java Development Manual for defensive
coding, and the target JDK's contracts for runtime behavior. For attribution or conflicting
guidance, consult the [source notes](references/source-notes.md).

## When to Use

- For implementation and debugging, follow the target module's conventions and limit edits to
  the requested behavior. A build, deployment, or documentation task alone is outside scope.
- For a review, keep the worktree read-only and apply the rules relevant to the diff.
- For a Java behavior question, go directly to the relevant contract. Ask for the JDK version
  only when it changes the answer and the target release cannot be inferred.

## Instructions

### Establish the baseline

Read the applicable repository instructions, nearby code, and target module's build settings.
Check the compiler release or, where set separately, the source and target levels. Use those
settings with the module's toolchain and runtime requirements to select APIs and language
features. Keep the existing release and preview settings. Check unfamiliar APIs against
documentation for that release. Preserve public API, serialization, framework, and nullability
contracts.

### Apply the rules that match the change

Trace the changed code to the callers that rely on it. Read every section that applies, including
when one expression involves several contracts (for example, decimal equality in a map key).

- For decimal precision and equality, boxed values, bean names, enum metadata, null, or `Optional`,
  read [Values and API contracts](references/java-contracts.md#values-and-api-contracts).
- For collection construction, mutability, null elements, iteration, arrays, views, or lookup,
  read [Collections](references/java-contracts.md#collections).
- For string accumulation or delimited fields, read [Text](references/java-contracts.md#text).
- For executors, virtual threads, thread-local context, or parallel streams,
  read [Concurrency](references/java-contracts.md#concurrency).
- For switches, text blocks, records, patterns, or sealed types,
  read [Language features](references/java-contracts.md#language-features).
- For closing, unlocking, exception handling, interruption, or logging,
  read [Resources and failures](references/java-contracts.md#resources-and-failures).

### Structure and document Java code

- Use early returns or continues for exceptional cases. Split independent business steps into
  action-named methods. Name intermediate values, business thresholds, and sentinel values.
- Explain business rules, units, and exceptional boundaries in the project's comment language
  with English half-width punctuation. Document units, nullability, and boundaries of public
  and protected APIs in Javadoc.
  Reuse inherited documentation and omit redundant descriptions of obvious accessors.
- Use explicit imports, conventional modifier order, braces around control-flow bodies, and
  uppercase `L` for long literals. Group overloads and constructors, use `@Override` where
  legal, qualify static members with their class, and keep type-use annotations with their type.
- Reserve `UPPER_SNAKE_CASE` for deeply immutable `static final` constants. Use `lowerCamelCase`
  for loggers and mutable `static final` objects.

### Format changed handwritten Java files

1. Select only changed handwritten Java files. Leave generated sources to their generator.
2. Use the repository's configured `google-java-format` task or pinned formatter within that
   scope. If no formatting task is configured, check build scripts and local tooling for an
   existing `google-java-format` CLI. Verify the actual executable with `--version` and `--help`.
3. Let the formatter handle wrapping, two-space indentation, K&R braces, and the Google Style
   100-column limit with its documented exceptions. Use its check mode when available.
   Otherwise, compare its stdout with each selected file. Inspect the diff for unrelated edits.

### Verify and report

- For implementation changes, verify the affected caller contracts, such as null or empty results,
  numeric precision, ownership, or framework mappings. Exercise the relevant boundary in a targeted
  test or check. Run the module's relevant compilation, tests, and static checks. Report the change,
  observed results, and any boundary or check left unverified, including formatting.
- For review findings, give the location, failure condition, impact, and repair. Distinguish
  correctness defects from style violations. Report in the user's language.
