# Trip JSON Contract

`trip.json` is the single source of truth for validation and every renderer.
Keep planning state, evidence state, and presentation separate.

## Contents

1. [Root Object](#root-object)
2. [Constraints](#constraints)
3. [Sources and Evidence](#sources-and-evidence)
4. [Places](#places)
5. [Days and Segments](#days-and-segments)
6. [Decisions, Risks, and Tasks](#decisions-risks-and-tasks)
7. [Status Rules](#status-rules)

## Root Object

Use this shape. Optional descriptive fields may be omitted, but do not rename
required fields because the bundled scripts consume them directly.

```json
{
  "schema_version": "1.0",
  "title": "皖南川藏线两日自驾",
  "subtitle": "四大一小 · 美食优先",
  "status": "draft",
  "timezone": "Asia/Shanghai",
  "generated_at": "2026-08-09T10:00:00+08:00",
  "last_verified_at": "2026-08-09T09:30:00+08:00",
  "fixture": false,
  "brief": {
    "origin_place_id": "trip-origin",
    "destination_place_ids": ["ningguo", "jingxian"],
    "start_date": "2026-08-15",
    "end_date": "2026-08-16",
    "transport": "self-drive",
    "party": {
      "adults": 4,
      "children": [{"age_years": 8}],
      "seniors": 0
    },
    "priorities": ["food", "scenery"],
    "notes": []
  },
  "constraints": {},
  "overview": {
    "summary": "A conservative two-day loop with meals on the route.",
    "decisions": [],
    "risks": []
  },
  "sources": [],
  "evidence": [],
  "places": [],
  "days": [],
  "verification_tasks": [],
  "checklist": []
}
```

Required root fields are `schema_version`, `title`, `status`, `timezone`,
`generated_at`, `brief`, `constraints`, `overview`, `sources`, `evidence`,
`places`, `days`, `verification_tasks`, and `checklist`.

Normalize the confirmed travel brief before writing the root object:

- Derive `end_date` inclusively from a confirmed `start_date` and trip length.
  For example, a two-day trip starting on 2026-09-12 ends on 2026-09-13.
- Do not invent a date when the user supplied only a duration. Close the
  Minimum Intake Gate before researching live availability or validating JSON.
- Treat a request to recommend lodging as sufficient intake, but keep the
  specific stay as a candidate or open decision. The trip remains `draft`
  until that decision is accepted and any blocking stay facts are verified.

Allowed trip statuses are:

- `draft`: a material choice or blocking verification remains unresolved;
- `ready`: the current plan has no open decision or blocking verification task.

## Constraints

Make thresholds explicit so validation never hides a planning assumption:

```json
{
  "max_unscheduled_gap_minutes": 30,
  "driving": {
    "max_continuous_minutes": 120,
    "min_break_minutes": 20,
    "max_daily_minutes": 360,
    "hard_max_daily_minutes": 480,
    "latest_end": "18:30"
  },
  "child": {
    "max_continuous_vehicle_minutes": 120,
    "latest_day_end": "20:30"
  },
  "meal_windows": {
    "lunch": {"start": "11:30", "end": "14:00", "required": true},
    "dinner": {"start": "17:30", "end": "20:30", "required": true}
  }
}
```

Require `child` when the party contains children. Tighten thresholds for known
needs. Do not silently relax an explicit limit to make a route pass.

## Sources and Evidence

Record a source once:

```json
{
  "id": "map-route-d1-1",
  "type": "map",
  "title": "Driving route result",
  "access_method": "official_api",
  "url": "https://...",
  "accessed_at": "2026-08-09T09:30:00+08:00"
}
```

Use `locator` instead of `url` for a tool result with no public link:

```json
{
  "id": "map-route-d1-2",
  "type": "map",
  "title": "Map tool route query",
  "access_method": "official_connector",
  "locator": "route-query:ningguo-to-fangtang:2026-08-09T09:35+08:00",
  "accessed_at": "2026-08-09T09:35:00+08:00"
}
```

Allowed source types are `official`, `map`, `transport`, `first_party`,
`weather`, `ugc`, `local_media`, `user`, and `other`. Except for `user`, every
source needs a public `url` or a non-secret `locator`.

Every source also requires the actual `access_method` admitted by the Source
Gate loaded in Step 2. `public_web` requires a public HTTP(S) `url`; a locator
is not a substitute. `fixture` is valid only when the root object has
`fixture: true`.

Attach evidence to one target and one aspect:

```json
{
  "id": "ev-d1-drive-duration",
  "target_id": "d1-drive-1",
  "aspect": "duration",
  "status": "verified",
  "source_ids": ["map-route-d1-1"]
}
```

Allowed aspects are `identity`, `location`, `route`, `duration`, `distance`,
`hours`, `price`, `reservation`, `parking`, `queue`, `policy`, `weather`, and
`experience`.

- `verified` and `candidate` evidence must cite at least one source.
- `unknown` evidence must contain a useful `note` and reference an open
  verification task.
- Keep one record per `target_id + aspect`; put corroborating sources in the
  same record.

## Places

Normalize route nodes so continuity can be checked:

```json
{
  "id": "ningguo-lunch",
  "name": "宁国午餐候选",
  "kind": "restaurant",
  "address": "宁国城区",
  "coordinates": {"lat": 30.63, "lon": 118.98},
  "details": {
    "must_order": ["宁国地方菜"],
    "price_note": "点单时确认",
    "parking_note": "停车条件待复核",
    "child_fit": "确认可做不辣菜",
    "backup_for": null
  }
}
```

Allowed place kinds are `origin`, `destination`, `attraction`, `restaurant`,
`stay`, `service`, `transport_hub`, and `other`. Coordinates, when present, use
WGS-84 latitude and longitude.

Every used place needs `identity` and `location` evidence. A user-provided home,
booking, or meeting point can use a `user` source without exposing private
details in rendered outputs.

## Days and Segments

Use RFC 3339 timestamps with an explicit UTC offset. Put every meaningful block
on one ordered timeline.

```json
{
  "day": 1,
  "date": "2026-08-15",
  "title": "青龙湾与山路前段",
  "start_place_id": "trip-origin",
  "end_place_id": "fangtang-stay",
  "segments": [
    {
      "id": "d1-drive-1",
      "type": "travel",
      "mode": "drive",
      "plan_status": "planned",
      "title": "出发地至途中休息点",
      "start_at": "2026-08-15T06:30:00+08:00",
      "end_at": "2026-08-15T08:30:00+08:00",
      "from_place_id": "trip-origin",
      "to_place_id": "xuancheng-break",
      "distance_km": 126,
      "route_duration_minutes": 120,
      "daylight_required": false,
      "notes": []
    },
    {
      "id": "d1-break",
      "type": "rest",
      "plan_status": "planned",
      "title": "司机与儿童休息",
      "start_at": "2026-08-15T08:30:00+08:00",
      "end_at": "2026-08-15T09:00:00+08:00",
      "place_id": "xuancheng-break",
      "notes": []
    },
    {
      "id": "d1-lunch",
      "type": "meal",
      "meal_kind": "lunch",
      "plan_status": "candidate",
      "title": "宁国午餐",
      "start_at": "2026-08-15T11:30:00+08:00",
      "end_at": "2026-08-15T12:30:00+08:00",
      "place_id": "ningguo-lunch",
      "notes": []
    }
  ]
}
```

The example above is a shape excerpt, not a complete valid day.

Allowed segment types are `travel`, `activity`, `meal`, `rest`, `buffer`, and
`checkin`. Allowed plan statuses are `fixed`, `planned`, and `candidate`.

- `travel` requires `mode`, `from_place_id`, and `to_place_id`.
- Other segment types require `place_id`.
- `meal` also requires `meal_kind`: `breakfast`, `lunch`, `dinner`, or `snack`.
- `distance_km` requires distance evidence; `route_duration_minutes` requires
  duration evidence. Omit an exact value when the evidence is unknown.
- A place change must occur through a travel segment.
- A fixed booking or connection uses `plan_status: fixed`.
- A day ending at a `stay` place includes a `checkin` segment at that place.
- Represent free time as a `buffer` at the current place.

## Decisions, Risks, and Tasks

Use decisions for group choices:

```json
{
  "id": "decision-stay",
  "question": "第一晚住哪里？",
  "options": ["宁国", "方塘"],
  "status": "open",
  "selected": null
}
```

A resolved decision must record `selected`. A ready trip cannot contain an open
decision.

Use risks as evidence targets:

```json
{
  "id": "risk-traffic-control",
  "title": "可能有临时交通管制",
  "level": "high",
  "critical": true,
  "mitigation": "出发前 48 小时复核官方公告"
}
```

Use verification tasks to close evidence gaps:

```json
{
  "id": "verify-traffic-control",
  "evidence_id": "ev-traffic-control",
  "action": "复核交管部门公告",
  "due": "T-48h",
  "blocking": true,
  "status": "open"
}
```

Use checklist items for group-ready actions:

```json
{
  "group": "t-48h",
  "item": "复核天气和临时交管",
  "status": "open",
  "task_ids": ["verify-traffic-control"]
}
```

Allowed checklist groups are `now`, `t-48h`, and `pack`. Allowed task and
checklist statuses are `open`, `done`, and `not_needed`.

Treat `checklist` as the group-ready action layer. Link every open blocking
verification task from exactly one concise checklist item through `task_ids`.
Group related route legs, venue checks, or weather checks into one action;
leave non-blocking detail in `verification_tasks` for the ledger and HTML.

## Status Rules

- Keep `plan_status` on timeline choices and evidence status in `evidence`.
- Use the presentation labels defined in
  [`output-contract.md`](output-contract.md) when rendering evidence status.
- Keep a trip in `draft` while a blocking verification task or group decision
  remains open.
- Preserve fixed segments during audits unless the user explicitly changes the
  booking or connection.
