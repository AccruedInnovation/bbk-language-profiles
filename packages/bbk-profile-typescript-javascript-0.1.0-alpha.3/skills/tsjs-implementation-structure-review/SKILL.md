---
name: tsjs-implementation-structure-review
description: Review a TypeScript/JavaScript ImplementationStructureContract, ExecutionSlice, or exact candidate for consequential package, module, export, declaration, runtime-schema, state, effect, async-resource, consumer, and touchpoint conformance without policing harmless private layout.
---

# TS/JS Implementation Structure Review

Use this pack only when the generic BBK applicability level is `contract`, a material inline structure concern is being reviewed, or a planned-versus-actual assertion requires it. Do not preload it into ordinary workers.

## Authority and subject

Bind:

- exact generic contract ID, revision, and digest;
- exact slice IDs where applicable;
- exact candidate or validation cohort;
- preflight/profile-lock identity;
- fixed decisions, delegated freedom, prohibited shortcuts, and acceptance criteria;
- exact assertions assigned to this review.

The generic BBK object remains authoritative. This skill proposes findings; it does not change scope, grant effects, waive assertions, or declare readiness/release.

## Type-driven structure checks

Review six meanings of “type”:

1. **Identity:** distinct domain, package, resource, route, message, and host identities do not collapse into interchangeable primitives where confusion is consequential.
2. **State:** consequential closed states and transitions are explicit and exhaustively handled; static types do not conceal runtime transition gaps.
3. **Boundary:** exported types, runtime schemas, declarations, package exports, module conditions, messages, configuration, and consumer behavior remain synchronized.
4. **Ownership:** one package/module owns mutable state, timers, subscriptions, workers, streams, caches, processes, AbortSignals, cleanup, and source-of-truth decisions.
5. **Failure:** absence, rejection, conflict, timeout, cancellation, partial completion, stale input, degraded operation, and recovery are caller-visible where handling differs.
6. **Evidence:** not-run, blocked, tool error, inconclusive, pass, and fail remain distinct.

Recommend a type or abstraction only when it prevents a material invalid combination, localizes an invariant, clarifies ownership, stabilizes a boundary, improves change locality, creates a real seam, or hides consequential complexity.

## Planned-versus-actual materiality

Treat these as normally material:

- public/shared export or declaration surface;
- package `exports`/`imports`, entry-point, ESM/CommonJS, browser, bin, or host/plugin shape;
- runtime schema, serialized event/message, persistence, configuration, or migration contract;
- state/effect/resource owner;
- cancellation, cleanup, stream/backpressure, worker, subscription, process, or shutdown owner;
- fixed decision or prohibited shortcut;
- test seam or touchpoint required for independent work;
- behavior path whose owner or failure semantics changed.

Treat these as normally within delegated freedom unless independently poor:

- private helper names and locations;
- equivalent local iteration style;
- private test utility placement;
- internal refactoring that preserves fixed ownership, public contracts, behavior, effects, and evidence.

Do not use raw file-count or exact private-tree equality as the primary conformance rule.

## Slice quality

A TS/JS execution slice should:

- expose one real CLI, API, UI, package-consumer, protocol/host, report, or other inspectable touchpoint;
- include the TypeScript/static path and the actual emitted/runtime/consumer path where relevant;
- name one integration owner;
- include all packages/modules/contracts required to make the touchpoint real;
- bind explicit assertions and evidence;
- contain or reverse effects;
- name temporary aliases, mocks, fixture adapters, generated declarations, temporary exports, shims, or servers and their disposition;
- enable a clear next slice or capability.

A foundation-first slice is acceptable only when a vertical touchpoint would be misleading, it retires a named feasibility/safety risk, it has its own inspectable observation, and it names the next integrated slice.

## Review disposition

Return exactly one:

- `CONFORMS`;
- `ADVISORY_DIVERGENCE`;
- `MATERIAL_DIVERGENCE`;
- `BLOCKED`;
- `NOT_APPLICABLE`.

For material divergence, identify the exact fixed decision, public/shared contract, owner, behavior path, effect boundary, assertion, or slice affected. For blocked review, identify the missing inventory, built artifact, declaration, consumer, runtime, browser, or host evidence. Preserve delegated private differences without manufacturing findings.
