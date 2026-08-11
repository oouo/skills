# Self-Drive Planning

Read this reference for private-car and rental-car itineraries.

## Route Model

Treat driving as an activity with fatigue, daylight, parking, and recovery
costs. Record each meaningful leg separately instead of using one daily mileage
number.

For each leg, research or expose:

- origin and destination;
- route distance and normal duration from a map source;
- road class, tolls, and known vehicle restrictions when material;
- parking or safe stopping point at the destination;
- charging or fuel needs when range is material;
- weather, temporary controls, mountain roads, ferries, or seasonal closures;
- whether the leg should occur in daylight.

## Feasibility Defaults

Use these as conservative planning warnings, not universal laws:

| Condition | Default response |
| --- | --- |
| One continuous drive block exceeds 120 minutes | Add a real break, especially with children |
| Daily driving exceeds 6 hours | Warn and simplify the activity plan |
| Daily driving exceeds 8 hours | Treat as infeasible unless it is an explicit transfer day |
| Mountain or unfamiliar scenic road ends after dark | Move the leg earlier or expose the risk |
| Parking is unknown at a fixed-time stop | Add parking verification and arrival buffer |
| Meal requires a substantial detour | Compare it against a route-compatible backup |

Tighten these defaults for new drivers, children, seniors, pets, severe weather,
high altitude, towing, or large vehicles.

Write the chosen thresholds into `constraints.driving` and, when children are
present, `constraints.child`. The validator must read those values instead of
embedding a hidden universal limit.

## Family Breaks

- Break a long drive into independently sourced legs.
- Schedule toilet, hydration, and movement stops rather than hiding them in a
  generic duration estimate.
- Put a meal in the timeline when the travel window crosses lunch or dinner.
- Avoid making the child or senior constraint depend on an optional attraction
  running exactly on time.

## Scenic Roads

- Count the road itself as an attraction when driving is the experience.
- Use a slower map route or a clearly labeled planning allowance; do not apply
  city-road average speed to a scenic mountain road.
- Keep photo stops and overlooks separate from driving time.
- Identify the last safe turn-around, fuel, charging, toilet, and overnight
  points when the route is remote.
- Recheck temporary controls, weather, and road availability at T-48h and on
  departure day.

## Rental Cars and Mixed Transport

- Record pickup and return windows, license and deposit requirements, charging
  or fuel policy, and luggage capacity as fixed constraints.
- Add realistic airport or station handoff time.
- Do not count a train or flight arrival time as the start of driving; include
  baggage, pickup, inspection, and loading.

## Roadtrip Completion Gate

Before marking the trip ready, confirm that:

- every exact drive leg has current map evidence;
- every place transition is connected by a travel segment;
- daily drive time and continuous blocks pass explicit trip constraints;
- mountain or restricted legs have daylight and vehicle checks;
- every activity has an arrival, parking, and departure path;
- fuel, charging, toilets, meals, and breaks are placed where needed;
- the final return, rental return, or last train connection has a buffer.
