# Cover Brief Contract

Write every brief in this exact structure. Replace all placeholders and remove
all angle brackets from the saved file.

```markdown
# Cover Brief

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
Geometry: <top-center; top margin; height; preferred width and hard maximum>
Collision Plan: <evidence-specific plan that preserves the fixed component>

## Main Title
<6-12 Chinese characters preferred>

## Subtitle
<10-18 Chinese characters preferred>

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
- <evidence-specific subject protection rule>
- <mobile thumbnail rule>

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
- `Top Bar` uses `centered-split-pill`, the preset's fixed category, one factual
  context, and one valid palette variant.
- Top-bar geometry and colors match `top_bar_system` exactly.
- `Display Text` equals `Category｜Context`; two-level locations use ` · ` inside
  `Context`.
- `Collision Plan` follows the collision ladder without changing the component
  shape or anchor.
- The title and subtitle are grounded in evidence.
- `Layout Rules` include preset rules, the series-spine invariant, and
  evidence-specific subject protection.
- `Evidence Notes` expose uncertainty instead of hiding it.
- `Evidence Index` cites every material title, top-bar, summary, subject, and
  location claim with a frame timestamp, transcript line, user note, or named
  fallback from `preset-routing.md`.
- At least one cited frame is suitable for the generation `--ref` handoff.
- The planned top bar passes the 25% thumbnail checks in `top-bar-system.md`.
- The file exists at `briefs/<video-slug>.md`.
