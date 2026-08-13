# Cover Brief Contract

Write every brief in this structure. Replace placeholders and remove angle
brackets from the saved file.

```markdown
# Cover Brief

## Publication Risk
State: <unpublished or published>
Edits Used: <user-reported number or unknown>
Online Experimentation: forbidden

## Evidence Contract
Video ID: <ID or slug>
Original Video: <path>
Contact Sheet: <path>
Authoritative Subject Source: <frame or cover path>
Locked Material: <people/dog/props/landmarks/scenery/title pixels>
Generation Authorization: <background-only, clean-top-only, full visual, or none>

## Category
<family-travel or dog-story>

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
Mode: <locked-artwork or deterministic-font>
Source: <approved title-layer path for locked-artwork; none for deterministic-font>
Font: <exact file path for deterministic-font; none for locked-artwork>
Font SHA-256: <digest for deterministic-font; none for locked-artwork>
Typography: <fixed point size, line break, fill, stroke, kerning, and interline>
Geometry: <top edge and maximum width; no auto-fit>
Protection: <immutable source pixels or deterministic title rectangle>

## Subtitle
Text: <optional editorial note>
Visibility: brief-only; do not render unless the series contract explicitly allows it

## Cover Preset
<semantic preset ID from resources/cover-presets.yaml>

## Visual Direction
- Primary Colors: <hex values>
- Background Color: <hex value>
- Accent Colors: <hex values>
- Rendering: <rendering>
- Mood: <mood>
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
- `Generation Authorization` is narrower than or equal to the user's request.
- `Locked Material` names recognizable source-frame elements explicitly.
- The canvas and profile cell are measured rather than guessed.
- The font path and SHA-256 are pinned before final typography.
- The top-bar width is content-driven while height and glyph metrics stay fixed.
- `Main Title.Mode` is complete: an existing approved title is `locked-artwork`
  with an exact source path, while a new title is `deterministic-font` with a
  pinned font, SHA-256, fixed typography, and geometry.
- A new title is never left as an unimplemented direction or delegated to the
  image model for final Chinese rendering.
- The clean source predates the defect; a damaged flattened candidate is not
  treated as the only source when a better one exists.
- `Authorized Region` and `Lock Boundary` are precise enough for a zero-diff
  automated check.
- The required QA includes actual profile layout and source-video comparison.
- `Status` remains `HOLD` until the rendered artifacts pass all gates.
