---
name: full-bleed-icon-creator
description: >
  Use when creating or substantially redrawing opaque full-bleed square module
  icons for Egern or similar hosts that apply their own corner radius. Covers
  brand-new raster generation, matched PNG/SVG delivery, semantic composition,
  prompt maintenance, geometry validation, and small-size visual QA.
---

# Full-Bleed Icon Creator

## Overview

Treat geometry as an acceptance gate, never as a composition recipe. Build one
organic character whose own silhouette fills both axes, then let the host apply
the final corner radius.

## When to Use

Use this skill for a brand-new or substantially redrawn opaque square module
icon whose host supplies the final corner radius. Do not use it for a minor
vector edit, a transparent logo, or an established code-native icon system.

## Instructions

### 1. Establish the Contract

- Locate the target repository and read its `README.md`, `AGENTS.md`, and
  `CLAUDE.md` before changing assets.
- Preserve an existing public filename unless the user explicitly requests a
  rename. Use short lowercase kebab-case for a new name.
- Confirm the required delivery paths. For the reference contract, use:

  ```text
  sources/<name>.png
  png/<name>.png
  svg/<name>.svg
  ```

- Read [`references/asset-contract.md`](references/asset-contract.md) before
  drafting any full-bleed asset.
- Inspect visual references only from the target repository or paths the user
  explicitly provides. Read them in place; keep private or project-owned
  binaries out of this skill.
- Prefer the target repository's validator. Use the bundled validator only when
  the repository follows the same `sources/png/svg` layout.

Completion criterion: the subject, semantic outcome, filename, output paths,
background family, existing repository rules, and validation command are known.

### 2. Write the Semantic Brief

- Choose one unmistakable anthropomorphic main character and one to three
  supporting symbols that describe the module's function or result.
- Make the main body naturally broad: use an orb, cloud, panel, ticket, tag,
  pin, bubble, or another subject-native organic silhouette.
- Keep state changes and supporting symbols inside the body or tightly
  overlapping it. Use overlap and layering to show sequence.
- Remove words, copied brand geometry, decorative scenery, and detached pieces
  that exist only to stretch the measured bounds.
- Reject a brief whose silhouette reads as a cross, plus sign, four handles, or
  symmetric top/bottom tabs paired with side cards.
- Read [`references/prompt-template.md`](references/prompt-template.md) and
  combine its shared lock with the asset-specific subject, background color,
  symbols, and semantic order.

Completion criterion: one generation prompt defines a coherent character,
function, outcome, palette, full-bleed layout, and regeneration rule.

### 3. Generate a Brand-New Raster Source

- Call an available image-generation tool and generate from a blank canvas.
- Save the accepted original model output immediately as
  `sources/<name>.png`.
- Inspect the uncropped square. Require a near-uniform background in all four
  literal corners and a single, readable, balanced subject cluster.
- Regenerate the complete raster when the composition, geometry, semantic
  reading, or style fails. Keep rejected drafts outside the repository.
- Preserve source provenance: raster acceptance happens before any SVG work.

Completion criterion: a genuinely new retained source passes visual review as
an uncropped square without any post-generation composition repair.

### 4. Normalize the Delivery PNG Once

Normalize coordinates and strip metadata in one direct operation:

```bash
magick 'sources/<name>.png' -resize 800x800! -strip 'png/<name>.png'
```

- Keep every source pixel represented in the output; do not crop, rearrange,
  erase, mask, or selectively retouch the source.
- Verify that the PNG is exactly 800x800, sRGB, and fully opaque.

Completion criterion: the retained source and delivery PNG differ only by the
single direct 800x800 normalization accepted by the validator.

### 5. Author the Editable SVG Independently

- Create `svg/<name>.svg` only after the raster source and PNG are accepted.
- Start with a full-canvas background rectangle and use editable vector
  primitives for the subject, outlines, highlights, and compact shadow.
- Match the PNG's subject, semantic order, background family, composition, and
  visual weight without tracing or embedding raster data.
- Use the target repository's SVG generator only as a draft when the asset is
  registered there. Refine the vector result to match the accepted subject.

Completion criterion: the SVG is valid XML, uses a `0 0 800 800` viewBox,
contains no raster reference, and reads as the same icon family at small sizes.

### 6. Validate Geometry, Provenance, and Style

Run the repository validator when present:

```bash
scripts/validate-icon.sh '<name>'
```

Otherwise run the bundled validator from the installed skill directory:

```bash
SKILL_DIR='<absolute path to full-bleed-icon-creator>'
"$SKILL_DIR/scripts/validate-icon.sh" '<repository-root>' '<name>'
```

- Install missing validator dependencies only after user approval. The bundled
  script requires `magick`, `xmllint`, `rg`, and `rsvg-convert`.
- Treat a raster geometry failure as a regeneration signal. The QA mask is a
  measuring instrument and must never modify delivery pixels.
- Repeat direct normalization when source-to-PNG equivalence fails.
- Repair XML, vector structure, or semantic mismatch in the SVG itself.
- Treat fewer than 30000 PNG colors or normalized PNG-to-SVG RMSE below 0.15 as
  a provenance/style alarm. Regenerate unless the user explicitly accepts a
  deliberate flat-vector exception.
- Inspect source, PNG, and rendered SVG as uncropped squares and through the
  rounded proxy at 120px, 64px, 40px, and 32px on light and dark surroundings.

Completion criterion: every numeric check passes, the rounded proxy clips zero
subject pixels, and raster/vector outputs remain recognizably the same family at
all four display sizes.

### 7. Maintain the Repository and Report

- Update the canonical asset list and final generation prompt in the target
  repository's source-of-truth document.
- Keep only the retained source, delivery pair, required script or prompt
  updates, and project-owned documentation changes.
- Run `git diff --check` and inspect `git status` without staging unrelated
  work. Commit or push only when the user explicitly requests it.
- Report the absolute paths, source-to-PNG changed-pixel count, PNG color count,
  subject bounds, four clearances, centroid distance, rounded-proxy clipped
  pixels, normalized RMSE, and visual-QA result.

Completion criterion: the repository contains exactly one accepted source and
one PNG/SVG delivery pair for the asset, its canonical prompt is current, no QA
drafts remain, and the report accounts for every acceptance gate.
