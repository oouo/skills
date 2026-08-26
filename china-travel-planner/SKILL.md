---
name: china-travel-planner
description: >-
  Use when planning, auditing, or packaging a multi-day trip in China,
  especially a self-drive or family itinerary. Covers source-grounded
  research, route/time/meal feasibility, uncertainty handling, and
  WeChat-ready image cards, group-review H5 roadbooks, and optional PDF archives.
---

# China Travel Planner

## Overview

Build a constraint-first roadbook: establish evidence coverage and internal
time feasibility before making the plan attractive. Keep `trip.json` as the
single source of truth, then render channel-specific outputs from it.

## When to Use

| Request | Execute |
| --- | --- |
| New plan or revision | Steps 1-4, requested Step 5 outputs, then Step 6 when refresh is due |
| Audit only | Steps 1-4, then return the findings |
| Existing `trip.json`, render only | Step 4, then Step 5 from unchanged input facts |
| Departure refresh | Refresh due facts in Step 2, then Steps 4 and 6 plus requested outputs |

Unless the user explicitly requests one channel, default a completed plan to the
combined WeChat review bundle: image cards for quick sharing plus a static H5 for
continuous full-plan review. Do not make the user choose between them. Keep H5
as the primary reading layer when the card series is long.

## Instructions

### 1. Frame the Travel Brief

- Extract the origin, destinations, exact dates or trip length, transport,
  traveler mix, budget, priorities, hard constraints, and requested channel.
- For a new plan, close this Minimum Intake Gate before research, route
  construction, or rendering:

  | Field | Acceptable input |
  | --- | --- |
  | Origin | A named place or transport hub |
  | Destination | A named place or region, or an explicit request to recommend one |
  | Schedule | Start and end dates, or a confirmed start date plus trip length |
  | Party | Adult count; child count and ages or `unknown`; senior count |
  | Transport | A chosen mode, or an explicit request to compare or recommend modes |
  | Overnight | For a multi-day trip: fixed stay, preferred area, or `recommend` |

- Ask for every missing gate field in one concise turn. Reuse supplied facts
  verbatim, do not ask for them again, and do not start Step 2, Step 3, or Step
  5 until each missing field is supplied or explicitly delegated.
- Treat `recommend`, `you decide`, and equivalent wording as delegation rather
  than missing input. Keep the resulting destination, transport, or stay as a
  visible candidate or open decision until the user accepts it.
- If a child age is unavailable, retain `unknown` and apply conservative child
  constraints instead of inventing an age. Ask about budget, priorities, and
  other preferences in the same turn only when they materially change routing
  or feasibility; otherwise declare a conservative assumption.
- Treat children, seniors, mobility needs, pets, dietary needs, night-driving
  limits, and fixed bookings as scheduling constraints rather than prose notes.
- Route an existing itinerary through the same evidence and feasibility gates.

Completion criterion: the Minimum Intake Gate is closed for a new plan, and
every remaining assumption is explicit and reversible.

### 2. Pass the Source Gate and Build the Evidence Ledger

- Read [`references/source-policy.md`](references/source-policy.md).
- Inventory available research capabilities before invoking them. Admit only
  capabilities that pass the Source Gate; tool availability is not permission.
- Research each material fact with the source class that owns it.
- Record every used source with its type, public URL or non-secret locator, and
  actual `access_method`, plus its check time. Link each factual aspect to those
  source IDs in the evidence ledger.
- Mark a fact `verified`, `candidate`, or `unknown`. Keep exact values out of
  `unknown` facts and never upgrade model memory into live evidence.

Completion criterion: every invoked capability passed the Source Gate, every
route-critical fact is sourced or visibly marked as a candidate or unknown,
and conflicting evidence is resolved or exposed.

### 3. Build `trip.json`

- Read [`references/trip-contract.md`](references/trip-contract.md).
- For self-drive or rental-car travel, also read
  [`references/roadtrip.md`](references/roadtrip.md).
- Read [`references/food-routing.md`](references/food-routing.md) when food is a
  stated priority, a restaurant is fixed, or dietary constraints affect routing.
- Express each day as ordered `travel`, `activity`, `meal`, `rest`, `buffer`,
  or `checkin` segments connected through structured places.
