# Preset Routing

Use this reference after classifying the video. Keep category detection separate
from visual preset definitions.

## Category Mapping

| Category | Cover preset | Reason |
| --- | --- | --- |
| `family-travel` | `travel-family` | The family outing or shared travel memory drives the story. |
| `dog-story` | `dog-protagonist` | The dog drives the story; AI is a production detail. |

Do not write the legacy IDs `travel-family-cover` or `dog-ai-cover` into new
briefs. They were renderer-routing labels rather than reusable preset names.
Do not use the legacy category `dog-ai`; use `dog-story` and record AI
generation or enhancement only as an evidence attribute when confirmed.

## Banner Content

For `family-travel`, prefer factual location fields:

```text
Primary: <city>
Secondary: <scenic spot>
```

If the scenic spot is unknown, use `Secondary: 出游地`. If the city is also
unknown, use `Primary: 城市` rather than inventing one.

For `dog-story`, prefer a factual location and scene:

```text
Primary: <city>
Secondary: <scene>
```

If city evidence is weak but the theme and scene are clear, use:

```text
Primary: <theme>
Secondary: <scene>
```

Safe theme fallbacks include `萌宠` and `小狗`. Use a breed only when the
evidence supports it.

## Banner Treatment

Start with the selected preset's `banner_default`. Use its `banner_fallback`
when the default would cover a face, dog, landmark, hand, readable sign, or the
main action.

Supported treatments:

| Treatment | Use |
| --- | --- |
| `compact-stacked-corner` | A clean top-left or top-center area can hold a two-line tag. |
| `single-line-bar` | Important content occupies the top area; minimize occlusion. |
| `top-thin-band` | Location context matters and the top edge is visually calm. |
| `small-corner-tag` | The central subject must dominate the cover. |

Render `single-line-bar` as `Primary｜Secondary`. Keep every other treatment as
two structured fields; do not force decorative punctuation into the content.

## Preset Materialization

Copy these values from `resources/cover-presets.yaml` into `## Visual Direction`
in the brief:

- primary colors
- background color
- accent colors
- rendering
- mood
- font
- decorative hints
- subject priority

Copy the applicable composition rules into `## Layout Rules`. This makes the
brief portable and prevents a renderer from needing project-level configuration.

## Renderer Boundary

Treat `adapters` as invocation mappings only. Do not copy adapter values into
the semantic preset ID, and do not install them into a project's preference
files.

When a renderer does not support an exact value:

1. Preserve the brief's exact visual direction in the generation prompt.
2. Use the adapter's closest supported fallback.
3. Report any material degradation instead of silently changing the style.
