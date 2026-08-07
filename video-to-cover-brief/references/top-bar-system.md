# Top-Bar System

Use this reference after selecting the semantic preset. Treat
`resources/cover-presets.yaml#top_bar_system` as the source of truth for IDs,
geometry, palette tokens, and forbidden fallbacks.

## Series Spine

The top bar is the cover series' **spine**, not free decoration. Keep these
properties stable across every cover:

- centered at the top
- one rounded outer capsule
- fixed-width category and context cells
- one vertical divider
- one fixed Simplified Chinese sans-serif type size
- no ornaments outside the capsule

The fixed cells and type size are deliberate. A generative renderer tends to
shrink longer strings and enlarge shorter ones; that variation becomes obvious
in a three-column profile grid even when each full-size cover looks acceptable.
Allow the subject composition and scene color to carry the cover's variation.

## Materialize the Component

1. Copy the category label from the selected preset.
2. Resolve the context with `preset-routing.md`.
3. Form the auditable text as `Category｜Context`.
4. Select a palette variant from the top safe zone's brightness and category.
5. Copy the variant's exact left/right background, text, and border colors.
6. Copy the fixed 1080×1440 geometry and 52 px type size.
7. State an evidence-specific collision plan that protects the fixed component.

The visible component uses two cells. The `｜` form exists only for the brief
and reporting. Do not render the separator glyph in addition to the divider.

Never ask a generative image model to typeset the final top bar. Generate the
visual layer without text, then compose the capsule and its text with
`scripts/render-cover-type.sh` or an equivalent deterministic vector/canvas
step. Deterministic composition is what makes the font size, cell widths,
spelling, and divider repeatable across the series.

## Visual-Generation Handoff

Invoke `baoyu-cover-image` with `--text none`. Its saved prompt must state:

- Render a text-free 3:4 visual layer.
- Reserve the brief's fixed top-bar and title safe zones.
- Keep the protected face, dog, landmark, and main action outside those zones.
- Add no letters, Chinese characters, numbers, tags, signs, logos, or watermark.
- Preserve the supplied subject's identity instead of replacing it with a
  generic person or dog.

After generation, scan the visual layer for accidental text before composing
the deterministic typography. Reject rather than paint over material text that
would remain visible.

## Collision Ladder

When the top center conflicts with a face, dog, landmark, existing sign, or main
action, resolve the collision in this order:

1. Shorten the context while preserving its factual meaning.
2. Choose another evidence-supported keyframe with a calmer top safe zone.
3. Reserve or reconstruct the top safe zone without changing the subject.
4. Recompose or recrop the text-free visual layer.
5. Pause if the collision remains.

Do not move the component to a corner, stack its fields, stretch it across the
canvas, or attach flowers, hearts, rays, flags, and decorative lines. If the
collision remains after the ladder, record it in `Layout Rules` and pause before
generation rather than silently breaking the series spine. Never reduce the
52 px type size to rescue an overlong context.

## Thumbnail Acceptance

Full-size inspection catches spelling; it does not prove mobile usability.
Validate the planned and rendered cover in both of these views:

- one exact 196×261 profile cell, viewed without zoom
- one three-column grid in intended profile order, including existing covers
  when the user supplies them

The 196×261 baseline comes from the supplied real profile result. If a newer
user screenshot provides a different measured cell, use that measurement and
record it in the brief instead of guessing.

Acceptance requires:

- Category and context remain readable.
- The capsule is recognizably the same component as other covers.
- Category and context use the same apparent type size on short and long labels.
- The bar does not cover a protected subject or evidence-bearing detail.
- Main-title hierarchy remains dominant.
- Every Chinese character and separator is exact.
- No text appears outside the top bar and main title.
- No external ornament makes the component look like a new structure.
- The grid does not expose font-size drift, repeated color blocks, or a single
  cover that breaks the series spine.