- Put meals and overnight check-ins on the timeline. Preserve fixed bookings
  with `plan_status: fixed`.
- Keep planning state on segments and evidence state in the evidence ledger.
- Group every open blocking verification task into a concise checklist action;
  keep low-level evidence tasks in the ledger instead of duplicating them in
  WeChat cards.

Completion criterion: every day's travel, visits, meals, rest, check-in, and
meaningful buffer are accounted for in one canonical `trip.json`.

### 4. Pass the Feasibility Gate

Run from the skill directory:

```text
python3 scripts/validate_trip.py <trip.json>
```

- Fix every `ERROR` and rerun until the validator exits successfully.
- Review every `WARNING`. Change the plan when it reveals a real risk; retain
  the warning only when the uncertainty is intentionally visible to the user.
- Resolve validation failures by correcting evidence, constraints, or the
  timeline while preserving the user's stated constraints and available facts.
- Interpret a clean result as structural, evidence-coverage, and internal-time
  feasibility only. Keep real-world safety and availability in the departure
  checks.

Completion criterion: validation reports zero errors, and every warning has an
explicit planning or disclosure response.

### 5. Render the Review Bundle

Read [`references/output-contract.md`](references/output-contract.md), then
render both default channels unless the user explicitly limits the output.

For the default image-card plus H5 bundle:

```text
python3 scripts/render_review_bundle.py <trip.json> \
  --out <output-repository>/YYYY-MM-<place-pinyin>
```

Name each trip directory `YYYY-MM-<place-pinyin>`, using the start month from
`brief.start_date` and the full lowercase, toneless pinyin of the primary
destination or named route. Use hyphens between multiple destination names;
never use initials, Chinese characters, or an English translation. For example,
a trip starting in August 2026 on the Wannan Sichuan-Tibet route uses
`2026-08-wannan-chuanzangxian/`.

This produces `wechat/`, `h5/index.html`, and an operator-only `UPLOAD.md`
inside that trip directory. Deliver the local paths and explicitly remind the
user to upload the `h5/` directory themselves. Never place upload instructions
inside the public H5 page and never initiate a cloud upload as part of ordinary
rendering. Keep the artifact and default handoff provider-neutral: describe
required hosting capabilities and publishing patterns without naming or
preferring a provider. Add provider-specific guidance only when the user selects
a provider or asks for a comparison, and verify its current documentation before
answering.

For a WeChat sharing pack:

```text
python3 scripts/render_wechat.py <trip.json> --out <output-directory>
```

This produces a short `summary.txt`, numbered 1080x1440 PNG cards, and a
`manifest.json`. If Pillow is missing, report the missing dependency and ask
before installing anything.

For an explicitly requested H5-only roadbook:

```text
python3 scripts/render_roadbook.py <trip.json> --output <h5-directory>/index.html
```

Use the self-contained H5 roadbook for full-plan review in a WeChat group. It
keeps every day visible in one page, puts open decisions first, and collapses
the evidence ledger without removing it. Generate a separate upload handoff from
[`references/h5-publishing.md`](references/h5-publishing.md); do not publish it.

Generate PDF only when requested. Derive it from the validated HTML, then
render and inspect every page with the available PDF or browser workflow.

Completion criterion: every artifact is derived from the same validated JSON,
contains no contradictory exact values, and passes every applicable check in
the output contract's QA section.

### 6. Run the Departure Gate

- Recheck time-sensitive facts when the trip is near, using the refresh windows
  in the source policy.
- Put unresolved decisions near the top of the WeChat summary and overview card.
- Keep departure-day checks for weather, traffic controls, opening status,
  reservations, and transport availability in the checklist.
- Render candidates explicitly as unbooked, unconfirmed, and not safety-verified.
- Write real-trip artifacts to the user's requested working directory, never
  into this skill directory.

Completion criterion: every fact due for refresh has current evidence or an
open task, and the user can distinguish confirmed plans, open decisions, and
departure-day checks without reading the source ledger.

## Failure Boundaries

- When a renderer fails, preserve the validated JSON and retry only the output
  stage.
- Treat booking, payment, messaging, publishing, and external uploads as
  separate actions. The default workflow stops at local artifacts and a manual
  upload reminder.
