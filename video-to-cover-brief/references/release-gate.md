# Douyin Cover Release Gate

Use this gate after image generation and before recommending an upload or a
published-cover edit. A live edit is a scarce release action, not a preview
tool. Keep exploration, comparison, and rejection local.

## Risk States

| State | Meaning | Required behavior |
| --- | --- | --- |
| `DRAFT` | Brief or visual layer is incomplete. | Continue locally. |
| `HOLD` | A candidate exists but any gate is unverified or failed. | Do not recommend upload or edit. |
| `LOCAL_READY` | Full-size, single-cell, and grid checks pass. | Present no more than two finalists to the user. |
| `READY_TO_PUBLISH` | The user explicitly approves one exact local candidate. | Recommend only that file; any later change returns to `HOLD`. |

For a published work, record the user's reported edits used and remaining edit
budget. If unknown, treat the budget as scarce. Never infer that an edit is
safe merely because the platform still exposes the edit button.

## Required Artifacts

1. The final 1080×1440 cover.
2. A 196×261 single-cell preview, or a cell measured from the user's newer
   real profile screenshot.
3. A three-column grid preview in intended newest-to-oldest order.
4. Existing neighboring covers in the grid when the user supplies them.
5. A short pass/fail report naming the exact candidate file.

Use `scripts/build-douyin-grid-preview.sh` for the baseline cell and grid when
ImageMagick is available. Set `SINGLE_CELL_OUTPUT` to retain the first cover's
exact-size cell, and pass files in the exact order they should appear. The script
includes a bottom-left play-count placeholder by default; set
`SHOW_PLAY_OVERLAY=0` only when a separate app-shell mock already supplies it.

## Gates

### 1. Text Integrity

- The visual layer contains no accidental text.
- The final visible text is only the fixed top bar and main title.
- Every Simplified Chinese character is exact at full size.
- The subtitle remains editorial-only and is not rendered.

### 2. Fixed Typography

- The top bar uses the fixed 52 px source type in both cells.
- Short and long context labels keep the same font size, weight, and glyph
  width; neither auto-fit nor horizontal compression is allowed.
- The main title uses the fixed 116 px source type.
- Its font file/family stays fixed within each semantic preset.
- When text overflows, rewrite or rebalance the line break. Do not shrink it.

### 3. Actual-Size Readability

View the 196×261 cell at 100% with no zoom:

- category and context can be read rather than merely recognized as a pill
- the main title can be read in one glance
- no thin subtitle, ornamental text, or micro-badge turns into visual noise
- title and top bar remain subordinate to the protected face, dog, or main
  action
- the bottom-left play-count overlay does not cover a face, paw, hand, or small
  evidence-bearing subject

### 4. Three-Column Profile Fit

- the new cover does not expose font-size drift against neighboring covers
- the series spine is stable in position, width, height, and apparent type size
- adjacent covers do not merge into an undifferentiated color block
- the subject remains identifiable in every cell
- a legacy or outlier cover is called out instead of silently treating the grid
  as consistent

### 5. Evidence and Identity

- the person, dog, landmark, and event still match the source evidence
- generative enhancement does not replace a recognizable subject with a generic
  substitute
- the cover promises the same kind of moment the video actually delivers

### 6. Human Release Approval

Show the exact final candidate and its actual-size grid preview together. Ask
for approval once. Do not describe an unreviewed candidate as publishable. If
the user requests any visual or copy change, return the status to `HOLD`, make
the change locally, and rebuild both previews.

## Report Template

```markdown
Release status: <HOLD, LOCAL_READY, or READY_TO_PUBLISH>
Candidate: <exact path>
Publication state: <unpublished or published>
Edits used / remaining: <user-reported values or unknown>
Single-cell preview: <path>
Grid preview: <path>
Text integrity: <pass/fail + reason>
Fixed typography: <pass/fail + reason>
Actual-size readability: <pass/fail + reason>
Profile fit: <pass/fail + reason>
Evidence and identity: <pass/fail + reason>
User approval: <pending or confirmed>
```
