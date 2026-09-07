---
name: video-to-cover-brief
description: >-
  Use when turning a local short video of any subject into an evidence-grounded
  Douyin cover brief, cover series, or published-cover replacement. Covers
  keyframe provenance, source-material preservation, deterministic Chinese
  typography, approved hand-brushed titles and illustration alternatives,
  staged review, and release packaging.
compatibility: >-
  Requires local video or keyframes. Deterministic rendering and QA use
  ffmpeg/ffprobe, ImageMagick 7, HarfBuzz, Bash, Python 3, shasum, and the
  bundled locked top-bar font or an explicitly approved override. New
  hand-brushed title candidates use the bundled approved default reference or
  a user-approved alternative plus raster image generation.
---

# Video to Cover Brief

## Overview

Turn a local short video of any subject into an auditable Douyin cover workflow.
Start with evidence and a renderer-neutral brief. Preserve supplied video-frame
material as immutable source pixels, use an image model only where generation is
actually authorized, and finish Chinese typography as either deterministic type
or explicitly approved, pixel-locked artwork.

Always build and present the source-frame direction first. When the user says
that direction is unsatisfactory or explicitly asks to continue with a cartoon
or illustration treatment, the workflow may switch to an evidence-constrained
original illustration. The illustration represents the documented story; it is
never described or packaged as a frame from the video.

The workflow can stop after the brief or continue through generation, local
review, repair, and packaging. A candidate is never a release merely because it
looks plausible at full size.

## When to Use

Use this skill for any local short video that needs an auditable brief, a new
cover, a repaired cover, or a canonical local release package for Douyin. Genre
never determines eligibility; available evidence and the requested cover
workflow do.

## Non-negotiables

- Ground every subject, action, location, top-bar field, and story claim in
  inspected frames, transcript lines, metadata, or an explicit user statement.
- Treat supplied video frames and confirmed cover material as source assets,
  not loose visual references. Do not redraw recognizable people, animals,
  products, characters, interfaces, landmarks, props, poses, or scenery unless
  the user explicitly asks for it.
- Use a source frame for the first cover direction even when the best candidate
  has recorded limitations. Do not self-route to illustration merely because a
  frame is weak, generation is easier, or an illustration may look more dramatic.
- Open `original-illustration` only after the user reacts negatively to the
  source-frame direction or explicitly requests a cartoon or illustration
  revision. Record the exact feedback as the routing trigger. Explicit overall
  dissatisfaction such as “not quite satisfied” authorizes one local cartoon
  candidate; a narrow repair note about typography, color, or cropping does not.
- A third-party or watermarked image with uncertain provenance may inform only
  high-level, non-exclusive ideas such as “red place-name cup beside a canal.”
  Do not attach it to a generation call, remove its watermark, trace it, or copy
  its distinctive composition. Follow the evidence and style contract in
  [references/original-illustration-fallback.md](references/original-illustration-fallback.md)
  when that branch is active.
- Keep generated visual copy empty by default. A short factual place name on a
  generic memory object is allowed only when the user requests it and it is
  recorded in the visible-text allowlist; brands, logos, and unsupported signs
  remain forbidden.
- Treat an approved hand-brushed main title as locked artwork. Do not regenerate,
  retype, stretch, compress, or replace it. Move an intact title layer only when
  the user approves the layout change.
- Give every main title one complete release mode: preserve approved source
  artwork, or compose deterministic type with a pinned local font. A new
  hand-brushed title may pass through `artwork-candidate`, but that state is
  review-only and cannot reach release.
- For requested hand-brushed titles, read
  [references/hand-brushed-title-system.md](references/hand-brushed-title-system.md)
  and run `scripts/check-hand-brushed-title-assets.sh`. Use the bundled default
  for the established series without requesting a repeat upload. Reference
  content supplies style, not new video facts. Keep model lettering at
  `artwork-candidate` until glyph, edge, and profile review plus exact user
  approval promote the canonical layer to `locked-artwork`.
- When no approved hand-brushed workflow or usable reference exists, generate a
  text-free visual and compose the title with a pinned local font. Do not invent
  a font family, imitate an absent artwork style, or leave the title unresolved.
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
- Use `72px` visible top-bar glyph height for new covers in the validated
  `1086×1448` profile while keeping the approved card and component geometry
  unchanged. Treat `48px` as a legacy published-cover value, not a new default.
- Do not retrofit a published legacy cover merely to adopt `72px`. Preserve its
  remaining edit budget unless the user explicitly authorizes the exact edit;
  reserve scarce live edits for factual errors, wrong-cover pairing, severe
  clipping, or similarly material defects.
- Resolve every new top bar from bundled contract
  `lxgw-wenkai-medium-stroke1-v2`: proportional LXGW WenKai Medium with the
  locked SHA-256 and `1px` same-color source stroke before 72px normalization.
  Missing or changed font bytes force `HOLD`; never fall back to a host-system
  Song, Hei, or first-match font. A replacement needs an exact user-approved
  override record.
