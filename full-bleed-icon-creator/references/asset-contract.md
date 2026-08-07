# Full-Bleed Asset Contract

Read this contract before designing, generating, or accepting a full-bleed
module icon.

## Delivery Contract

| Property | Required value |
| --- | --- |
| Raster canvas | 800x800 PNG |
| Raster color | Fully opaque sRGB |
| Vector canvas | 800x800 viewBox |
| Vector content | Editable primitives only |
| Source retention | Accepted original model output |
| Naming | Lowercase kebab-case |

Keep the retained source, PNG, and SVG as one subject and one semantic sequence.
The host application applies the final corner radius.

## Full-Bleed Geometry

Measure the subject with a corner-seeded background flood-fill mask:

| Measurement | Acceptance range |
| --- | --- |
| Subject width | 740-780px |
| Subject height | 740-780px |
| Left/right/top/bottom clearance | 4-32px each |
| Centroid distance from `(399.5,399.5)` | At most 32px |
| Subject pixels clipped by 160px round-rectangle proxy | 0 |

Use these numbers only to accept or reject a composition. Let the character's
own organic silhouette provide most of the reach. Keep rounded-corner regions
clear and place functional symbols inside or tightly overlapping the body.

## Visual Family

- Use a polished kawaii editorial vector-sticker character.
- Shape contours with a slightly organic, hand-formed feel.
- Ink the subject with confident thick near-black outlines.
- Layer paper-cut forms with compact depth shading and restrained highlights.
- Keep tactile speckle inside colored subject shapes.
- Use one high-contrast, asset-specific background color edge to edge.
- Keep the background near-uniform with only subtle paper grain.
- Use high-saturation cyan, lime, yellow, pink, orange, blue, or purple accents.
- Preserve a strong silhouette and friendly expression at 32px.

The result should feel authored and tactile, not glossy 3D or mechanically flat.

## Semantic Composition

- Build one main anthropomorphic character.
- Limit supporting symbols to a small physically connected set.
- Encode actions and outcomes through internal layering and overlap.
- Prefer universal symbols over words or copied logos.
- Use compact shadows that land directly on the full-bleed background.
- Keep the background subordinate to the subject.

The accepted silhouette is one coherent cluster. A narrow character expanded by
detached extremities is still a narrow composition and must be regenerated.

## Provenance Gates

1. Generate a new raster from the final prompt.
2. Retain the accepted model output unchanged as source evidence.
3. Normalize the entire source to 800x800 exactly once.
4. Accept the PNG before authoring the SVG.
5. Build the SVG with editable primitives rather than raster embedding.
6. Compare both media visually and through the validator.

The flood-fill mask, rounded proxy, and rendered SVG preview are temporary QA
artifacts. Keep them outside the repository and discard them after inspection.

## Failure Routing

| Failure | Correct next action |
| --- | --- |
| Raster subject is narrow, cross-shaped, or semantically unclear | Rewrite the brief and regenerate the full raster |
| A corner is transparent or contains a baked radius | Regenerate with the full-bleed lock |
| Mask size, clearance, centroid, or proxy clipping fails | Regenerate the full raster |
| Source-to-PNG changed pixels is nonzero | Repeat only the direct normalization |
| SVG contains raster data or invalid XML | Re-author the SVG |
| SVG tells a different story or has different visual weight | Refine the SVG against the accepted PNG |
| PNG color count is below 30000 | Reinspect provenance and regenerate |
| Normalized RMSE is below 0.15 | Reinspect provenance/style and regenerate |

Only an explicit user-approved flat-vector exception may waive the final two
alarms. It does not waive opacity, source retention, geometry, or pure-vector
requirements.
