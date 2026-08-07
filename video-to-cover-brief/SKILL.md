---
name: video-to-cover-brief
description: >-
  Use when turning a local family-travel or dog-centered short video into an
  evidence-grounded Douyin cover brief or replacing an already-published cover.
  Covers keyframe evidence, fixed Simplified Chinese typography, a deterministic
  split-pill series spine, semantic presets, real-size profile-grid previews,
  scarce edit-budget handling, and confirmed handoff to baoyu-cover-image.
---

# Video to Cover Brief

## Overview

Create a renderer-neutral cover brief from a local short video. Route the brief
to a reusable semantic preset and a fixed **series spine**. Generate the visual
layer without text, then compose the top bar and main title deterministically so
short and long copy cannot silently change font size.

The primary output is a self-contained Markdown brief. A confirmed generation
continues through exact-size single-cell and three-column profile previews. Do
not describe a candidate as publishable until the local release gate passes and
the user approves that exact file.

## When to Use

Use this skill for a local family-travel or dog-centered short video that needs
an auditable cover brief, a new cover, or a replacement for a published cover.
Reject unrelated genres and stop before image generation until the user confirms.

## Instructions

### Non-negotiables

- Ground every title, top-bar field, subject, location, and story detail in the
  available video evidence.
- Do not invent a city, scenic spot, dog breed, family member, or story beat.
- Use scene-based fallbacks rather than fake location placeholders.
- Write all cover copy in natural Simplified Chinese.
- Keep the series spine fixed. Never switch it to a corner tag, stacked badge,
  hanging flag, or full-width band to solve a composition collision.
- Keep the top-bar and main-title font sizes fixed. Rewrite, rebreak, reframe, or
  pause instead of using auto-fit, condensed glyphs, or per-cover type scaling.
- Generate a text-free visual layer and apply visible typography with a
  deterministic compositor. Do not ask an image model to draw final Chinese
  text whose metrics must stay consistent across a series.
- Treat a published edit as a scarce release action. Never upload or modify a
  live work merely to preview a candidate.
- Validate at the measured profile-cell size and in a three-column grid. A
  full-size cover or an enlarged contact sheet is not a mobile acceptance test.
- Protect the profile's bottom-left play-count overlay zone; the raw cover is
  not the whole final interface.
- Select a semantic cover preset; do not expose renderer-specific style names
  as the brief's public contract.
- Write the brief before offering image generation.
- Do not generate an image until the user confirms.
- Do not manage `.baoyu-skills/baoyu-cover-image/EXTEND.md` on behalf of
  `baoyu-cover-image`; let that skill own its preferences and first-time setup.

### Inputs

| Input | Required | Use |
| --- | --- | --- |
| Local video path | Yes | Inspect metadata, frames, audio, and visible subjects. |
| Transcript file | Optional | Prefer it for title hooks and the factual summary. |
| Extracted keyframes | Optional | Use them for visual focus and occlusion constraints. |
| User note | Optional | Treat it as intent and verify it against evidence. |
| Publication state | Optional | Record whether this is new or already published. |
| Edits used / remaining | Optional | Preserve the user's reported release budget; never guess. |
| Profile screenshot | Optional | Measure the real three-column cell and calibrate preview size. |
| Existing neighboring covers | Optional | Build the intended profile grid rather than judging one cover alone. |

If no transcript or keyframes exist, inspect the video with available local
tools. Do not install dependencies only to inspect the video. A user summary can
support narrative facts, but it cannot replace visual evidence for subjects,
locations, composition, or generation references.

### Steps

1. **Resolve evidence.**
   - Confirm that the video or supplied evidence exists.
   - Derive `<video-slug>` from the video filename without its extension. Create
     `briefs/evidence/<video-slug>/` in the user's working project.
   - When `ffprobe` is available, save metadata:

     ```bash
     ffprobe -v error -show_format -show_streams -of json '<video>' \
       > 'briefs/evidence/<video-slug>/metadata.json'
     ```

   - Read the duration and extract frames at approximately 10%, 50%, and 90%:

     ```bash
     ffmpeg -ss '<seconds>' -i '<video>' -frames:v 1 -q:v 2 \
       'briefs/evidence/<video-slug>/frame-<timestamp>.jpg'
     ```

   - Inspect all three frames. Add frames around cuts, readable text, or an
     occlusion-sensitive subject. Use supplied keyframes when they provide
     equivalent beginning/middle/end coverage.
   - Gather duration, visible subjects, setting, location clues, emotional tone,
     readable text, and the main action. Cite a frame path and timestamp or a
     transcript line for every material claim.
   - If speech materially affects the title or summary, use a supplied
     transcript or an already available local transcription tool. Otherwise,
     request a transcript or user summary and mark spoken details unknown.
   - If neither local tools nor supplied frames provide visual evidence, stop
     and request keyframes.
   - Finish only when beginning/middle/end evidence exists and every material
     claim has a source.
2. **Classify the video.**
   - Choose exactly one category: `family-travel` or `dog-story`.
   - Choose `family-travel` when the outing or family moment drives the story.
   - Choose `dog-story` when the dog is the protagonist, including AI-generated
     or AI-enhanced footage.
   - When both signals appear, classify by the main emotional focus.
   - If neither category fits, stop without creating a brief.
   - Finish when one supported category is selected and its evidence is cited.
