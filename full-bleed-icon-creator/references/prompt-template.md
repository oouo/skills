# Generation Prompt Template

Read this file when writing the final prompt for a new or substantially
redesigned full-bleed icon. Replace every angle-bracket placeholder.

```text
Create a brand-new full-bleed square module icon from a blank canvas.

Subject:
- Main character: <one anthropomorphic subject-native broad body>.
- Function: <the module action>.
- Outcome: <the visible result>.
- Supporting symbols: <one to three tightly connected symbols>.
- Semantic order: <how the layers show action then outcome>.

Palette:
- Use <background color> from edge to edge as a high-contrast, nearly uniform
  background with only subtle paper grain.
- Use <subject colors> for a clear small-size silhouette.

Style lock:
- Use a polished kawaii editorial vector-sticker style with slightly organic
  hand-shaped contours, thick near-black hand-inked subject outlines, layered
  paper-cut forms, subject-contained tactile speckle, restrained highlights,
  compact depth shading, crisp contrast, and a friendly expression.
- Keep one coherent layered character cluster. Put supporting states inside the
  body or tightly overlap them with its organic silhouette.
- Use no words, letters, numbers, watermark, copied logo, or literal brand
  geometry.
- Produce tactile authored illustration, not glossy 3D rendering or
  mechanically perfect flat geometry.

Full-bleed lock:
- The final delivery is an 800x800 fully opaque sRGB image. Fill every literal
  corner. The host application applies rounded corners.
- Use no inset tile, enclosing badge, ring, frame, halo, vignette, scenery, or
  floor plane.
- Let the main character's own orb, cloud, panel, ticket, tag, pin, bubble, or
  other organic body supply most of the top, bottom, left, and right reach.
- Target a QA subject mask 740-780px wide and 740-780px high, with 4-32px
  clearance at all four cardinal edges.
- Keep the mask centroid within 32px of (399.5,399.5) and all subject pixels
  inside a 160px round-rectangle proxy.
- Treat those measurements as acceptance limits, never as a request for a
  cross, plus sign, four handles, paired side cards, or detached protrusions.

Acceptance:
- Render the complete square without a baked corner radius.
- Preserve a strong silhouette at 120px, 64px, 40px, and 32px.
- If any semantic, style, or geometry requirement fails, discard the complete
  draft and regenerate from this prompt. Do not repair an older raster by
  scaling, cropping, stretching, moving, masking, erasing, or retouching it.
```

After accepting the source, store this shared lock and the final subject block
in the target repository's canonical prompt documentation.
