---
name: tsjs-test-strategy-review
description: Design or review TypeScript/JavaScript type, runtime, integration, package-consumer, browser, property, fuzz, fault, mutation, performance, and evidence strategy proportionally.
---

# TS/JS Test Strategy Review

Design evidence around exact assertions. Do not maximize test count or coverage percentage.

## Separate test layers

### Static and type-level

Use where applicable:

- semantic type checking;
- JavaScript `checkJs` or `@ts-check`;
- expected-success type consumers;
- expected-failure type fixtures;
- declaration emit and public inference checks;
- project-reference and supported TypeScript-version checks;
- lint rules that establish a declared property.

A type test does not prove runtime behavior.

### Runtime component and integration

- pure unit behavior;
- real boundary integration;
- malformed runtime inputs;
- persistence and transaction behavior;
- cancellation, retry and idempotency;
- streams, timers, workers, subprocesses and shutdown;
- actual emitted entry-point execution;
- generated artifact consistency.

### Package and consumer

- pack/dry-run contents;
- clean installation;
- Node ESM import;
- CommonJS require only when claimed;
- TypeScript NodeNext/bundler consumers;
- plain JavaScript consumer;
- CLI bin behavior;
- browser or host loading;
- declaration and source-map resolution.

### Browser and UI

- real browser for behavior emulators cannot establish;
- accessibility and keyboard interaction;
- routing/history and storage;
- SSR/hydration and server/client boundaries;
- CSP/XSS-sensitive behavior;
- service worker/cache behavior;
- supported browser matrix.

## Higher-assurance techniques

Select only when useful:

- property-based testing for broad input/state invariants;
- fuzzing for parsers, decoders, protocols and untrusted structured data;
- model-based/state-machine testing for workflows and async protocols;
- differential testing against a prior version or independent implementation;
- metamorphic testing when exact expected outputs are difficult;
- deterministic failpoints for persistence and multi-step effects;
- mutation testing for important logic and test-suite discrimination;
- performance, bundle-size and memory regression tests.

Missing optional tooling is advisory. A required technique that cannot run is `BLOCKED`.

## Test realism

Review whether tests accidentally rely on:

- workspace hoisting or undeclared dependencies;
- source aliases absent from runtime;
- transpilation different from production;
- DOM emulation for browser-only behavior;
- fake timers for all scheduling behavior;
- mocks that erase the contract being tested;
- shared mutable fixtures;
- network or wall-clock nondeterminism;
- retries that conceal flakiness;
- snapshots without semantic review;
- source files rather than the built or packed artifact.

## Coverage and selection

Coverage is a navigation aid, not a universal release threshold. Ask:

- which critical assertions have no test;
- which lines are covered without meaningful assertions;
- which failures or variants remain unexercised;
- whether generated and package surfaces are included;
- whether tests run under supported runtime/module conditions;
- whether a cheaper deterministic check can establish the same claim.

## Flakiness and retries

Preserve every attempt. Distinguish:

```text
candidate failure
test assertion defect
fixture defect
infrastructure failure
timing sensitivity
known bounded nondeterminism
```

A later pass does not erase an earlier failure. Retry policy must be declared before the run and include a final disposition.

## Evidence preservation

Record:

- candidate and profile-lock digests;
- runtime, TypeScript, package-manager and test-runner versions;
- package, feature/condition, browser, and environment selection;
- exact command;
- seed and minimized failure;
- corpus or fixture digest;
- all attempts and durations;
- built or packed artifact identity;
- coverage gaps and exclusions.

## Output

Map each material assertion to one completing evidence method and owner. Identify redundant tests, missing layers, unrealistic fixtures, flaky evidence, and inappropriate independence. Return a proportional recommended gate plan rather than “run everything.”

## Execution-slice evidence

For each alpha.4 slice, test the declared integrated touchpoint rather than only its technical layers. Bind static, build, runtime, package-consumer, browser, or host evidence separately. Confirm one integration owner, exact candidate/cohort identity, failure containment, and every temporary scaffold's removal, fixture retention, or promotion-review disposition.
