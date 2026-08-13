# Preset and Copy Routing

Keep evidence classification, top-bar copy, visual preset, and renderer adapter
separate. The brief is the portable contract.

## Category mapping

| Category | Preset | Subject priority |
| --- | --- | --- |
| `family-travel` | `travel-family` | real family/travel moment and place |
| `dog-story` | `dog-protagonist` | the dog and its action |

Reject unrelated genres rather than forcing them into a supported preset.

## Top-bar copy

Use one centered cream card. A short factual scene can be a single label; a
confirmed location hierarchy may be a left/right pair separated by a geometric
blue dot.

### Family travel

Prefer, in order:

1. confirmed city/scenic spot pair, such as `盱眙 · 白鹭洲`
2. confirmed province/city pair, such as `江苏 · 兴化`
3. confirmed scenic spot or setting, such as `第一山雪场` or `油菜花田`
4. concrete evidence-supported scene, such as `春日花田`

### Dog story

Use the factual event or setting: `冰雕`, `山野光影`, `录音棚`, `油菜花田`,
`端午粽子`, or another visible hook. Do not repeat `小狗` merely to fill a
category slot, and do not invent a breed.

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
