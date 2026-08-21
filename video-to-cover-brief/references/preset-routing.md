# Preset and Copy Routing

Keep the content profile, top-bar copy, visual preset, and renderer adapter
separate. The brief is the portable contract.

Keep the main-title system separate as well. An approved hand-brushed style
comes from the series contract and its style reference, not from a travel, pet,
or other semantic preset. When its palette is scene-adaptive, derive exact title
colors from the inspected source frame while preserving the approved brush,
outline/glow, and composition grammar.

For the established series design, resolve `default-hand-brushed-title-v1` from
`resources/hand-brushed-title-default.yaml`. Use the bundled lettering crop for
generation and do not ask the user to re-upload the approval reference. A
semantic cover preset never overrides or silently replaces this title contract.

## Content profile

Record a small evidence-grounded profile instead of assigning the video to a
closed genre list:

| Field | Record |
| --- | --- |
| Primary subject | Cover-carrying person, animal, product, place, character, interface, or scene. |
| Story hook | Visible action, event, contrast, question, result, or topic. |
| Factual context | Confirmed location, event, object, topic, stage, episode, or none. |
| Protection priorities | Recognizable or evidence-bearing regions that must stay intact. |

Use short natural phrases. Do not expose an invented taxonomy to the user or
reject a video because it lacks a named genre.

## Preset routing

Choose in this order:

1. Use an explicit user- or series-approved preset when one exists.
2. Use a specialized preset when the inspected evidence clearly matches its
   `suitable_for` signals.
3. Use `source-led-neutral` for every other subject. This fallback preserves the
   source palette and primary subject instead of fabricating a genre style.

| Evidence signal | Preset | Subject priority |
| --- | --- | --- |
| no approved specialized preset | `source-led-neutral` | primary evidence subject |
| family outing, parent-child travel, or scenic visit | `travel-family` | family and place |
| dog-led story or action | `dog-protagonist` | the dog and its action |

Presets are adapters behind the routing seam, not eligibility rules. Adding a
new preset improves a known visual treatment; it must not narrow the base
workflow.

## Top-bar copy

Use one centered cream card. A short factual scene can be a single label; a
confirmed location hierarchy may be a left/right pair separated by a geometric
blue dot.

Prefer the shortest factual context that helps distinguish the video:

1. a confirmed hierarchy when both sides matter, such as `盱眙 · 白鹭洲`
2. a confirmed event or action, such as `第一次下厨` or `录音棚`
3. a confirmed object, topic, stage, or episode, such as `开箱实测` or `第二关`
4. a concrete visible setting, such as `春日花田`

Do not prepend a genre label merely to classify the video. Do not invent a
location, product model, animal breed, episode, result, or story beat.

### Copy constraints

- Keep the exact user-confirmed wording when one exists.
- Keep punctuation deterministic. Use the geometric dot for a pair; do not ask
  the image model to draw it.
- Shorten meaning before changing shared typography.
- Let the card grow horizontally for longer labels; never shrink glyphs per
  cover.
- Cite the evidence or explicit user confirmation behind the final wording.

## Visual preset routing

The preset controls palette and composition priorities, not the identity of the
subject. A video-frame subject remains the authoritative source even when the
visual layer receives generative enhancement.

### `source-led-neutral`

- preserve the authoritative frame's palette, lighting, and primary subject
- protect faces, bodies, animals, products, characters, interfaces, readable
  evidence, and the main action when present
- add no genre-coded decoration; use only accents approved by the series
- default to deterministic assembly from source material rather than a full
  redraw

### `travel-family`

- preserve people, faces, clothing, poses, landmarks, signs, boats, bridges,
  water, and scenery from the selected frame when they are part of the material
- use warm natural light and restrained travel accents
- protect hands, faces, and evidence-bearing landmarks from title and platform
  overlays

### `dog-protagonist`

- keep the dog recognizable from the source frame
- protect the face, paws, props, and main action
- use playful accents sparingly; do not replace the dog with a generic breed or
  a newly invented pose

## Generation boundary

Choose the narrowest valid mode:

1. `none`: deterministic typography or source-pixel repair only
2. `clean-top-only`: model supplies a text-free top background plate
3. `background-only`: model supplies a masked background repair source
4. `full-visual`: allowed only for a genuinely new visual whose subject identity
   is not locked to supplied material, or when the user explicitly requests a
   full redraw

When a renderer lacks an exact semantic value, use its closest adapter while
preserving the brief. Report degradation; do not alter the series contract.
