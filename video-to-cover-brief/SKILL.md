---
name: video-to-cover-brief
description: >-
  Use when turning a local family-travel or dog-centered short video into an
  evidence-grounded Douyin cover brief, cover series, or published-cover
  replacement. Covers keyframe provenance, source-material preservation,
  deterministic Simplified Chinese top bars, protected main-title pixels,
  staged image generation, profile-grid QA, pixel-diff release gates, and final
  version packaging.
compatibility: >-
  Requires local video or keyframes. Deterministic rendering and QA use
  ffmpeg/ffprobe, ImageMagick 7, HarfBuzz, Bash, shasum, and user-approved
  Chinese fonts.
---

# Video to Cover Brief

## Overview

Turn a local family-travel or dog-centered video into an auditable Douyin cover
workflow. Start with evidence and a renderer-neutral brief. Preserve supplied
video-frame material as immutable source pixels, use an image model only where
generation is actually authorized, and compose measurable Chinese typography
deterministically.

The workflow can stop after the brief or continue through generation, local
review, repair, and packaging. A candidate is never a release merely because it
looks plausible at full size.

## When to Use

Use this skill for a local family-travel or dog-centered short video that needs
an auditable brief, a new cover, a repaired cover, or a canonical local release
package. Reject unrelated genres instead of forcing them into these presets.

## Non-negotiables

- Ground every subject, action, location, top-bar field, and story claim in
  inspected frames, transcript lines, metadata, or an explicit user statement.
- Treat supplied video frames and confirmed cover material as source assets,
  not loose visual references. Do not redraw recognizable people, dogs,
  landmarks, props, poses, or scenery unless the user explicitly asks for it.
- Treat an approved hand-brushed main title as locked artwork. Do not regenerate,
  retype, stretch, compress, or replace it. Move an intact title layer only when
  the user approves the layout change.
- Give every main title one complete mode: preserve approved source artwork, or
  compose a new title with a pinned local font. Never leave a new title as an
  unimplemented visual direction.
- Never ask an image model to generate final visible Chinese whose spelling,
  glyph shape, or metrics must be exact. Generate a text-free visual or repair
  source, then compose exact typography with pinned local fonts or restore
  approved title pixels from an intact source.
- Start every repair from the cleanest authoritative source that predates the
  defect. Do not repeatedly paint over a damaged flattened candidate.
- Limit model output to the authorized region with a mask. After compositing,
  require a maximum pixel difference of zero everywhere else.
- Do not identify Chinese-title repairs by broad color selection on a similar
  background. Derive a minimal geometric or source-difference mask; color-only
  masks can capture the background and create rectangular bands.
- Work in small review batches—three covers by default—until the user approves
  the system. Do not generate an entire series before representative review.
- Keep all exploration local. Never upload, publish, or edit a live Douyin work
  without explicit authorization for that exact file.
- Keep only one canonical final package. Preserve rejected and superseded work
  as history, but do not expose multiple folders as competing final versions.

## Inputs

| Input | Required | Use |
| --- | --- | --- |
| Local video or evidence frames | Yes | Establish the real subject, action, and scene. |
| User-approved canvas/profile screenshot | Recommended | Lock canvas and measure the actual grid cell. |
| Existing cover or clean source plate | Optional | Preserve approved pixels and repair only the named area. |
| Approved top-bar font | Required before final type | Make Chinese deterministic and auditable. |
| Approved title artwork or title font | Required before final title | Resolve the title as locked artwork or deterministic type. |
| Existing neighboring covers | Recommended for a series | Judge consistency in the actual three-column layout. |
| Publication state/edit budget | Optional | Treat reported live edits as scarce; never guess. |

If the user provides no usable video or keyframe evidence, stop and request it.
Do not substitute a verbal summary for visual identity or layout evidence.

## Instructions

### 1. Resolve evidence

1. Confirm that the local video or supplied frames exist.
2. Derive `<video-id>` or `<video-slug>` from the source filename.
3. Create `briefs/evidence/<video-id>/` in the working project.
4. When available, save `ffprobe` metadata and frames near 10%, 50%, and 90%:

   ```bash
   ffprobe -v error -show_format -show_streams -of json '<video>' \
     > 'briefs/evidence/<video-id>/metadata.json'
   ffmpeg -ss '<seconds>' -i '<video>' -frames:v 1 -q:v 2 \
     'briefs/evidence/<video-id>/frame-<timestamp>.jpg'
   ```

5. Add frames around cuts, readable text, or the intended cover moment.
6. Build a contact sheet and inspect it. Record the subject, action, setting,
   readable source text, location clues, and uncertainty.
7. Cite a frame path and timestamp or transcript line for every material claim.

Finish only when beginning/middle/end evidence exists and at least one frame is
suitable for the generation or compositing handoff.

### 2. Classify and write the brief

1. Choose exactly one category: `family-travel` or `dog-story`.
2. Read [references/preset-routing.md](references/preset-routing.md),
   [resources/cover-presets.yaml](resources/cover-presets.yaml), and
   [references/top-bar-system.md](references/top-bar-system.md).
3. Resolve a factual top-bar label, semantic preset, palette, protected source
   regions, and an intentional collision plan.
4. Propose a concrete Simplified Chinese main title and choose exactly one mode:
   - `locked-artwork`: record the intact approved title source and pixel lock
   - `deterministic-font`: pin the title font, SHA-256, point size, line break,
     fill, stroke, top edge, and maximum width; do not use auto-fit
5. Read [references/brief-contract.md](references/brief-contract.md), write
   `briefs/<video-id>.md`, validate every field, report `HOLD`, and pause for the
   user's confirmation before image generation.

### 3. Establish the series contract

Before the first cover is generated, lock the following in the brief set or a
package-local contract. Do not edit project governance files without a separate
user request:

