# Preset Routing

Read this reference after classifying the video. Keep evidence classification,
top-bar copy, and preset values separate.

## Category Mapping

| Category | Cover preset | Top-bar category | Reason |
| --- | --- | --- | --- |
| `family-travel` | `travel-family` | `旅行` | The outing or family memory drives the story. |
| `dog-story` | `dog-protagonist` | `萌宠` | The dog drives the story. |

Do not use the legacy category `dog-ai` or the legacy preset IDs
`travel-family-cover` and `dog-ai-cover`.

## Top-Bar Context

The left field is fixed by the selected preset. Resolve only the right `Context`
field from evidence.

### Family travel

Use the most specific factual context that remains readable:

1. Confirmed city and scenic spot: `盱眙 · 白鹭洲`
2. Confirmed province/city pair: `江苏 · 兴化`
3. Confirmed scenic spot or setting only: `油菜花田`
4. No location evidence but a clear visual scene: `湖边散步`, `春日花田`, or
   another concrete scene supported by frames

Do not write placeholder locations such as `城市` or `出游地`. A concrete scene
is more honest and more useful to viewers than a fake location slot.

### Dog story

Describe the factual scene, event, or visual hook:

- `冰雕`
- `录音棚`
- `油菜花田`
- `山野光影`
- `端午粽子`

Prefer `萌宠` as the fixed category. Do not spend the context field repeating
`小狗`, and do not use a breed unless evidence confirms it.

### Copy constraints

- Prefer 2-10 Chinese characters for `Context`.
- Join two confirmed location levels with ` · `.
- Do not put `｜` inside `Context`; the renderer uses it between the two cells.
- Shorten context before changing geometry or hiding text.
- Cite the evidence or named fallback that supports the final context.

## Palette Routing

Select the palette variant from `top_bar_system.palette_variants`:

| Condition | Variant |
| --- | --- |
| `family-travel` with a bright or midtone top safe zone | `travel-day` |
| `family-travel` with a predominantly dark, low-light top safe zone | `travel-night` |
| `dog-story` | `dog` |

Judge the top safe zone, not the average brightness of the entire frame. Preserve
the selected variant's exact tokens. Do not apply one-off seasonal color shifts
inside a brief; add a named palette variant to the YAML source of truth instead.

## Preset Materialization

Copy these values into the brief:

- semantic preset ID
- top-bar system ID
- category label
- evidence-grounded context
- display text
- palette variant and exact color tokens
- top-bar geometry and collision plan
- primary colors, background color, and accent colors
- rendering, mood, font, decorative hints, and subject priority
- applicable composition rules

The brief must remain portable: a renderer should not need project preferences
to reconstruct the intended series spine.

## Renderer Boundary

Treat `adapters` as invocation mappings only. Do not copy adapter values into
the semantic preset ID or install them into project preference files.

When a renderer lacks an exact value:

1. Preserve the brief's exact visual and top-bar direction in the prompt.
2. Use the adapter's closest supported fallback.
3. Report material degradation instead of changing the series spine.