- Keep only one canonical final package. Preserve rejected and superseded work
  as history, but do not expose multiple folders as competing final versions.

## Inputs

| Input | Required | Use |
| --- | --- | --- |
| Local video or evidence frames | Yes | Establish the real subject, action, and scene. |
| Canvas/profile screenshot | Recommended | Lock canvas and measure the profile cell. |
| Existing cover or clean source plate | Optional | Preserve pixels; repair only named regions. |
| Top-bar font override | Optional | The bundled locked default is automatic; a replacement needs exact user approval. |
| Title artwork or font | Required before final type | Lock artwork or render deterministic type. |
| Title-style reference | Bundled default or user-approved replacement | Resolve the established design from the skill assets without asking for a repeat upload. |
| Existing neighboring covers | Recommended for a series | Judge the three-column grid. |
| Publication state/edit budget | Optional | Treat reported live edits as scarce; never guess. |
| Source-frame feedback | Illustration only | Record dissatisfaction or a cartoon request. |
| Memory object and visible copy | Optional | Preserve one user-selected story cue under an exact visible-text allowlist. |

If the user provides no video or keyframe evidence, stop and request it. A weak
frame set does not independently activate `original-illustration`: present the
best evidence-grounded source-frame direction and let user feedback control the
switch. Do not substitute a verbal summary for visual identity or layout
evidence.

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
7. Score candidate frames for focus, exposure, resolution, subject legibility,
   crop resilience, and title-safe-zone availability. Record rejection reasons
   instead of recycling a visibly failed frame.
8. Cite a frame path and timestamp or transcript line for every material claim.

Finish when beginning/middle/end evidence exists, plausible cover moments have
recorded strengths and limitations, and one best available frame is selected for
the first source-frame direction. If every frame is weak, disclose that limitation
instead of switching modes automatically.

### 2. Profile the content and write the brief

1. Build a concise, evidence-grounded content profile: primary subject, story
   hook, factual context, and material that must remain recognizable.
2. Start with `Visual Source Mode: source-frame`. Record the exact first candidate
   or brief direction presented to the user and its review status. Change the mode
   to `original-illustration` only after qualifying user feedback; for that mode,
   read
   [references/original-illustration-fallback.md](references/original-illustration-fallback.md)
   and record the source-frame attempt, exact feedback trigger, approval state,
   truth claim, memory object, visible-text allowlist, and prompt-manifest path.
3. Read [references/preset-routing.md](references/preset-routing.md),
   [resources/cover-presets.yaml](resources/cover-presets.yaml), and
   [references/top-bar-system.md](references/top-bar-system.md). Run
   `scripts/check-top-bar-font-assets.sh`; a failure keeps the brief at `HOLD`.
4. Prefer a user- or series-approved preset, otherwise use a specialized preset
   when its evidence signals clearly match. Fall back to `source-led-neutral`
   for every other genre; never reject a video merely because no specialized
   preset exists.
5. Resolve a factual top-bar label, palette or source-preservation rule,
   protected source regions, and an intentional collision plan.
6. Propose a concrete Simplified Chinese main title and choose one current state:
   - `locked-artwork`: record the intact approved title source and pixel lock
   - `artwork-candidate`: for a new hand-brushed title, record the approved style
     contract ID, reference path and SHA-256, exact copy and line break, brush
     grammar, fixed or scene-adaptive palette rule, candidate geometry, and
     pending approval; this state forces `HOLD`
   - `deterministic-font`: pin the title font, SHA-256, point size, line break,
     fill, stroke, top edge, and maximum width; do not use auto-fit
7. Read [references/brief-contract.md](references/brief-contract.md), write
   `briefs/<video-id>.md`, validate every field, report `HOLD`, and pause for the
   user's confirmation before image generation.

### 3. Establish the series contract

Before the first cover is generated, lock the following in the brief set or a
package-local contract. Do not edit project governance files without a separate
user request:

- canonical canvas and color space; use `1086×1448` sRGB PNG when matching the
  validated reference implementation, otherwise use the user's measured canvas
- exact top-bar font contract ID, source, file, SHA-256, approval provenance,
  approval-record SHA-256, and `source_stroke_px` from the resolver; use the
  bundled locked default unless an explicit approved override is complete
- top-bar top edge, card height, component height, visible glyph height, color,
  stroke, padding, corner radius, and separator geometry
- for the validated profile, `72px` visible glyph height on new covers without
  enlarging the existing card or component; record any legacy published value
  explicitly instead of silently migrating it
- main-title mode and either its authoritative artwork path or its complete
  deterministic-font contract; an `artwork-candidate` also records its style
  contract ID, reference, exact copy, palette behavior, candidate bounds, and
  approval state
