# Douyin Cover Release Gate

Run this gate after each review batch and again on the canonical package. A live
edit is a release action, not a preview tool.

## States

| State | Meaning | Required behavior |
| --- | --- | --- |
| `DRAFT` | Brief, clean plate, or assembly is incomplete. | Continue locally. |
| `HOLD` | Any automated or human gate is unverified or failed. | Do not publish. |
| `LOCAL_READY` | One candidate passes local mechanical and visual review. | Present it for approval. |
| `FINAL` | The user approves the exact package and the package hashes pass. | Treat it as the only current local release. |
| `READY_TO_PUBLISH` | The user separately authorizes the exact online action. | Publish only that exact file. |

Any change to a `LOCAL_READY`, `FINAL`, or `READY_TO_PUBLISH` file returns the
new artifact to `HOLD` until the full gate is rerun.

## Required package artifacts

1. Numbered final PNGs in one canonical directory.
2. `meta/SOURCES.tsv` mapping sequence, filename, video ID, source file, and
   version note.
3. `meta/SHA256SUMS` for every final cover.
4. `meta/TOPBAR-TEXT.txt` with one final label per cover.
5. `meta/MAIN-TITLES.tsv` with one final title mode per cover and no
   `artwork-candidate` rows.
6. A full-series montage and top-bar montage.
7. Main-title, subject-middle, and bottom/edge QA montages.
8. Exact-cell and three-column profile previews in intended order.
9. SHA-256 manifests for QA and profile previews.
10. A package-local review record naming the exact package and status.
11. For reference-guided hand-brushed titles, the approved canonical RGBA title
    layer, its SHA-256, style contract ID, style-reference provenance, and exact
    user approval.

## Mechanical gates

### File contract

- expected continuous numbered cover set and no extra root-level PNG
- `meta/SHA256SUMS` names that exact cover set once each, not merely the same
  number of arbitrary files
- exact canonical dimensions and sRGB color space
- no unexpected alpha channel in flattened finals
- virtual canvas normalized to the image dimensions
- image decode succeeds without corruption warnings

### Typography

- pinned font file exists and matches its recorded SHA-256
- HarfBuzz shapes every top-bar string without `.notdef` or `gid0`
- top edge, card height, component height, text color, card color, and visible
  glyph height match the series contract
- context length changes card width, not font size
- the image model has not generated the final visible top-bar Chinese
- each main title is either immutable `locked-artwork` or fixed-size
  `deterministic-font`; no unresolved title direction reaches release
- `artwork-candidate` is never release-eligible; reference-guided lettering must
  have an exact canonical layer path and SHA-256 plus explicit user approval
- scene-adaptive artwork records exact approved colors and passes full-size and
  exact-profile-cell contrast review

### Provenance

- each packaged file equals its source file by SHA-256
- every `SOURCES.tsv` filename maps exactly once to the packaged cover set
- each video ID has one original video, one evidence contact sheet, one brief,
  and one source record
- each reference-guided title records the style-reference path and SHA-256 while
  keeping the reference's embedded text and scene out of the new cover's factual
  evidence
- a bundled default records `default-hand-brushed-title-v1`; its provenance and
  generation-reference hashes match the skill contract rather than an ad hoc
  user re-upload
- final sequence and profile sequence are explicit, not inferred from lexical
  filename sorting

### Pixel protection

- every repair has an explicit authorized mask or lock boundary
- maximum pixel difference outside the authorized region is zero
- source-derived title or subject regions equal the intact authoritative source
- approved hand-brushed title pixels and alpha equal the canonical locked title
  layer; no post-approval redraw, recolor, or scaling is present
- clean background replacement contains no card residue or seam outside the new
  card
- every previously reported defect has a regression check that fails on the
  known-bad version and passes on the candidate

Use ImageMagick `Difference` or equivalent direct pixel comparison. Compare
authentic same-size pixels; perceptual similarity is not sufficient for locked
material.

## Human gates

Inspect all of the following; no single montage replaces another:

- full-cover overview
- enlarged top bars and their lower seams
- main titles, including all stroke caps and descenders
- every hand-brushed Chinese character, character order, line break, and absence
  of extra or pseudo-text against the exact approved candidate
- subject middle sections for redrawing, deformation, or wrong identities
- bottom and outer edges for crops, patches, and residue
- exact profile cells and the real/app-shell three-column layout
- each cover beside its video contact sheet

Pay special attention to defects automation commonly misses: clipped title
strokes, similarly colored rectangular bands, isolated alpha residue, subtle
subject redraws, and composition changes that are harmless at full size but
obvious in the profile grid.

## Repair decision

| Failure | Response |
| --- | --- |
| Top-bar geometry/font drift | Re-render deterministically from the contract. |
| Old card corner or lower seam | Rebuild from a clean top plate; do not cover the old card. |
| Main-title stroke clipped | Recover the exact pixels from an intact source with a minimal mask. |
| Hand-brushed candidate unapproved or misspelled | Keep `HOLD`; reject or regenerate an isolated candidate and request exact user approval. |
| Background changes outside title | Replace a color mask with a source-difference/geometric mask. |
| Recognizable subject changed | Reject; restart from the video-frame material and lock the subject. |
| Profile grid exposes imbalance | Recompose the clean visual; do not silently alter shared typography. |

## Final report template

```markdown
Release status: <HOLD, LOCAL_READY, FINAL, or READY_TO_PUBLISH>
Canonical package: <exact path>
Cover count: <actual/expected>
Cover SHA-256: <pass/fail>
QA SHA-256: <pass/fail>
Source/video mapping: <pass/fail>
Typography contract: <pass/fail>
Hand-brushed title approval and locked-layer hash: <pass/fail/not applicable>
Locked-pixel checks: <pass/fail>
Regression checks: <pass/fail>
Human full/top/title/subject/edge/profile review: <pass/fail>
Package contains no extra root-level PNG: <pass/fail>
User approval: <pending or exact approval>
Online publication authorization: <absent or exact authorization>
```
