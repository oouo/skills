# Cover Brief Contract

Write every brief in this exact structure. Replace all placeholders and remove
all angle brackets from the saved file.

```markdown
# Cover Brief

## Publication Risk
State: <unpublished or published>
Edits Used: <user-reported number or unknown>
Remaining Edit Budget: <user-reported number or unknown>
Online Experimentation: forbidden

## Category
<family-travel or dog-story>

## Top Bar
System: <centered-split-pill>
Category: <旅行 or 萌宠>
Context: <factual location or scene>
Display Text: <Category｜Context>
Palette Variant: <travel-day, travel-night, or dog>
Left Cell: <background hex / text hex>
Right Cell: <background hex / text hex>
Border: <hex>
Geometry: <1080×1440 canvas; top 43 px; height 112 px; total width 610 px;
left cell 180 px; right cell 430 px; border 4 px>
Typography: <52 px; fixed; no auto-fit or glyph scaling>
Collision Plan: <evidence-specific plan that preserves the fixed component>

## Main Title
Text: <4-8 Chinese characters>
Render Lines:
- <line 1, at most four characters>
- <line 2 when needed, at most four characters>

## Subtitle
Text: <optional editorial supporting copy>
Visibility: brief-only; do not render

## Typography Contract
Canonical Canvas: 1080×1440
Main Title Font Role: <preset main_title_family>
Main Title Size: 116 px fixed
Main Title Top: <default 190 px or evidence-supported fixed value>
Main Title Fill: <selected palette title_fill>
Main Title Stroke: <selected palette title_stroke>
Auto-fit: forbidden; rewrite or rebreak before shrinking
Visible Text: top-bar category, top-bar context, and main title only

## Profile Preview
Cell: <196×261 or measured user-screenshot cell>
Grid: three columns
Platform Overlay: protect the bottom-left 72×32 px play-count zone
Existing Covers: <paths or none supplied>
Required Artifacts: <single-cell preview path; grid-preview path after generation>

## Video Summary
<2-4 factual sentences describing the actual content>

## Visual Focus
- <focus 1>
- <focus 2>
- <focus 3>

## Cover Preset
<semantic preset ID from resources/cover-presets.yaml>

## Visual Direction
- Primary Colors: <hex values>
- Background Color: <hex value>
- Accent Colors: <hex values>
- Rendering: <rendering>
- Mood: <mood>
- Font: <font>
- Decorative Hints: <concise hints>
- Subject Priority: <subject>

## Layout Rules
- <preset composition rule 1>
- <preset composition rule 2>
- Keep the centered split-pill top bar as the stable series spine.
- Generate a text-free visual layer, then compose typography deterministically.
- Treat the Top Bar and Main Title as the complete visible-text allowlist.
- Do not add keyword tags, dates, logos, watermarks, or decorative copy.
- <evidence-specific subject protection rule>
- Keep evidence-bearing faces, paws, hands, and small subjects outside the
  profile play-count overlay zone.
- <mobile thumbnail rule>

## Release Gate
Status: HOLD until the rendered single-cell and grid previews pass local review
Upload Recommendation: do not upload or edit the published work before explicit
user approval of the final local preview

## Evidence Notes
- Confirmed: <important confirmed facts>
- Uncertain: <important unknowns or none>

## Evidence Index
- <claim or fallback>: <frame path @ timestamp, transcript line, user note, or
  documented fallback>
```

## Validation

Before reporting completion, verify:

- `Category` contains one supported evidence category.
- `Cover Preset` contains one ID present in `resources/cover-presets.yaml`.
- `Visual Direction` matches the selected preset exactly.
- `Publication Risk` records user-reported edit usage when available; unknown
  is treated as scarce rather than assumed unlimited.
- `Top Bar` uses `centered-split-pill`, the preset's fixed category, one factual
  context, and one valid palette variant.
- Top-bar geometry and colors match `top_bar_system` exactly.
- `Context` is at most six Chinese characters and does not force a font-size
  change; a longer factual location stays in the evidence instead.
- `Display Text` equals `Category｜Context` for audit reporting.
- `Collision Plan` follows the collision ladder without changing the component
  shape, anchor, cell widths, or type size.
- The title and subtitle are grounded in evidence.
- The main title is at most eight Chinese characters, uses at most two
  intentional lines, and never relies on auto-fit.
- The subtitle is brief-only unless the user explicitly changes the series
  contract and revalidates the whole profile grid.
- `Layout Rules` include preset rules, the series-spine invariant, and
  evidence-specific subject protection.
- `Layout Rules` make the top bar and main title the complete
  visible-text allowlist and forbid all additional copy.
- `Evidence Notes` expose uncertainty instead of hiding it.
- `Evidence Index` cites every material title, top-bar, summary, subject, and
  location claim with a frame timestamp, transcript line, user note, or named
  fallback from `preset-routing.md`.
- At least one cited frame is suitable for the generation `--ref` handoff.
- `Profile Preview` names the actual-size cell and three-column grid artifacts.
- `Profile Preview` protects the bottom-left play-count overlay instead of
  treating the raw cover as the complete visible result.
- The planned top bar and title pass the exact-size checks in
  `top-bar-system.md`; full-size readability alone is not sufficient.
- `Release Gate` remains `HOLD` before rendered local previews and explicit user
  approval. Never use a live upload or published edit as a preview mechanism.
- The file exists at `briefs/<video-slug>.md`.
