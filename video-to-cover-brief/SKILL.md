---
name: video-to-cover-brief
description: >-
  Use when turning a local family-travel or dog-centered short video into an
  evidence-grounded Douyin cover brief. Covers keyframe evidence, Simplified
  Chinese copy, a series-consistent split-pill top bar, semantic presets, and
  confirmed handoff to baoyu-cover-image.
---

# Video to Cover Brief

## Overview

Create a renderer-neutral cover brief from a local short video. Route the brief
to a reusable semantic preset and a fixed **series spine**: the same centered
split-pill top bar on every cover, with only its category, context, and palette
variant changing.

The primary output is a self-contained Markdown brief, not a final image. Invoke
`baoyu-cover-image` only after the user confirms.

## When to Use

Use this skill when the user provides a local family-travel or dog-centered
short video and wants an auditable Douyin cover brief before image generation.
Use it when multiple covers must share the same split-pill series spine while
their evidence-grounded copy, palette variant, and composition still vary.

## Instructions

### Non-negotiables

- Ground every title, top-bar field, subject, location, and story detail in the
  available video evidence.
- Do not invent a city, scenic spot, dog breed, family member, or story beat.
- Use scene-based fallbacks rather than fake location placeholders.
- Write all cover copy in natural Simplified Chinese.
- Keep the series spine fixed. Never switch it to a corner tag, stacked badge,
  hanging flag, or full-width band to solve a composition collision.
- Select a semantic cover preset; do not expose renderer-specific style names
  as the brief's public contract.
- Write the brief before offering image generation.
- Do not generate an image until the user confirms.
- Do not create, copy, merge, or overwrite a project's
  `.baoyu-skills/baoyu-cover-image/EXTEND.md`.

### Inputs

| Input | Required | Use |
| --- | --- | --- |
| Local video path | Yes | Inspect metadata, frames, audio, and visible subjects. |
| Transcript file | Optional | Prefer it for title hooks and the factual summary. |
| Extracted keyframes | Optional | Use them for visual focus and occlusion constraints. |
| User note | Optional | Treat it as intent and verify it against evidence. |

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
   - Resolve the top-bar category, factual context, palette variant, exact color
     tokens, and collision plan. Preserve the fixed component and anchor.
   - Copy renderer-neutral visual values and applicable composition rules into
     the brief.
   - Finish when every field required by the brief contract has one resolved,
     evidence-grounded value.
4. **Write and validate the brief.**
   - Read [references/brief-contract.md](references/brief-contract.md).
   - Draft the top bar, title, subtitle, summary, visual focus, layout rules,
     preset ID, and visual direction.
   - Save the exact contract to `briefs/<video-slug>.md`.
   - Verify every required section, evidence citation, preset token, and top-bar
     invariant. At least one cited frame must be suitable for `--ref`.
   - Finish when every validation item in the contract passes.
5. **Report and pause.**
   - Report the category, top-bar display text and palette variant, title,
     subtitle, preset, brief path, and evidence directory.
   - Ask whether to continue to image generation.
   - Stop before generation until the user confirms.

### Copy Rules

| Field | Rule |
| --- | --- |
| Main title | Prefer 6-12 Chinese characters; keep it concrete and visual. |
| Subtitle | Prefer 10-18 Chinese characters; explain the scene or emotion. |
| Top-bar category | Use the preset's fixed `旅行` or `萌宠` label. |
| Top-bar context | Prefer 2-10 factual Chinese characters; shorten before changing layout. |
| Language | Use Simplified Chinese only. |
| Tone | Keep it natural, human, Douyin-friendly, and free of fake hype. |

Keep the main title within two lines and the subtitle within one line. Avoid
generic phrases that could fit any video.

### Generation Handoff

After the user confirms:

1. Re-read the selected preset and top-bar system in
   [resources/cover-presets.yaml](resources/cover-presets.yaml).
2. Keep the exact colors, subject priority, series-spine geometry, palette
   variant, and composition rules materialized in the brief.
3. Read the preset's `adapters.baoyu-cover-image` mapping.
4. Verify that `baoyu-cover-image` already has an `EXTEND.md` at one of its
   documented project, XDG, or user paths. If none exists, ask the user to
   configure that skill separately.
5. Select at least one inspected keyframe that clearly shows the subject and
   composition. Request a reference frame if none is suitable.
6. Invoke `baoyu-cover-image` with:
   - the brief file
   - the mapped `type`, `palette`, `rendering`, `text`, `mood`, and `font`
   - `--aspect 3:4`
   - `--lang zh`
   - `--quick`
   - `--ref` with the selected frame or supplied references
7. Keep the brief's exact top-bar and visual direction authoritative when the
   renderer only offers an approximate adapter value.

Never bootstrap `EXTEND.md` from this skill. Report any material renderer
degradation instead of silently changing the series spine.

### Extending Presets

1. Add one semantic preset to `resources/cover-presets.yaml`.
2. Add or update its category rule in `references/preset-routing.md`.
3. Reuse `top_bar_system`; do not create a per-preset component shape.
4. Add a palette variant only when an existing variant cannot maintain contrast.
5. Keep renderer-independent fields authoritative and adapters nested under the
   preset.
6. Add a new top-level skill only when another workflow needs to consume the
   same preset catalog independently.
