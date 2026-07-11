# Cover Brief Contract

Write every brief in this exact structure. Replace all placeholders and remove
all angle brackets from the saved file.

```markdown
# Cover Brief

## Category
<family-travel or dog-story>

## Top Banner
Primary: <city or theme>
Secondary: <scenic spot or scene>

## Banner Treatment
<compact-stacked-corner, single-line-bar, top-thin-band, or small-corner-tag>

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
- <evidence-specific occlusion rule>
- <mobile thumbnail rule>

## Evidence Notes
- Confirmed: <important confirmed facts>
- Uncertain: <important unknowns or none>

## Evidence Index
- <claim or fallback>: <frame path @ timestamp, transcript path + line, user note, or documented fallback>
```

## Validation

Before reporting completion, verify:

- `Category` contains one supported evidence category.
- `Cover Preset` contains one ID present in `resources/cover-presets.yaml`.
- `Visual Direction` matches that preset exactly.
- The title and subtitle are grounded in evidence.
- The banner uses factual values or documented fallbacks.
- `Layout Rules` include preset rules and evidence-specific subject protection.
- `Evidence Notes` expose uncertainty instead of hiding it.
- `Evidence Index` cites every material title, banner, summary, subject, and
  location claim with a frame timestamp, transcript line, user note, or named
  fallback from `preset-routing.md`.
- At least one cited frame is suitable for the generation `--ref` handoff.
- The file exists at `briefs/<video-slug>.md`.
