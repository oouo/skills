# Original Illustration Fallback

Use this branch only after a real source-frame direction has been prepared and
the user says it is unsatisfactory or explicitly asks to continue with a cartoon
or illustration revision. It is an alternative representation layer behind the
evidence model, not an automatic response to weak frames.

## Selection gate

Choose `original-illustration` only when all of these are true:

1. Beginning, middle, and end frames have been inspected.
2. One best available source-frame direction has been prepared and presented,
   with its strengths and limitations recorded.
3. The user reacts negatively to that direction or explicitly requests a cartoon
   or illustration revision. Record the exact statement. Explicit dissatisfaction
   with the overall source-frame direction authorizes one local cartoon candidate;
   a narrow note about title placement, top-bar color, or another repair does not.
4. Location, subject type, action, and any memory object are supported by video
   evidence or an explicit user statement.
5. The brief states `Truth Claim: original illustration; not a video frame`.

Do not activate this branch solely because frames are blurred, overexposed,
compressed, awkwardly cropped, or missing a clean title-safe zone. First show or
describe the best source-frame direction honestly. Silence is not dissatisfaction.

## Rights and reference boundary

- Never remove or disguise a third-party watermark.
- Do not use an uncertain or watermarked image as an edit target or attached
  generation reference. Extract only generic, non-exclusive ideas that the user
  explicitly values, then design a different scene from written constraints.
- For an uncertain third-party image, change camera height, perspective,
  foreground placement, subject direction, environment layout, lighting, and
  crop. The result must not function as a substitute copy of that image.
- Generic place names may appear on a non-branded memory object only when
  factually supported, user-requested, and allowlisted. Reject logos, brand trade
  dress, unsupported shop signs, and pseudo-Chinese.
- The approved cartoon revision authorizes stylizing evidence-backed subjects,
  actions, poses, and scenery from the inspected video frame. Do not invent
  facial identity, logos, product details, or private-object details that the
  evidence does not support. If exact identity or branding matters, keep those
  elements as source pixels or stay with `source-frame`.

## Evidence bundle

Record these fields before generation:

| Field | Requirement |
| --- | --- |
| Source-frame attempt | Candidate path or brief direction shown first |
| Source-frame review | Strengths, limitations, and user-visible status |
| Feedback trigger | Exact dissatisfaction or cartoon/illustration request |
| Trial approval | Exact overall dissatisfaction or cartoon request |
| Truth claim | `original illustration; not a video frame` |
| Factual anchors | Location, subject type, action, season/time if supported |
| Memory object | One concise foreground cue or `none` |
| Visible-text allowlist | Exact text; empty by default |
| Forbidden identity | People, brands, landmarks, props that must not be invented |
| Title-safe zone | Intended geometry for later deterministic/locked title |
| Prompt manifest | Exact expanded prompt, tool, output path, dimensions, SHA-256 |

## Reusable prompt template

Use the ImageGen `illustration-story` taxonomy. Keep the style block unchanged;
it is the approved cartoon rendering contract. Fill only evidence-backed
bracketed values and remove unused lines instead of leaving placeholders.

```text
Use case: illustration-story
Asset type: vertical short-video cover base, 3:4 portrait composition
Primary request: Create an original hand-painted illustration representing
[LOCATION OR DOCUMENTED SETTING]. This must be a newly designed scene, not a
tracing or close reconstruction of any uncertain third-party image. Use the
inspected video frame as the content reference for the subject and action.
Scene/backdrop: [EVIDENCE-BACKED ENVIRONMENT AND ARCHITECTURE].
Subject: [EVIDENCE-BACKED ACTION OR SUBJECT TYPE]. Include [MEMORY OBJECT] as a
clear but secondary foreground story cue.
Style/medium: refined Chinese travel-poster illustration, hand-painted gouache
and light ink-wash texture, cinematic rather than childish, crisp enough for a
modern social-media cover.
Composition/framing: 3:4 portrait; [MEMORY OBJECT] occupies about 18–22% of the
foreground, the main action remains readable near the visual center, and the
scene creates depth. Reserve a generous calm negative-space area at [TITLE-SAFE
ZONE] for a later two-line title.
Lighting/mood: [EVIDENCE-BACKED OR USER-APPROVED LIGHTING], controlled highlights,
balanced exposure, [MOOD].
Color palette: [SCENE-ADAPTIVE PALETTE].
Text (verbatim): [ALLOWLISTED MEMORY-OBJECT TEXT, OR “none”].
Constraints: original composition; no watermark; no logos; no other writing or
signage; no main title; no decorative border; no recognizable real people; any
allowlisted Simplified Chinese must be legible and correct.
Avoid: copying the camera angle, object placement, architecture, people, or
foreground geometry of any uncertain third-party reference; blown highlights;
clutter; extra memory objects; malformed Chinese text.
```

## Tested Jiangnan travel variant

For a Jiangnan canal story, use gray-tiled whitewashed houses, restrained red
lanterns, blue-green water, a clearly readable black-awning boat, warm wood, and
soft foliage. A generic red takeaway cup may carry an allowlisted two-character
place name as the foreground memory object. Put the cup and boat on different
depth planes, keep the boat action clear, and reserve an uncluttered upper zone
for the separately approved hand-brushed title.

This variant captures the successful logic of the Anchang test without making
Anchang, a coffee cup, or travel content mandatory for other videos.

## Review and promotion

1. Confirm that the source-frame direction and feedback trigger are recorded.
2. Generate the clean illustration base before any main-title candidate.
3. Check dimensions, exposure, factual anchors, fixed-style adherence,
   source-frame content continuity, composition difference from any uncertain
   third-party reference, allowlisted text, absence of extra
   text/logos/watermarks, and profile-cell legibility.
4. Save the exact prompt and SHA-256 beside the generated plate.
5. Present the base to the user at `HOLD`.
6. After exact approval, treat that plate as the authoritative visual source for
   deterministic assembly. Do not call it a frame or documentary photo.
7. Keep main-title creation on the existing `artwork-candidate` or
   `deterministic-font` path; never bake an unapproved main title into the plate.
