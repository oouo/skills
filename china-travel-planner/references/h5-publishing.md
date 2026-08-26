# H5 Publishing Handoff

Generate a validated, share-safe static H5 and hand it to the user for manual
publishing. Keep rendering and hosting separate so platform failures never
change `trip.json` and the skill never operates a hosting account by default.

## Contents

1. [Build the Artifact](#build-the-artifact)
2. [Write the Manual Handoff](#write-the-manual-handoff)
3. [Select a Hosting Method](#select-a-hosting-method)
4. [Reuse One Publishing Channel](#reuse-one-publishing-channel)
5. [Update and Roll Back](#update-and-roll-back)
6. [Privacy and Link Hygiene](#privacy-and-link-hygiene)

## Build the Artifact

Prefer the combined bundle:

```text
python3 scripts/validate_trip.py <trip.json>
python3 scripts/render_review_bundle.py <trip.json> \
  --out <output-repository>/YYYY-MM-<place-pinyin>
```

For an explicit H5-only request, write `index.html` at the root of an `h5/`
directory. Still create a separate operator handoff beside that directory.

Verify the page locally before delivery:

- open `index.html` through a local HTTP server;
- test 360-, 390-, and 430-pixel viewports without horizontal overflow;
- follow every day link and the overview, food/stay, checklist, and evidence links;
- confirm that navigation targets are at least 44 CSS pixels tall;
- confirm that the evidence ledger is present and collapsed by default;
- confirm that the page contains one non-executable `trip-data` script only;
- confirm that `noindex,nofollow,noarchive` metadata is present.

## Write the Manual Handoff

Keep the publishing guide outside `h5/`; never expose operational instructions
to people reviewing the public page. The handoff must tell the user:

- no upload, login, DNS change, or hosting mutation was performed;
- publish only the generated `h5/` directory;
- keep `index.html` at the root of the uploaded folder or ZIP;
- reuse an existing site or project when appropriate;
- use a preview or staging environment first when the selected host provides one;
- verify the stable HTTPS address after the production release succeeds.

End the artifact delivery message with a direct reminder that the user must
publish the files themselves.

## Select a Hosting Method

Choose by capability, not by vendor name. The host must support prebuilt static
HTML and provide a stable HTTPS address. Prefer version history, preview
deployments, rollback, and custom-domain support when the user needs them.

Use one of these patterns:

| Method | Fit | Required capability |
| --- | --- | --- |
| Direct upload | Manual folder or ZIP publishing | Accept prebuilt files without a build step |
| Git publishing | Users already maintain a repository | Publish a selected branch or directory |
| Static object hosting | Users already operate storage and CDN | Serve `index.html` over HTTPS |

- Do not name, rank, or recommend a provider when the user only asks for the
  standard review bundle.
- Follow a provider named by the user instead of replacing it with a preferred
  host.
- When the user asks for provider options, present at most two suitable choices
  and explain the operational difference that matters to this artifact.
- Verify current platform documentation before giving provider-specific steps.
- Explain filing, region, domain, and availability constraints conditionally;
  never generalize one provider's rules to every host.

## Reuse One Publishing Channel

Treat the hosted site as a reusable sharing channel, not as one trip:

- recommend a neutral site identifier such as `travel-roadbook`;
- do not create a new site or project for every destination or itinerary;
- keep one stable sharing address when the selected host supports it;
- create a new deployment, release, or source update for each revision;
- describe production replacement and rollback using the selected platform's
  verified terminology rather than assuming universal environment names.

## Update and Roll Back

- Render every revision from the updated, validated `trip.json`.
- Use `generated_at` as the visible revision time; never invent a version label.
- Publish a preview first when the host supports previews.
- Publish the same `h5/` artifact to the live environment only after review.
- Retain the previous successful version until the stable-address release check
  passes when the host provides deployment history or rollback.

## Privacy and Link Hygiene

- Publish only the renderer's share-safe `h5/` artifact.
- Do not publish source `trip.json`, cards, tokens, or the operator handoff.
- Do not claim that `robots` metadata or an unguessable path is access control.
- Avoid short links, redirect chains, advertisements, analytics, and unrelated
  third-party scripts. They add failure and trust surfaces in WeChat.
- Never rent a third party's filed domain or use a so-called anti-blocking domain.
- Do not add WeChat OAuth, JS-SDK, payment, location, or user-profile access as
  part of this static-roadbook workflow.
