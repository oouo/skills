# Output Contract

Render all channels from the same validated `trip.json`. Never research or
silently change facts inside a renderer.

## Contents

1. [Default Review Bundle](#default-review-bundle)
2. [WeChat Sharing Pack](#wechat-sharing-pack)
3. [Card System](#card-system)
4. [H5 Review Roadbook](#h5-review-roadbook)
5. [PDF](#pdf)
6. [Output QA](#output-qa)

## Default Review Bundle

Unless the user explicitly requests a single channel, produce:

```text
2026-08-wannan-chuanzangxian/
├── wechat/
│   ├── summary.txt
│   ├── manifest.json
│   └── cards/
├── h5/
│   └── index.html
└── UPLOAD.md
```

Name the trip directory `YYYY-MM-<place-pinyin>`:

- derive `YYYY-MM` from `brief.start_date`, not the generation or publication
  date;
- use the full lowercase, toneless pinyin of the primary destination or named
  route;
- join multiple public-facing destination names in route order with hyphens;
- do not use initials, Chinese characters, or English translations;
- use `2026-08-wannan-chuanzangxian`, not `2026-08-wnczx`, for an August 2026
  trip on the Wannan Sichuan-Tibet route.

Cards are the quick-scan and forwarding layer. H5 is the complete continuous
review layer. Keep `UPLOAD.md` outside `h5/` so operational instructions do not
become part of the public site. Tell the user to upload only `h5/` themselves.
Keep the default handoff valid for any static host and free of provider names.
Mention a provider only when the user selected one or explicitly requested a
comparison.

## WeChat Sharing Pack

Use this as the default when the user mentions a WeChat group, family group, or
easy forwarding.

Produce:

```text
wechat/
├── summary.txt
├── manifest.json
└── cards/
    ├── 01-overview.png
    ├── 02-day-1.png
    ├── 03-day-2.png
    ├── 04-food-and-stay.png
    └── 05-checklist.png
```

For one to three days, target four to six cards: overview, one card per day,
food and stay, then checklist. Longer trips become numbered WeChat series.
Keep the overview first and the checklist last. Split an overflowing day into
continuation cards instead of shrinking body text below the readable floor.

Render the curated `checklist` as the group-chat action layer. Do not append
every low-level `verification_task` after it; complete evidence work remains in
`trip.json` and HTML. Require each open blocking task to be represented through
`checklist[].task_ids` before rendering.

Write `summary.txt` as plain text, not Markdown. Keep it concise enough to paste
directly into a group chat. Include:

- title, dates, traveler mix, and transport;
- route in one line;
- up to three open decisions or verification tasks;
- a one-line description of the attached cards.

## Card System

Render cards as 1080x1440 PNG with a 3:4 portrait ratio.

Use a route-spine visual language:

- mist `#F3F7F5` for the canvas and white for information surfaces;
- ink `#18343C`, muted ink `#465B61`, and dividers `#CBDAD5`;
- route pine `#0F6B62` for sequence and verified status;
- meal yellow `#F6E7BD` and material-risk clay `#B64232`;
- a vertical route spine at x=114 with content beginning at x=168;
- a 72-pixel safe inset and restrained Chinese sans-serif typography.

Use 45-51-pixel primary timeline text, 39-pixel secondary text, and a 36-pixel
absolute floor on the 1080-pixel canvas. These become roughly 15-17, 13, and
12 pixels in a 360x480 phone preview. Use a regular-or-medium CJK face for body
copy and a distinct bold face for headings; never use a light face for phone
cards. When available, use a condensed sans-serif utility face for timeline
numerals only. Move optional detail to HTML or split a card before crossing the
floor.

Card responsibilities:

| Card | Required content |
| --- | --- |
| Overview | Dates, travelers, route, summary, high risks, open decisions |
| Day | Ordered timeline, movement, meals, stay, buffer, statuses |
| Food and stay | Route-fit options, dishes, parking, child fit, backups |
| Checklist | T-minus timing, reservations, weather, traffic, unresolved facts |

Map evidence status to visible symbols and Chinese text:

- `verified` -> `✓ 已核验`;
- `candidate` -> `○ 待确认`;
- `unknown` -> `? 待核实`;
- material risk -> `! 风险`.

The overview must make sense when viewed alone. Use text and symbols as well as
color. Keep the full trip title on the overview and summary; use a concise,
complete series label in repeated card headers. Keep formal names, times,
amounts, and warnings untruncated; split the card when they do not fit.

## H5 Review Roadbook

Use H5 as the primary WeChat review layer when the group must inspect the whole
plan at once or the image series would be unwieldy. Render it locally before
asking to publish. Keep it self-contained and responsive. Include:

- overview, decisions, risks, and source freshness;
- a mobile day spine and sticky in-page navigation;
- daily timelines;
- food and stay options;
- checklist and evidence ledger;
- a complete share-safe copy of the JSON in a non-executable
  `<script id="trip-data" type="application/json">` block.

Keep the itinerary expanded because it is the review subject. Collapse the
evidence ledger by default because it supports the plan rather than leading the
discussion. Add `noindex`, `nofollow`, and `noarchive` metadata, plus ordinary
Open Graph title and description metadata. Keep the itinerary readable and the
anchor links usable without JavaScript. Add only the small inline progressive
enhancement needed to mark the day currently visible below the sticky navigation
and horizontally reveal its day chip.

Optimize the page for WeChat's narrow in-app browser:

- use `viewport-fit=cover` and safe-area insets;
- keep body copy at 16 CSS pixels or larger with at least 1.7 mobile line height;
- keep navigation targets at least 44 CSS pixels tall;
- test at 360, 390, and 430 CSS pixels without horizontal overflow;
- use sticky horizontal day navigation with touch scrolling;
- avoid external fonts, hover-only behavior, animation, and required JavaScript.

Keep navigation or booking URLs as ordinary labeled links. Do not publish or
host the file. Put the manual handoff beside the bundle using
[`h5-publishing.md`](h5-publishing.md).

Omit personal names, phone numbers, identity numbers, booking codes, signed
URLs, home addresses, and private coordinates from every shareable layer,
including embedded JSON. Use a sanitized deep copy for rendering and leave the
input `trip.json` unchanged. Use a neutral origin label for a private home
location.

## PDF

Treat PDF as an optional archive or print channel. Derive it from the validated
HTML instead of maintaining a second layout source. Use the available PDF
workflow to render every page and inspect clipping, page breaks, fonts, links,
and status labels.

## Output QA

Before delivery, verify that:

- the validator reports zero errors;
- the trip directory matches `YYYY-MM-<place-pinyin>` and its month matches
  `brief.start_date`;
- the trip directory contains the requested `wechat/` and `h5/` channel
  directories, with each artifact in its corresponding channel;
- every PNG is exactly 1080x1440 and opens successfully;
- card numbering is continuous and matches `manifest.json`;
- no text crosses a card boundary or becomes unreadably small;
- muted text keeps at least 6.5:1 contrast against the canvas;
- status chips and adjacent detail text have a measured gap rather than a
  fixed guessed offset;
- the WeChat summary and overview expose the same open attention items;
- exact route, time, price, and operating claims match `trip.json`;
- candidate and unknown facts remain visibly labeled;
- HTML embeds the same schema version and trip title;
- H5 has no horizontal overflow at 360, 390, or 430 pixels;
- H5 has safe-area support, 16-pixel mobile body copy, and 44-pixel tap targets;
- every H5 day-navigation link targets an existing section;
- scrolling through a day updates and reveals the matching day-navigation chip;
- the evidence ledger is present and collapsed by default;
- upload instructions are outside `h5/` and are absent from `index.html`;
- fixture or evaluation data is visibly marked as non-production.

For visual QA, inspect the originals, 360x480 phone previews, and a contact
sheet. Treat sending a representative card to a test group as a manual action
that requires explicit authorization.