3. **Materialize the preset and series spine.**
   - Read [references/preset-routing.md](references/preset-routing.md).
   - Read [resources/cover-presets.yaml](resources/cover-presets.yaml).
   - Read [references/top-bar-system.md](references/top-bar-system.md).
   - Map the category to one semantic preset.
   - Resolve a two-to-six-character top-bar context, palette variant, exact
     color tokens, and collision plan. Preserve the fixed component, cell
     widths, anchor, and 52 px typography.
   - Write a four-to-eight-character main title. Choose its intentional line
     break, fixed 116 px type, palette fill/stroke, and safe vertical position.
     Rewrite the copy if it cannot fit; do not shrink it.
   - Copy renderer-neutral visual values, fixed typography, and applicable
     composition rules into the brief.
   - Finish when every field required by the brief contract has one resolved,
     evidence-grounded value.
4. **Write and validate the brief.**
   - Read [references/brief-contract.md](references/brief-contract.md).
   - Draft publication risk, top bar, main-title lines, brief-only subtitle,
     typography contract, profile-preview contract, summary, visual focus,
     layout rules, preset ID, and visual direction.
   - Save the exact contract to `briefs/<video-slug>.md`.
   - Verify every required section, evidence citation, preset token, and top-bar
     invariant. At least one cited frame must be suitable for `--ref`.
   - Finish when every validation item in the contract passes.
5. **Report and pause.**
   - Report publication risk, category, top-bar display text and palette variant,
     title lines, preset, preview target, brief path, and evidence directory.
   - State that the release gate is `HOLD`; a brief is not a publishable cover.
   - Ask whether to continue to image generation.
   - Stop before generation until the user confirms.

### Copy Rules

| Field | Rule |
| --- | --- |
| Main title | Use 4-8 Chinese characters; concrete hook, at most two lines and four characters per line. |
| Subtitle | Optional editorial support only; do not render by default. |
| Top-bar category | Use the preset's fixed `旅行` or `萌宠` label. |
| Top-bar context | Use 2-6 factual Chinese characters; shorten before any layout change. |
| Language | Use Simplified Chinese only. |
| Tone | Keep it natural, human, Douyin-friendly, and free of fake hype. |

Prefer an event, reaction, contrast, or specific moment over a lyrical phrase
that merely repeats the visible scene. The same fixed title size applies to
every cover; line breaks absorb length differences.

### Generation Handoff

After the user confirms:

1. Re-read the selected preset and top-bar system in
   [resources/cover-presets.yaml](resources/cover-presets.yaml).
   Read [references/release-gate.md](references/release-gate.md).
2. Keep the exact colors, subject priority, series-spine geometry, palette
   variant, and composition rules materialized in the brief.
3. Read the preset's `adapters.baoyu-cover-image` mapping.
4. Let `baoyu-cover-image` load or complete its own `EXTEND.md` setup. Resume
   this same confirmed generation after setup without changing the brief.
5. Select at least one inspected keyframe that clearly shows the subject and
   composition. Request a reference frame if none is suitable.
6. Read the **Visual-Generation Handoff** section in
   [references/top-bar-system.md](references/top-bar-system.md). Require a
   text-free visual layer with the fixed top-bar and title zones reserved.
7. Invoke `baoyu-cover-image` with:
   - the brief file
   - the mapped `type`, `palette`, `rendering`, `text`, `mood`, and `font`
   - `--aspect 3:4`
   - `--lang zh`
   - `--ref` with the selected frame or supplied references
8. Before generation, scan the saved final prompt and remove every request for
   visible text, tag, badge, logo, sign, caption, or watermark. The adapter's
   `text` value must be `none`.
9. Reject any generated visual layer containing accidental text. Compose the
   fixed top bar and title with `scripts/render-cover-type.sh` or an equivalent
   deterministic vector/canvas step. Never resize the composed text to fit. The
   script accepts an intentional `\\n` title break, for example:

   ```bash
   scripts/render-cover-type.sh visual.png cover.png \
     '萌宠' '录音棚' dog '小狗开麦\n当主播' 190
   ```

10. Build a 196×261 single-cell preview and a three-column profile grid. Use
    `scripts/build-douyin-grid-preview.sh` when ImageMagick is available and
    include supplied neighboring covers in intended newest-to-oldest order:

    ```bash
    SINGLE_CELL_OUTPUT=cell.png \
      scripts/build-douyin-grid-preview.sh grid.png \
      candidate.png neighbor-1.png neighbor-2.png
    ```
11. Run every check in `references/release-gate.md`. Failed or unverified checks
    keep the candidate at `HOLD`; iterate locally without spending a live edit.
12. Present no more than two `LOCAL_READY` finalists with their grid previews.
    Only the exact user-approved file becomes `READY_TO_PUBLISH`.

Keep the brief's exact typography, top bar, and visual direction authoritative
when an adapter is only approximate. Report remaining degradation and hold the
release instead of silently changing the series spine.

### Extending Presets

1. Add one semantic preset to `resources/cover-presets.yaml`.
2. Add or update its category rule in `references/preset-routing.md`.
3. Reuse `top_bar_system`; do not create a per-preset component shape.
4. Add a palette variant only when an existing variant cannot maintain contrast.
5. Keep renderer-independent fields authoritative and adapters nested under the
   preset.
6. Add a new top-level skill only when another workflow needs to consume the
   same preset catalog independently.
