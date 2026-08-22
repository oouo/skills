# Deterministic Top-Bar System

Use this reference when defining or rendering the series top bar. Treat
`resources/cover-presets.yaml#top_bar_system` as the bundled default profile.
If the user supplies an existing approved series, measure that series and record
the resulting project contract instead of forcing a legacy profile onto it.

## Why the top bar is deterministic

The top bar is the repeating series spine. A model-generated bar can change
Chinese glyphs, font weight, padding, height, and corner geometry on every
cover. Those differences become obvious in a three-column grid even when each
cover looks acceptable alone.

Generate the visual layer without the final bar. Compose the bar with a real
font file after generation and verify its pixels mechanically.

## Locked default font

Resolve the top-bar font through
`scripts/resolve-top-bar-font.py` and
`resources/top-bar-font-contract.json`. The bundled default is the proportional
`assets/fonts/LXGWWenKai-Medium.ttf` file with SHA-256
`d4bdeb38a39151d74d084cba5090f8cb7d20bf83eedb78c35939ae70b9f4e3f6`.
Its approved visual treatment is called
`lxgw-wenkai-optical-semibold-v1`: Medium plus a `4px` same-color stroke. The
name does not describe a separate Semibold font file.

An absent, changed, or unreadable bundled font returns `HOLD`; never search the
host system for a replacement. A different font is an explicit override and
must supply `TOP_FONT`, `TOP_FONT_SHA256`, `TOP_FONT_CONTRACT_ID`, and a
`TOP_FONT_APPROVAL_RECORD` that names the exact contract ID and digest. Do not
bundle an alternative whose redistribution license has not been confirmed.

## Validated 1086×1448 profile

The reference implementation uses:

- canvas: `1086×1448`, sRGB PNG
- component: one centered, opaque cream rounded rectangle
- card top: `y=38`
- card height: `96px`
- transparent component height: `106px`
- cream: `rgb(255,248,237)`
- text: `#1654A8`
- source type: 120pt, 2px kerning, 4px same-color stroke, then resampled to a
  fixed visible glyph height of `72px` as one whole label
- corner radius: `22px`
- paired labels: one `14px` blue dot, with `45px` from each adjacent visible
  text edge to the dot
- shadow, glow, outline, bottom strip, and external ornament: none

The locked default font is a skill dependency. Record its contract ID, bundled
path, SHA-256, source, and approval provenance in every new brief and package.
Check every label with HarfBuzz before rendering; `.notdef` or `gid0` is a
release failure.

The 120pt-to-72px step is the validated system's one allowed
`uniform-visible-height` normalization. It preserves the label's aspect ratio
and is not an overflow rescue. Reject a label whose trimmed source ink is below
`60px` at the reference settings because thin-only strings can otherwise be
enlarged into a visibly different type size. Never stretch one axis, normalize
individual glyphs, or apply an extra per-cover scale after this step.

Keep the card and component geometry unchanged when adopting `72px`; this is a
typography revision, not a proportional enlargement of the entire top bar.
At the reference geometry, the visible text leaves about `12px` above and below
inside the `96px` card. Verify long labels and title collisions in the exact
profile cell rather than shrinking the shared type size.

## Legacy published covers

- Treat `48px` as the legacy value used by previously published covers.
- Do not spend a live edit merely to migrate a visually acceptable legacy cover
  to `72px`.
- Start new covers at `72px` and let them form a clear series-version boundary.
- Change an already published cover only with explicit authorization for that
  file, prioritizing factual errors, wrong-cover pairing, severe clipping, and
  other material defects over cosmetic consistency.
- Record the actual legacy value in its brief and package; never relabel a
  `48px` artifact as compliant with the new-cover default.

## Content-driven width

Keep height, top edge, font metrics, and padding fixed. Let width respond to the
measured text group. Short labels stay compact; long labels grow horizontally.
Do not shrink type to rescue a long label.

For a single label:

1. Render the complete label at the fixed source settings and verify its source
   ink height is at least `60px`; then uniformly normalize the whole label to the
   fixed visible glyph height.
2. Add the approved horizontal padding. The bundled renderer uses `180px`
   total as a neutral default; set `CARD_WIDTH` to the measured series width
   when matching an approved project.
3. Round to the series' width step when one exists.
4. Center the resulting card on the canvas.

For a paired label:

1. Render the left and right labels separately with the same source settings,
   source-ink guard, and whole-label normalization.
2. Compute `left width + 45 + 14 + 45 + right width`.
3. Add the approved outer padding and center the group. The bundled renderer's
   neutral paired-label default is `320px` total because the validated project
   intentionally gave long location labels generous breathing room.
4. Draw the blue dot; do not render a separator glyph from the font.

The brief may report paired text as `left · right`. The actual dot is geometry,
not a text character.

## Collision ladder

When the bar or its lower seam collides with the main title or subject:

1. shorten only the factual context, without changing its meaning
2. choose another evidence-supported keyframe with calmer top space
3. use or generate a clean text-free top plate
4. reconstruct only the authorized background region
5. restore approved main-title and subject pixels from the authoritative source
6. pause if no clean solution remains

Do not move the bar to a corner, add decorative ears/flowers, reduce its height,
or shrink the type. Do not place a solid rectangle under it to hide a seam.

## Clean-source compositing

If an old bar or shadow is baked into the base:

- obtain a clean plate from an intact earlier source or a text-free image-model
  output
- use a full-width vertical mask that replaces only the approved top region and
  feathers back into the authoritative cover before the locked boundary
- restore title pixels with a source-derived mask when title strokes cross the
  feather band
- require zero pixel difference beneath the lock boundary

Never edit a rounded rectangle in place by covering it with another rectangle.
That workflow produces the protruding corners, underlines, gray bands, and color
seams that a top-bar QA crop is designed to expose.

## Acceptance

Check both full size and the actual profile cell:

- the centerline first cream pixel is at the contract's top edge
- four interior corner samples match the exact card color
- the visible blue glyph bounding box has the fixed height
- every label passed the source-ink-height guard before normalization
- short and long labels have identical apparent type size
- no old card, shadow, strip, or background patch appears outside the new card
- the bar does not clip or overlap the approved main title
- every Chinese character is exact
- the profile grid shows one coherent series spine

Connected-component bounding boxes can be misleading when a background pixel
has the same color as the card. Prefer centerline and interior-point geometry
checks plus explicit pixel-difference masks.
