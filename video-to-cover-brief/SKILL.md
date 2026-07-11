---
name: video-to-cover-brief
description: >-
  Use when turning a local family-travel or dog-centered short video into an
  evidence-grounded Douyin cover brief. Covers keyframe inspection, auditable
  evidence, Chinese cover copy, and confirmed handoff to baoyu-cover-image.
---

# Video to Cover Brief

## Overview

Create a renderer-neutral cover brief from a local short video. Route the brief
to a reusable semantic preset, then invoke `baoyu-cover-image` only after the
user confirms.

The primary output is a Markdown brief, not a final image. Keep the brief
self-contained so another renderer can reproduce its visual direction without
loading project-level preferences.

## When to Use

Use this skill only for local family-travel or dog-centered short videos. Stop
without writing a brief when neither category fits.

## Instructions

### Core Rules

- Ground every title, banner field, subject, location, and story detail in the
  available video evidence.
- Do not invent a city, scenic spot, dog breed, family member, or story beat.
- Use explicit fallback labels when evidence is weak.
- Write all cover copy in natural Simplified Chinese.
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
support narrative facts, but it cannot replace visual evidence for subject,
location, composition, or generation references.

### Workflow

1. **Resolve evidence.**
   - Confirm that the video or supplied evidence exists.
   - Derive `<video-slug>` from the video filename without its extension. In the
     user's working project, create `briefs/evidence/<video-slug>/` for durable
     inspection artifacts.
   - When `ffprobe` is available, save metadata:

     ```bash
     ffprobe -v error -show_format -show_streams -of json '<video>' \
       > 'briefs/evidence/<video-slug>/metadata.json'
     ```

   - Read the duration, then extract frames at approximately 10%, 50%, and 90%:

     ```bash
     ffmpeg -ss '<seconds>' -i '<video>' -frames:v 1 -q:v 2 \
       'briefs/evidence/<video-slug>/frame-<timestamp>.jpg'
     ```

   - Inspect all three frames. Add more frames around cuts, readable text, or an
     occlusion-sensitive subject. Use supplied keyframes instead when they give
     equivalent beginning/middle/end coverage.
   - Gather duration, visible subjects, setting, location clues, emotional tone,
     readable on-screen text, and the main action. Cite the frame path and
     timestamp or transcript line for every material claim.
   - If speech materially affects the story, title, or summary, use a supplied
     transcript or an already available local transcription tool. Save or cite
     the transcript with line numbers. If neither exists, request a transcript
     or user summary and mark spoken details as unknown.
   - Record uncertain details instead of guessing.
   - If neither local tools nor supplied frames can provide visual evidence,
     stop and request keyframes; do not write the brief.
   - Finish when beginning/middle/end evidence exists and every material claim
     has a source.
2. **Classify the video.**
   - Choose exactly one category: `family-travel` or `dog-story`.
   - Choose `family-travel` when the outing or family moment is the core story.
   - Choose `dog-story` when the dog is the actual protagonist, whether or not the
     footage was AI-generated or AI-enhanced.
   - When both signals appear, classify by the main emotional focus.
   - If neither category fits, report that this skill does not cover the video
     and stop without creating a brief.
3. **Select and materialize a cover preset.**
   - Read [references/preset-routing.md](references/preset-routing.md).
   - Read [resources/cover-presets.yaml](resources/cover-presets.yaml).
   - Map the category to one preset and copy its renderer-neutral visual values
     into the brief.
   - Treat a preset as a reusable visual contract, not a `baoyu-cover-image`
     `--style` value.
4. **Write the brief.**
   - Read [references/brief-contract.md](references/brief-contract.md).
   - Draft the banner, title, subtitle, summary, visual focus, layout rules,
     preset ID, and visual direction.
   - Save the exact contract to `briefs/<video-slug>.md`, where `<video-slug>`
     is the video filename without its extension.
   - Verify that every required section exists and every factual statement is
     traceable to evidence or a documented fallback.
5. **Report and pause.**
   - Report the category, banner fields, banner treatment, title, subtitle,
     cover preset, brief path, and evidence directory.
   - Ask whether to continue to image generation.
   - Stop before generation until the user confirms.

### Copy Rules

| Field | Rule |
| --- | --- |
| Main title | Prefer 6-12 Chinese characters; keep it concrete and visual. |
| Subtitle | Prefer 10-18 Chinese characters; explain the scene or emotion. |
| Language | Use Simplified Chinese only. |
| Tone | Keep it natural, human, Douyin-friendly, and free of fake hype. |

Avoid generic phrases and titles that could fit any video. Keep the main title
within two lines and the subtitle within one line.

### Generation Handoff

After the user confirms:

1. Re-read the selected entry in
   [resources/cover-presets.yaml](resources/cover-presets.yaml).
2. Keep the exact colors, subject priority, banner treatment, and composition
   rules already materialized in the brief.
3. Read the preset's `adapters.baoyu-cover-image` mapping.
4. Verify that `baoyu-cover-image` already has an `EXTEND.md` at one of its
   documented project, XDG, or user paths. If none exists, stop and ask the user
   to configure that skill separately; do not enter its first-time setup from
   this workflow.
5. Select at least one inspected keyframe that clearly shows the subject and
   composition. Stop and request a reference frame if none is suitable.
6. Invoke `baoyu-cover-image` with:
   - the brief file
   - the mapped `type`, `palette`, `rendering`, `text`, `mood`, and `font`
   - `--aspect 3:4`
   - `--lang zh`
   - `--quick`
   - `--ref` with the selected keyframe or supplied reference images
7. Let `baoyu-cover-image` load its existing preferences. Never
   bootstrap its `EXTEND.md` from this skill.

The adapter palette is a supported renderer fallback. The exact palette and
composition in the brief remain authoritative. Do not invent scenery or ignore
the supplied video frame when a suitable reference image exists.

### Extending Presets

Add a new cover style without expanding the core workflow:

1. Add one semantic preset to `resources/cover-presets.yaml`.
2. Add or update a category-to-preset rule in
   `references/preset-routing.md`.
3. Keep renderer-independent fields authoritative.
4. Add renderer adapters under the preset instead of adding renderer-specific
   fields to the brief contract.
5. Add a new top-level skill only when another workflow needs to consume the
   same preset catalog independently.