- visible-text allowlist
- source-material protection boundaries
- preview cell dimensions and newest-to-oldest grid order
- naming for candidates, rejected work, and the single canonical final package

Do not silently inherit obsolete geometry from an older series. The bundled
reference profile is a proven default, not authority over explicit user assets.

### 4. Generate in representative batches

After confirmation:

1. For `original-illustration`, follow the linked fallback reference's prompt,
   provenance, and review procedure. Obtain exact approval of the clean base
   before generating the main title; that plate becomes the assembly source.
2. For a series, select three covers that stress different conditions: a short
   top-bar label, a long label, and a subject/title close to the top safe zone.
   For one cover, present up to three local candidates when useful.
3. Use the inspected frame as an edit/composition reference, not permission to
   invent a new subject.
4. For `artwork-candidate`, follow the linked hand-brushed-title reference's
   review and promotion procedure before final assembly. Review at most three
   canonical layers against the chosen frame or approved illustration plate;
   preserve that visual source outside the title alpha.
5. Reuse the approved visual base. If a visual or repair plate is still needed,
   follow the Generation handoff text boundary below. When the subject and title
   are approved, generate only the missing authorized background region.
6. Compose the deterministic top bar with `scripts/render-cover-type.sh`. It
   resolves the bundled locked font automatically, accepts `INPUT OUTPUT LEFT
   [RIGHT]`, rejects unapproved overrides and unstable visible-height
   normalization, and changes only the top-card rectangle.
7. Resolve the main title according to its release mode:
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
8. Build full-size, top-bar, main-title, subject, edge, exact-cell, and
   three-column previews.
9. Present the three as a batch and collect concrete feedback before generating
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

Read [references/release-gate.md](references/release-gate.md) for the complete
artifact, typography, provenance, pixel-protection, and human-review checklist.
Run it after each batch and on the canonical package. The generic checker covers
only the documented mechanical subset; its `PASS` does not replace project
geometry checks, locked-pixel comparisons, source/video review, or user approval.
Any failed or unverified gate returns the candidate to `HOLD`.

### 7. Package and close

1. Collect the exact user-approved files into one numbered package.
2. Write the artifacts and exact TSV schemas from the release-gate reference.
   For `deterministic-font`, the three artifact/approval fields must be
   `none`, `none`, `not-applicable`. For `locked-artwork`, include the canonical
   RGBA layer and its approval record. Never package `artwork-candidate`.
3. Generate the package font manifest and run the generic gate:

   ```bash
   scripts/resolve-top-bar-font.py --format manifest \
     > '<package>/meta/TOPBAR-FONT.json'
   PROJECT_ROOT='<project>' \
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

- pass the brief and inspected video frame for visual content; use the approved
  lettering reference for a title-only call, as its reference specifies
- follow the active mode's linked reference for its prompt and approval steps
- use the measured aspect ratio (`3:4` for the bundled profile); generate visual
  and background layers without text, except exact user-requested memory-object
  copy allowlisted under `original-illustration`; main titles always stay separate
- reserve the deterministic top-bar zone plus the locked-artwork or
  deterministic-font main-title zone; keep an artwork candidate separate until
  approval promotes it to locked artwork
- preserve subject identity and composition from the supplied material
- reject accidental visible text instead of painting another card over it
- for `source-led-neutral`, resolve exact palette, rendering, and mood values
  from the approved series or inspected evidence before calling the renderer;
  never pass placeholders such as `source-preserved` to a renderer

The model may create visual material and review-only hand-brushed title
candidates. Deterministic tools own final assembly, and explicit user approval
owns the transition from candidate lettering to locked final typography.

## Extending the skill

1. Add semantic presets only to `resources/cover-presets.yaml`.
2. Add evidence signals and top-bar copy rules to
   `references/preset-routing.md`; do not turn a new preset into a genre gate.
3. Keep detailed release checks in `references/release-gate.md`.
4. Keep hand-brushed candidate creation and promotion rules in
   `references/hand-brushed-title-system.md`.
5. Keep the bundled default title design machine-readable in
   `resources/hand-brushed-title-default.yaml`; update its asset hashes and tests
   whenever an approved style asset changes.
6. Add repeatable mechanical work to `scripts/`; do not duplicate it in prose.
7. Change the bundled top-bar font or rendering treatment only with a new
   contract ID and hash-bound approval record and review evidence. Follow
   `references/top-bar-system.md`; preserve the superseded contract as history,
   update affected presets/docs/tests, and never relabel existing releases.
8. Add an eval whenever a real failure reveals a reusable boundary.

After skill changes, run the local checks from the skill root:

```bash
bash scripts/check-top-bar-font-assets.sh
bash scripts/check-hand-brushed-title-assets.sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'
```

These validate the skill assets and fixtures, not a live Douyin release.