- canonical canvas and color space; use `1086×1448` sRGB PNG when matching the
  validated reference implementation, otherwise use the user's measured canvas
- exact top-bar font file and SHA-256
- top-bar top edge, card height, component height, visible glyph height, color,
  stroke, padding, corner radius, and separator geometry
- main-title mode and either its authoritative artwork path or its complete
  deterministic-font contract
- visible-text allowlist
- source-material protection boundaries
- preview cell dimensions and newest-to-oldest grid order
- naming for candidates, rejected work, and the single canonical final package

Do not silently inherit obsolete geometry from an older series. The bundled
reference profile is a proven default, not authority over explicit user assets.

### 4. Generate in representative batches

After confirmation:

1. For a series, select three covers that stress different conditions: a short
   top-bar label, a long label, and a subject/title close to the top safe zone.
   For one cover, present up to three local candidates when useful.
2. Use the inspected frame as an edit/composition reference, not permission to
   invent a new subject.
3. Ask the image model for a text-free clean visual or a clean repair plate. If
   the existing subject and title are already approved, generate only the
   missing background region.
4. Compose the deterministic top bar with `scripts/render-cover-type.sh`. It
   requires `TOP_FONT`, accepts `INPUT OUTPUT LEFT [RIGHT]`, rejects unstable
   visible-height normalization, and changes only the top-card rectangle.
5. Resolve the main title according to its mode:
   - for `locked-artwork`, restore the exact approved title pixels from the
     authoritative source without retyping or scaling them
   - for `deterministic-font`, run `scripts/render-main-title.sh` with the pinned
     font and brief values; it uses a fixed point size and never auto-fits

   ```bash
   TITLE_FONT='<font>' TITLE_FONT_SHA256='<digest>' \
     TITLE_POINT_SIZE=116 TITLE_FILL='#FFFFFF' TITLE_STROKE='#4B285F' \
     scripts/render-main-title.sh '<input>' '<output>' '第一次\n看海' 190
   ```

   Never pass approved hand-brushed title artwork to this compositor.
6. Build full-size, top-bar, main-title, subject, edge, exact-cell, and
   three-column previews.
7. Present the three as a batch and collect concrete feedback before generating
   the next three. Change the shared rule first when the problem is systemic.

### 5. Repair without collateral damage

When the user marks a defect:

1. Translate the red circle into an exact region and symptom: clipping,
   residue, seam, color band, collision, or unwanted person/object.
2. Find the cleanest source that still has the intended subject and complete
   title. Never assume the latest flattened candidate is the best base.
3. Decide whether the fix is deterministic compositing, source-pixel recovery,
   or a newly generated clean background patch.
4. Build the smallest mask that covers the defect plus anti-aliased edges.
5. Composite from the intact source or clean plate.
6. Hard-lock every unapproved area back to the authoritative pixels.
7. Generate a detail QA crop for the marked region and a full-cover comparison.
8. Add an automated regression check that fails on the old defect.

For real video-frame material, the model may supply a background repair source;
the final subject must still come from the original material pixels.

### 6. Run the release gate

Read [references/release-gate.md](references/release-gate.md). Require:

- exact dimensions, color space, channel contract, and normalized virtual canvas
- expected top-bar geometry and visible glyph height
- approved top-bar and deterministic-title font SHA plus HarfBuzz glyph coverage
- a complete `locked-artwork` or `deterministic-font` main-title contract
- source manifest and SHA-256 equality between packaged files and sources
- zero pixel difference outside every repair mask or locked boundary
- regression checks for every previously observed defect
- human review of the full cover, top bar, main title, subject, edges, and actual
  Douyin profile layout
- side-by-side comparison with video contact sheets to catch a correct filename
  paired with the wrong subject or scene

Any failed or unverified gate returns the candidate to `HOLD`.

### 7. Package and close

1. Collect the exact user-approved files into one numbered package.
2. Write `meta/SOURCES.tsv`, `meta/SHA256SUMS`, `meta/TOPBAR-TEXT.txt`, hashed QA
   artifacts, and a package-local review record.
3. Run the generic gate with explicit provenance and font inputs:

   ```bash
   PROJECT_ROOT='<project>' TOP_FONT='<font>' TOP_FONT_SHA256='<digest>' \
     scripts/check-cover-release.sh '<package>' '<expected-count>'
   ```

4. Run the project's top-bar, pixel-lock, and known-defect checks. Verify that the
   package contains exactly the intended root-level cover PNGs and no accidental
   candidate.
5. Record the sole current release inside the package. Update a project README
   only when the user asks; never edit agent rules merely to promote a cover.
6. Do not create another folder merely to change the status. Promote the
   reviewed package in place when the user explicitly approves it.
7. Do not publish online unless the user separately authorizes the live action.

## Generation handoff

When a raster image model or `baoyu-cover-image` is used:

- provide the brief and at least one inspected reference frame
- request `3:4`, Simplified Chinese context, and a text-free visual layer
- remove all prompt requests for visible Chinese, tags, badges, logos, dates,
  captions, signs, and watermarks
- reserve the deterministic top-bar zone plus the locked-artwork or
  deterministic-font main-title zone
- preserve subject identity and composition from the supplied material
- reject accidental visible text instead of painting another card over it

The model creates visual material; deterministic tools own final typography and
pixel-locked assembly.

## Extending the skill

1. Add semantic presets only to `resources/cover-presets.yaml`.
2. Add category and top-bar copy rules to `references/preset-routing.md`.
3. Keep detailed release checks in `references/release-gate.md`.
4. Add repeatable mechanical work to `scripts/`; do not duplicate it in prose.
5. Add an eval whenever a real failure reveals a reusable boundary.
