# Food Routing

Treat food as a spatial and temporal route decision, not a generic appendix.

## Separate Dish Truth from Restaurant Choice

- Use authoritative local sources to establish representative dishes, products,
  and food traditions.
- Use admitted experience evidence and map POI data to discover route-fit
  candidates.
- Use a first-party menu, booking page, phone confirmation, or recent venue
  notice for exact hours, prices, reservations, and operating status.

Form a recommendation only when dish relevance and restaurant route fit each
have their own evidence.

## Route-Fit Test

Evaluate every scheduled meal against:

- arrival time and operating window;
- detour from the current route;
- parking or transit access;
- expected queue and reservation need;
- group size and seating;
- child, senior, allergy, spice, and dietary fit;
- the next driving leg and whether the meal causes night driving;
- a nearby backup with different failure risks.

Put the selected restaurant in `places` and schedule a `meal` segment at that
`place_id`. Keep dish, parking, price, fit, and backup notes in `place.details`.
Record identity, location, hours, price, parking, queue, and experience as
separate evidence aspects whenever they appear in the plan.

## Meal Timing

- Schedule lunch when the active window crosses midday and dinner when it
  extends into evening.
- Add queue, parking, ordering, and payment time when they are material.
- Prefer a less famous route-compatible restaurant over a popular choice that
  breaks the day.
- Place the only acceptable child-friendly meal before a fragile attraction or
  mountain leg, or add a nearby backup.

## Backup Rules

- Track restaurant identity, location, and hours as independent evidence
  aspects; one confirmed aspect does not upgrade the whole venue.
- Provide a backup in the same area when queues, reservation, weather, or
  operating status could break the meal.

## Food Completion Gate

Before rendering, confirm that:

- every meal required by the travel window appears on the timeline;
- every meal references an existing restaurant place;
- local dishes and specific restaurants have separate evidence;
- each scheduled restaurant fits the route and traveler constraints;
- fragile meals have a route-compatible backup or an explicit open decision.
