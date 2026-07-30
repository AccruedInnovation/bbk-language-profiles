---
name: tsjs-development-practices
description: Apply practical TypeScript and JavaScript implementation guidance without imposing one framework, runtime, package manager, schema library, or module strategy. Use for bounded TS/JS worker tasks.
---

# TypeScript/JavaScript Development Practices

Apply this as an applicability-aware worker reference. Repository conventions and the work-unit contract are authoritative.

## 1. Establish which guarantees exist

Before editing, determine:

- whether semantic type checking actually runs;
- whether JavaScript is checked through `checkJs`, `@ts-check`, or JSDoc;
- whether the build is transpile-only;
- which runtime executes the result;
- which artifact consumers receive;
- which module-resolution mode each tool uses.

Do not infer type safety from `.ts` syntax, a successful bundler run, or runtime-native TypeScript execution.

## 2. Keep runtime trust boundaries explicit

Treat values from files, environment variables, HTTP, databases, queues, browser storage, workers, plugins, SDKs, and JSON as untrusted until parsed.

- Begin with `unknown`, bytes, or strings at external boundaries.
- Validate, normalize, and convert once at the boundary.
- Preserve absent, `undefined`, and `null` distinctions where behavior depends on them.
- Keep schemas, generated types, validators, and implementations from drifting.
- Avoid assertions that merely tell the checker to trust data the program has not checked.
- Return useful typed errors without exposing sensitive values.

## 3. Use the type system to reduce invalid states

Prefer:

- discriminated unions for state and variant behavior;
- branded or opaque identifiers when primitive confusion is consequential;
- exhaustive `never` checks at important closed unions;
- `unknown` rather than `any` at uncertain boundaries;
- narrow interfaces aligned with responsibility;
- explicit result or error contracts where callers must react differently;
- exact public return types when inference would leak implementation detail.

Use `any`, assertions, non-null assertions, ambient declarations, and suppressions only with a local rationale and a test or invariant appropriate to the risk. Do not turn style preferences into blanket findings.

## 4. Keep modules deep and package boundaries real

- Group code around coherent responsibility and change locality, not arbitrary file size.
- Avoid barrel exports that hide cycles or unintentionally expand the public API.
- Do not import sibling package source paths to bypass declared package contracts.
- Keep infrastructure details out of stable domain code where doing so reduces change amplification.
- Prefer one canonical implementation of business invariants; UI checks are convenience, not authority.
- Treat `package.json` exports, declarations, runtime entry points, and consumer fixtures as the package contract.

Do not add an interface, service, repository, wrapper, or dependency-injection framework unless it hides volatility, improves testability, or establishes a material boundary.

## 5. Design async and resource lifetimes

For promises, streams, timers, workers, subprocesses, listeners, sockets, transactions, and handles:

- define ownership and completion;
- propagate cancellation and deadlines;
- distinguish timeout from cancellation;
- settle every promise path exactly once;
- avoid floating promises and lost async errors;
- preserve backpressure and partial-write semantics;
- clean listeners, timers, workers, and child processes;
- make retry and idempotency explicit;
- test state after interruption, not only the happy path;
- avoid holding a transaction or mutable shared assumption across unrelated `await` points.

A single-threaded event loop does not eliminate races between callbacks or across `await` boundaries.

## 6. Make errors operationally meaningful

- Preserve causal context without wrapping every layer redundantly.
- Separate programmer defects, invalid input, transient dependency failures, conflicts, authorization failures, and cancellation.
- Do not catch an error merely to log and continue ambiguously.
- Define process exit codes and stdout/stderr behavior for CLIs.
- Redact secrets and personal data from logs and error payloads.
- Keep user-facing messages distinct from diagnostic evidence where appropriate.

## 7. Respect module and runtime contracts

- Do not mix ESM and CommonJS casually.
- Use explicit extensions and entry points according to the declared runtime and resolution mode.
- Test dynamic imports, conditional exports, top-level await, and default/named interop where claimed.
- Do not assume TypeScript path aliases work at runtime.
- Keep browser-only and server-only code from leaking across build boundaries.
- Treat dual-package output as an additional compatibility surface, not a free default.

## 8. Treat package installation and generation as effects

- Preserve the repository package manager and lockfile.
- Do not regenerate a lockfile unless the task authorizes dependency change.
- Inspect lifecycle scripts, native builds, downloaded binaries, patches, overrides, and registry configuration when affected.
- Keep code generation deterministic and identify the canonical source.
- Run final generator checks in check-only mode; do not silently rewrite a frozen candidate.
- Test the packed or deployed artifact rather than relying on workspace hoisting and source access.

## 9. Test contracts at the right layer

Use the cheapest sufficient method:

- type fixtures for compile-time acceptance and rejection;
- unit tests for pure behavior;
- integration tests for real boundaries;
- actual built artifact execution for emit and packaging claims;
- clean consumer installation for package contracts;
- real browser tests for browser behavior that DOM emulation cannot establish;
- property, model, differential, fuzz, mutation, or fault testing only when the risk warrants them.

Do not use coverage percentage as a proxy for correctness. Preserve seeds, minimized failures, retries, and flaky attempts.

## 10. Measure performance before changing architecture

Consider:

- algorithmic work and data volume;
- event-loop blocking;
- bundle and startup cost;
- repeated serialization and parsing;
- network waterfalls and over-fetching;
- allocation and garbage-collection pressure;
- memory retention through closures, listeners, caches, or source maps;
- build and type-check time.

Do not recommend memoization, workers, streaming, code splitting, alternate data structures, or a new framework without a measured or clearly bounded problem.

## 11. Handoff

Return:

- changed files and package boundaries;
- runtime, module, and language assumptions used;
- commands run and exact results;
- tests not run and why;
- public type/runtime/package compatibility impact;
- generated or packed artifacts affected;
- residual uncertainty and focused validation recommended.

## 10. Implement against an accepted structure contract

When an `ImplementationStructureContract` applies:

- implement its fixed package/module owners, public/shared contracts, state/effect ownership, behavior paths, seams, and prohibited shortcuts;
- choose private helpers, local algorithms, and internal test utility placement only inside delegated bounds;
- route any proposed change to a fixed export, declaration, runtime schema, owner, cancellation contract, effect boundary, or touchpoint through the named change route;
- keep emitted runtime behavior and exported declaration behavior aligned;
- record any unavoidable planned/actual divergence before candidate freeze.

For execution slices, integrate the smallest closure needed for the declared touchpoint. Do not optimize for one file or one technical layer. Name and disposition temporary path aliases, fixture adapters, mock servers, shims, generated declarations, temporary package exports, and host stubs.
