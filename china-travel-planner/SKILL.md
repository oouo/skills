---
name: china-travel-planner
description: >-
  Use when planning, auditing, or packaging a multi-day trip in China,
  especially a self-drive or family itinerary. Covers source-grounded
  research, route/time/meal feasibility, uncertainty handling, and
  WeChat-ready image cards with optional HTML or PDF roadbooks.
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

Default a new planning request with no channel to the WeChat sharing pack.

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

### 5. Render the Requested Channel

Read [`references/output-contract.md`](references/output-contract.md), then
render only the channels the user needs.

For a WeChat sharing pack:

```text
python3 scripts/render_wechat.py <trip.json> --out <output-directory>
```

This produces a short `summary.txt`, numbered 1080x1440 PNG cards, and a
`manifest.json`. If Pillow is missing, report the missing dependency and ask
before installing anything.

For an optional HTML roadbook:

```text
python3 scripts/render_roadbook.py <trip.json> --output <roadbook.html>
```

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
  separate actions requiring explicit user authorization.
