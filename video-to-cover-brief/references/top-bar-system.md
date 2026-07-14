# Top-Bar System

Use this reference after selecting the semantic preset. Treat
`resources/cover-presets.yaml#top_bar_system` as the source of truth for IDs,
geometry, palette tokens, and forbidden fallbacks.

## Series Spine

The top bar is the cover series' **spine**, not free decoration. Keep these
properties stable across every cover:

- centered at the top
- one rounded outer capsule
- compact left category cell
- content-driven right context cell
- one vertical divider
- bold Simplified Chinese sans-serif text
- no ornaments outside the capsule

Allow the main title, subject composition, illustration treatment, and scene
color to carry the cover's variation.

## Materialize the Component

1. Copy the category label from the selected preset.
2. Resolve the context with `preset-routing.md`.
3. Form the auditable text as `Category｜Context`.
4. Select a palette variant from the top safe zone's brightness and category.
5. Copy the variant's exact left/right background, text, and border colors.
6. Copy the geometry bounds and state an evidence-specific collision plan.

The visual renderer should draw two cells. The `｜` form exists for the brief,
reporting, and renderers that accept only one text string.

## Baoyu Prompt Handoff

Inline the resolved component into the final `baoyu-cover-image` prompt under a
`MUST PRESERVE` heading. Do not rely on a path to this file or the brief alone.
The prompt must state all of these constraints explicitly:

- Draw one top-centered, two-cell rounded capsule with a compact category cell,
  a content-driven context cell, and one vertical divider.
- Render the brief's category, context, main title, and subtitle verbatim.
- Use the resolved geometry, palette variant, exact color tokens, collision
  plan, and subject-protection rules from the brief.
- Treat the top bar as the only tag, badge, or label component. The top bar,
  main title, and subtitle are the complete visible-text allowlist.
- Add no keyword tags, dates, English copy, logos, watermarks, captions, or
  decorative text, even when the adapter uses `text-rich`.
- Preserve the main title as the dominant text hierarchy; the top bar remains
  compact metadata and must not compete with it.

Before rendering, scan the complete prompt and remove any instruction that asks
for a corner tag, stacked badge, hanging flag, full-width band, external
ornaments, or extra text. A contradictory instruction later in the prompt does
not override the series spine.

## Collision Ladder

When the top center conflicts with a face, dog, landmark, existing sign, or main
action, resolve the collision in this order:

1. Shorten the context while preserving its factual meaning.
2. Choose another evidence-supported keyframe with a calmer top safe zone.
3. Reserve or reconstruct the top safe zone without changing the subject.
4. Reduce the capsule width or type size within the YAML geometry limits.
5. Strengthen the capsule backing with the selected palette tokens.

Do not move the component to a corner, stack its fields, stretch it across the
canvas, or attach flowers, hearts, rays, flags, and decorative lines. If the
collision remains after the ladder, record it in `Layout Rules` and pause before
generation rather than silently breaking the series spine.

## Thumbnail Acceptance

Validate the planned and rendered cover at approximately 25% size:

- Category and context remain readable.
- The capsule is recognizably the same component as other covers.
- The bar does not cover a protected subject or evidence-bearing detail.
- Main-title hierarchy remains dominant.
- Every Chinese character and separator is exact.
- No text appears outside the top bar, main title, and subtitle.
- No external ornament makes the component look like a new structure.
