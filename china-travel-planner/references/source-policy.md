# Source Policy

Use source ownership rather than one global source ranking. A source can be
excellent for lived experience and unsuitable for opening hours.

Keep content authority and acquisition method separate:

- `type` is the evidence class used to decide which facts the source can own.
- `access_method` records how the information was actually obtained.

Record both from the real provenance. The validator checks the declaration;
the research step remains responsible for classifying it truthfully.

## Source Gate

Inspect a capability before invoking it. A tool being installed or available
does not make its data collection method acceptable.

| Access method | Default decision | Boundary |
| --- | --- | --- |
| `official_api` | Allow | Documented API supplied by the data owner |
| `authorized_api` | Allow | Authorization is documented by the data owner or provider |
| `official_connector` | Allow | First-party documentation shows owner supply or endorsement |
| `public_web` | Allow | Stateless public page; HTTP client or browser transport does not matter |
| `user_provided` | Allow | Material the user deliberately supplied in this task |
| `fixture` | Tests only | Valid only when the root object has `fixture: true` |
| `unofficial_connector` | Reject | Community connector without platform authorization |
| `experimental_connector` | Reject | Connector explicitly described as experimental or unstable |
| `reverse_engineered_api` | Reject | Undocumented, private, or reverse-engineered endpoint |
| `browser_automation` | Reject | Stateful login, QR scan, Cookie session, or simulated account use |

Admit `authorized_api` and `official_connector` only when primary documentation
proves the relationship. Keep every rejected method outside this travel
workflow, including a community connector that requires a personal session or
shares a trust boundary with platform write actions. Route an explicit
connector experiment to separate setup work rather than travel evidence.

When no admissible experience source exists, continue with authoritative facts
and route-fit candidates. Mark the experience aspect `unknown`, add an open
verification task, and say that reliable review evidence is unavailable. Never
turn absence of evidence into claims such as "best rated", "most authentic", or
"real traveler consensus".

Classify forwarded material by its publisher, not its messenger:

| Input | `type` | `access_method` | Highest default status |
| --- | --- | --- | --- |
| User's own constraint or confirmed booking | `user` | `user_provided` | `verified` |
| User-forwarded platform post, review, link, or screenshot | `ugc` | `user_provided` | `candidate` |
| User-forwarded operator notice | `official` | `user_provided` | `candidate` until publicly verified |
| Public operator notice read normally | `official` | `public_web` | `verified` for owned facts |

## Fact Ownership

| Fact | Verification owner | Candidate discovery or corroboration |
| --- | --- | --- |
| Closures, traffic controls, entry rules | Government or operating authority | Current local media |
| Opening hours and reservations | Attraction or venue operator | Official booking channel |
| Routes, coordinates, distance, duration | Map or transport service | A second route provider |
| Train, flight, hotel, ticket price | First-party seller at query time | Major booking platform |
| Weather and warnings | Meteorological authority | Map weather service |
| Local dishes and food traditions | Local government, museum, association | Reputable local media |
| Restaurant parking | Operator, map, or first-party venue data | Recent UGC |
| Restaurant queues | First-party live information or direct user report | Recent UGC and local media |
| Restaurant experience | Direct user report or documented field report | Recent UGC |
| Family suitability and practical friction | Direct venue facts or user report | Recent UGC and local guides |

UGC discovers candidate experience signals; a `verified` claim requires an
admissible, non-UGC owner. Policy, safety, reservations, live price, and route
fit stay with their verification owners, and a map score alone proves none of
them.

## Evidence Status

- `verified`: a current source that owns the aspect supports the claim.
- `candidate`: at least one source supports the aspect, but confirmation is
  still needed or the source does not own the fact.
- `unknown`: evidence is absent, stale, conflicting, or inaccessible.

Attach evidence to a specific target and aspect. Both verified and candidate
evidence cite sources. Unknown evidence carries a note and a verification task;
never attach an exact price, duration, distance, opening time, or availability
claim to it.

## Default Refresh Windows

Treat these as maximum ages, not guarantees:

| Fact | Refresh no later than |
| --- | --- |
| Weather, warnings, temporary traffic controls | 24-48 hours before use |
| Same-day transport or road availability | On departure day |
| Opening hours, reservations, venue notices | 7 days before use |
| Live prices and inventory | At booking or purchase time |
| Restaurant operation and queue conditions | 7 days before use |
| UGC experience | Prefer the latest 6 months; use older posts as context only |

Refresh sooner during severe weather, public holidays, major events, mountain
travel, or when the authority announces temporary measures.

## Conflict Resolution

1. Prefer the source that owns the fact.
2. Prefer a newer update from the same authority.
3. Check whether the sources describe different dates, entrances, vehicle
   classes, ticket types, or operating periods.
4. Preserve the conflict as `unknown` when it cannot be resolved.
5. Turn unresolved route-critical conflicts into an open decision or checklist
   item rather than silently selecting one value.

## Research Completion Gate

Before planning, confirm that:

- every fixed booking is recorded as a constraint;
- every exact route leg has map or transport evidence;
- every critical venue has current operating evidence;
- every exact live price is first-party or explicitly labeled as a snapshot;
- every source passed the Source Gate and records its actual method;
- every experiential recommendation is separated from authoritative facts;
- every missing critical fact is visible as `unknown`.
