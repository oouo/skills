# Runtime Mechanisms

Read this file only when indirection or runtime boundaries hide a transition in
the selected execution spine.

## Confirm the Edge

A declaration is not an invocation. Connect each hidden edge to the mechanism
that activates it:

| Mechanism | Evidence to find |
| --- | --- |
| Framework entry | Launch config, manifest, generated host code, or bootstrap |
| Decorator or annotation | Scanner, registration call, proxy, or active config |
| Dependency injection | Container assembly, provider, scope, and selected binding |
| Registry or plugin | Registration time, key, lookup, active set, and dispatch |
| Callback or event | Subscription, publisher, payload, ordering, and handler |
| Reflection or dynamic import | Name source, resolver, load condition, and target |
| Macro or generated code | Input, build step, generated artifact, and selected target |
| Async work | Spawn site, owner, join/cancel path, and error propagation |

Imports, interface implementations, type references, filenames, and AST calls
remain static candidates until this evidence connects them to runtime behavior.

## Identify the Runtime Boundary

Explain only boundaries used by the selected spine:

- For Web or UI code, distinguish request time, browser, server, worker, edge,
  build time, and generated/static execution. In Next.js, verify router type,
  file-system routing, Server and Client Components, route handlers, middleware,
  server actions, caching, and runtime declarations only where relevant.
- For CLI or workers, follow argument or message selection, signals,
  acknowledgement, retry, exit status, in-flight work, and shutdown only when
  they affect the path.
- For libraries, use public API assembly and first use in place of process
  startup. Identify who owns resources and cleanup.
- For agent or LLM systems, trace only the observed loop:

  ```text
  input -> messages/prompt -> model -> response -> tool selection/validation
        -> tool execution -> result reinjection -> stop condition -> output/state
  ```

  Keep model intent separate from host-side tool dispatch and external effects.

## Work Across Languages

When the language has no named guidance, derive the same spine from its build
files, executable or library entry, module system, object assembly, error model,
concurrency model, and resource lifecycle. Explain only language features that
change the observed control flow. Use `Unknown` when runtime selection depends
on configuration or generated artifacts outside the repository.

For concentrated files, mark semantic regions such as assembly, dispatch, core
rules, state mutation, effects, and shutdown. Include the final relevant region;
file length alone does not determine importance.
