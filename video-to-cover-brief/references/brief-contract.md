# Cover Brief Contract

Write every brief in this structure. Replace placeholders and remove angle
brackets from the saved file.

```markdown
# Cover Brief

## Publication Risk
State: <unpublished or published>
Edits Used: <user-reported number or unknown>
Online Experimentation: forbidden
Typography Generation: <new-72px or legacy-published-measured>

## Evidence Contract
Video ID: <ID or slug>
Original Video: <path>
Contact Sheet: <path>
Authoritative Subject Source: <frame or cover path>
Locked Material: <identity-bearing subjects/evidence-bearing regions/title pixels>
Generation Authorization: <background-only, clean-top-only, full visual, or none>

## Content Profile
Primary Subject: <evidence-grounded subject phrase>
Story Hook: <visible action, event, contrast, result, or topic>
Factual Context: <confirmed location, event, object, topic, stage, episode, or none>
Protection Priorities: <recognizable and evidence-bearing regions>

## Canvas and Profile
Canvas: <measured canvas; validated default 1086×1448 sRGB PNG>
Profile Cell: <measured cell; validated reference 196×261>
Grid: three columns, newest to oldest
Platform Overlay: protect the measured bottom-left play-count zone

## Top Bar
Text: <single factual label or left · right pair>
Font: <exact file path>
Font SHA-256: <digest>
Card: <top, card height, component height, fill, corner radius>
Typography: <visible glyph height, fill, stroke, kerning; no auto-fit>
Width Rule: content-driven from measured text plus fixed padding
Collision Plan: <evidence-specific clean-source plan>

## Main Title
Text: <evidence-grounded title>
Mode: <artwork-candidate (HOLD only), locked-artwork, or deterministic-font>
Source: <approved canonical title-layer path for locked-artwork; none otherwise>
Style Contract ID: <bundled contract ID, custom-reference, or none>
Style Reference: <approved path for artwork-candidate/reference-derived locked artwork; none otherwise>
Style Reference SHA-256: <digest or none>
Artwork Candidate: <canonical review-layer path, pending, or none>
Artwork Candidate SHA-256: <digest after canonicalization, pending, or none>
Palette Behavior: <fixed, scene-adaptive, or deterministic-font>
Palette: <exact candidate colors, fixed font colors, or pending before generation>
Approval: <pending for artwork-candidate; exact user approval for locked-artwork; not applicable for deterministic-font>
Font: <exact file path for deterministic-font; none for locked-artwork>
Font SHA-256: <digest for deterministic-font; none for locked-artwork>
Typography: <brush grammar, line break, outline/glow, and attached accents for artwork; fixed point size, line break, fill, stroke, kerning, and interline for deterministic-font>
Geometry: <canonical artwork bounds and position, or font top edge and maximum width; no post-approval scaling or font auto-fit>
Protection: <immutable source pixels or deterministic title rectangle>

## Subtitle
Text: <optional editorial note>
Visibility: brief-only; do not render unless the series contract explicitly allows it

## Cover Preset
<semantic preset ID from resources/cover-presets.yaml>
Routing Reason: <approved series rule, matched evidence signals, or general fallback>

## Visual Direction
- Primary Colors: <exact hex values or source-preserved>
- Background Color: <exact hex value or source-preserved>
- Accent Colors: <exact hex values or none>
- Rendering: <source-preserving or another renderer-neutral value>
- Mood: <evidence-grounded mood>
- Decorative Hints: <concise hints>
- Subject Priority: <subject>

## Layout Rules
- Preserve the authoritative video-frame subject and approved title pixels.
- Generate only the region named by Generation Authorization.
- Keep the deterministic top bar as the stable series spine.
- Add no unapproved visible copy, logo, watermark, or badge.
- Keep evidence-bearing subjects outside the profile overlay zone.
- <evidence-specific subject and collision rules>

## Repair and Pixel Locks
Clean Source: <path or pending>
Authorized Region: <geometry/mask or none>
Lock Boundary: <geometry or none>
Expected Outside-Region Difference: 0
Known-Defect Regressions: <list or none yet>

## Required QA
- full-cover overview
- enlarged top bar and lower seam
- main-title crop
- subject-middle crop
- bottom/edge crop
- exact profile cell and three-column grid
- side-by-side video contact sheet comparison

## Release Gate
Status: HOLD
Canonical Package: <planned path or pending>
Upload Recommendation: forbidden before exact user approval and a separate live-action authorization

## Evidence Notes
- Confirmed: <important confirmed facts>
- Uncertain: <important unknowns or none>

## Evidence Index
- <claim>: <frame path @ timestamp, transcript line, or explicit user statement>
```

## Validation

- The video ID, original video, contact sheet, brief, and authoritative source
  all exist or are explicitly pending before generation.
- Every title, top-bar field, location, subject, and story claim has evidence.
- The content profile describes the evidence without forcing a closed genre.
- An unmatched genre routes to `source-led-neutral` instead of being rejected.
- A specialized preset is used only when its evidence signals match or the user
  explicitly approves it.
- `Generation Authorization` is narrower than or equal to the user's request.
- `Locked Material` names recognizable source-frame elements explicitly.
- The canvas and profile cell are measured rather than guessed.
- The font path and SHA-256 are pinned before final typography.
- A new hand-brushed title records its approved style-reference path and hash,
  style contract ID, exact copy and line break, brush grammar, palette behavior,
  canonical bounds, and pending approval before candidate generation. Resolve
  `default-hand-brushed-title-v1` from the skill assets when the established
  series design is requested without a replacement reference; do not request a
  repeat upload.
- Text, locations, subjects, and scenery inside a style reference are not copied
  into the new cover unless separately supported by evidence.
- A scene-adaptive title palette records exact candidate colors derived from the
  inspected source frame; it does not blindly inherit the reference hues.
- New covers in the validated profile use `72px` visible top-bar glyph height
  while preserving the approved card and component geometry.
- Published legacy covers keep their measured typography by default; do not
  consume a scarce live edit solely to migrate `48px` to `72px`.
- The top-bar width is content-driven while height and glyph metrics stay fixed.
- `Main Title.Mode` is complete: an existing or newly approved title is
  `locked-artwork` with an exact canonical source path and SHA-256; a review-only
  hand-brushed title is `artwork-candidate` and forces `HOLD`; other new titles
  are `deterministic-font` with a pinned font, SHA-256, fixed typography, and
  geometry.
- An image-model title candidate never becomes final merely because it looks
  plausible. Exact glyph, line-break, extra-text, edge, profile-cell, and source
  collision review plus explicit user approval are required before promotion to
  `locked-artwork`.
- The clean source predates the defect; a damaged flattened candidate is not
  treated as the only source when a better one exists.
- `Authorized Region` and `Lock Boundary` are precise enough for a zero-diff
  automated check.
- The required QA includes actual profile layout and source-video comparison.
- `Status` remains `HOLD` until the rendered artifacts pass all gates.
