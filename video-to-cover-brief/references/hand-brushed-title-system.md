# Reference-Guided Hand-Brushed Main Titles

Read this reference when the user or an approved series contract requires a
custom painted or hand-brushed main title instead of a reusable font. This is a
candidate-approval workflow, not permission to treat arbitrary model text as
final typography.

## Validated default series design

Resolve the machine-readable contract from
`resources/hand-brushed-title-default.yaml`. Its stable ID is
`default-hand-brushed-title-v1`.

The skill bundles two hash-bound assets:

| Asset | Role | Contract |
| --- | --- | --- |
| `assets/approved-hand-brushed-title-reference.png` | Approval provenance and full-cover relationship | `1086×1448` sRGB PNG; SHA-256 `d4f53173e8a60b120f7f87e0916ff48dc0524ec650a891553c2d80503cd23f3b` |
| `assets/approved-hand-brushed-title-lettering-crop.png` | Preferred generation reference with top bar and scene removed | `1086×520` sRGB PNG; SHA-256 `91c6c54ead6883ee872a19ecb408b22b50d824dc3d2279e30a49631e2945564e` |

The approved title behavior is two interlocking lines, expressive
variable-width brush strokes, dry-brush terminals and long swashes, irregular
character scale and baseline, high-saturation color groups, and a warm-white
outline or glow that preserves profile-cell readability. The full reference's
title plus attached accents occupy approximately `977×445+78+171`; its top-bar
card is separate typography and is not part of the hand-brushed design.

The reference image's visible words, location, scenery, subject, and palette are
not instructions for a new cover. They demonstrate the approved title grammar
and layout relationship only.

## Resolve the reference without a repeat upload

When the user asks for the established series hand-brushed design and does not
provide a replacement reference:

1. Resolve `default-hand-brushed-title-v1` from the bundled YAML contract.
2. Verify both asset SHA-256 values before using them.
3. Record the full reference path and hash as provenance in the brief.
4. Pass the lettering crop as the image-generation style reference.
5. Do not ask the user to re-upload or paste the same reference again.

Run the bundled verifier from the skill root when a shell is available:

```bash
scripts/check-hand-brushed-title-assets.sh
```

Stop and report an asset-integrity failure if a path is missing or a digest
does not match. Ask for a new reference only when the user requests a materially
different lettering system, explicitly replaces the default, or the bundled
asset cannot be recovered.

## Route into the workflow

Use `artwork-candidate` only when all of these are true:

1. The user or approved series contract explicitly wants hand-brushed artwork.
2. The bundled default or a user-approved replacement exists and its path and
   SHA-256 are recorded.
3. The exact Simplified Chinese copy and intentional line break are confirmed in
   the brief.
4. The brief remains `HOLD` until the user approves one exact canonical layer.

Otherwise use `deterministic-font`. Do not guess a font that merely resembles
the reference and do not improvise an undocumented title style.

## Derive the candidate contract

Inspect the style reference and the authoritative visual source separately.
Use the selected video frame in `source-frame` mode or the exact approved plate
in `original-illustration` mode; keep the original video as factual evidence.
Record:

- brush anatomy: stroke weight range, pressure contrast, dry-brush texture,
  exposed tips, swashes, and allowed overlaps
- composition: line count, character scale variation, baseline irregularity,
  interline overlap, attached decorative marks, and maximum occupied bounds
- edge treatment: outline or glow color, thickness range, softness, and whether
  it belongs to the locked artwork
- palette behavior: fixed or scene-adaptive
- legibility behavior: target profile cell, minimum visual separation from the
  background, and which strokes must survive downsampling

For a scene-adaptive palette, do not copy the reference's hues by default.
Choose exact candidate colors from that visual source after inspection:

1. Avoid the dominant background colors behind each title segment.
2. Prefer two or three high-saturation roles with clear warm/cool or
   light/dark separation.
3. Preserve the series' warm-white outline or glow unless the approved reference
   contract says otherwise.
4. Record the exact hex values in the candidate brief before generation.
5. Check the colors on the full cover and the exact profile cell; aesthetic
   harmony at full size does not rescue low thumbnail contrast.

## Create a review batch

Generate the lettering separately from the cover visual:

1. Provide the approved style reference as a style reference only.
   For `default-hand-brushed-title-v1`, use the bundled lettering crop for the
   generation call and retain the full image only as provenance evidence.
2. Quote the exact Chinese title and state the intentional line break.
3. Request one isolated title group, transparent background when supported,
   and no location, caption, logo, watermark, Latin text, numbers, or extra
   Chinese.
4. Describe the measured brush grammar, candidate palette, outline or glow,
   attached accents, and target bounds. Do not ask for a named font.
5. Generate at most three candidates. Reject obvious misspellings or alien
   glyphs before presenting them, but do not silently repair or approve the
   remaining text on the user's behalf.
6. Before review, normalize each candidate onto the canonical transparent
   canvas and place it at its proposed final size and coordinates. This
   canonicalized layer, not the raw model output, is the object under review.
7. Present an enlarged isolated-title view and an exact-cell cover mockup for
   each surviving candidate. Keep the authoritative visual source unchanged in
   the mockup outside the candidate alpha.

## Approval gate

Keep every candidate at `HOLD` until the user confirms one exact candidate.
Review all of the following:

- every Chinese character is the requested character, not a visually similar
  substitute or invented component
- character order and line break match the brief
- no extra visible text, pseudo-text, accidental punctuation, or watermark
- no important stroke, dry-brush cap, outline, glow, or attached accent is
  clipped
- irregularity reads as intentional hand lettering, not broken typography
- the title is legible at the exact profile-cell size
- palette contrasts with the actual visual source and follows the approved fixed
  or scene-adaptive rule
- title placement does not hide protected source evidence

OCR may assist triage but cannot approve stylized Chinese. Human visual review
and the user's explicit selection are required.

## Promote and lock

After explicit approval:

1. Record the selected canonical RGBA layer path, dimensions, position, and
   SHA-256.
2. Change `Main Title.Mode` from `artwork-candidate` to `locked-artwork`.
3. Record the approval in the package-local review record.
4. Composite only the approved layer's exact pixels and alpha onto the
   authoritative source.
5. Do not regenerate, retype, recolor, stretch, compress, or rescale the locked
   layer. A layout change requires approval to move the intact layer as a unit.
6. Require zero pixel difference outside the approved title alpha and every
   separately authorized region.

If the user rejects every candidate, preserve them as rejected history and
return to the candidate contract or brief. Do not promote the least-bad option.
