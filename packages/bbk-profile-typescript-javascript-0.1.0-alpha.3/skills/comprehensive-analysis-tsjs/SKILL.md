---
name: comprehensive-analysis-tsjs
description: Conduct a broad evidence-based TypeScript/JavaScript architecture, correctness, compatibility, operability, testability, and maintainability survey. Use for inherited codebases, modernization assessments, or whole-system reviews—not as a mandatory precursor to every focused review.
---

# Comprehensive TypeScript/JavaScript Analysis

Act as an expert software architect and code reviewer. Identify material correctness, security, compatibility, operability, testability, and maintainability findings. Recommend refactoring only when it is the smallest responsible remedy.

## Review contract

Before reviewing, bind:

- exact repository, package, revision, and changed or sampled scope;
- runtime targets and supported consumers;
- TypeScript/JavaScript language mode;
- package manager, lockfile, module contract, build and test tools;
- review assertions, assurance depth, available evidence, and excluded scope.

Use repository evidence and executed checks where authorized. Distinguish:

```text
OBSERVED_DEFECT
SUPPORTED_RISK
DESIGN_WEAKNESS
MISSING_EVIDENCE
ADVISORY
COVERAGE_GAP
```

Do not convert an unverified suspicion into a defect. Do not force the report to contain refactors when no material issue is supported.

## Core architectural philosophy

Evaluate through deep-module architecture: small stable public surfaces should hide meaningful implementation complexity. Flag shallow abstractions that add indirection without reducing cognitive load. Do not recommend additional layers unless they materially improve testability, changeability, authority, failure containment, or domain isolation.

Testability is first-class, but dependency injection is a means rather than a goal. Prefer explicit inputs, pure logic, and narrow effects over framework machinery.

## Analysis dimensions

Apply only the dimensions relevant to the subject.

1. **Correctness and invariants** — invalid states, ordering protocols, inconsistent assumptions, unchecked fallthrough, partial updates, precision or coercion errors.
2. **Maintainability and complexity** — unnecessary coupling, high control-flow complexity, over-generalized helpers, hidden state, difficult local reasoning.
3. **Change amplification and evolution** — one concept requiring coordinated changes across unrelated modules, duplicated transformations, lockstep package changes.
4. **Architecture and modularity** — responsibility boundaries, depth, cohesion, information hiding, integration ownership, package and workspace boundaries.
5. **Pattern drift** — several incompatible approaches to the same concern where inconsistency increases cognitive load or operational risk.
6. **Dependency direction** — infrastructure leakage, circular package references, source imports that bypass package contracts, unstable dependencies flowing inward.
7. **Domain model integrity** — stringly typed identifiers, primitive obsession, duplicated validation, implicit state machines, business rules in presentation or persistence layers.
8. **Invariant duplication** — rules implemented independently in UI, API, services, jobs, database constraints, schemas, or consumers without one authoritative meaning.
9. **Dead code and stale artifacts** — unused exports, orphaned migrations, stale generated files, dead feature flags, obsolete package entry points, unreachable branches.
10. **Type-contract quality** — `any`, assertions, suppressions, declaration drift, unsafe narrowing, weak generic constraints, public inference leaks, missing exhaustiveness.
11. **Runtime-data boundaries** — external values trusted without parsing, schema/type drift, absent/null/undefined confusion, coercion and defaulting, versioned payloads.
12. **Module and package compatibility** — ESM/CommonJS, conditional exports, TypeScript versus runtime resolution, declarations, deep imports, packed consumer behavior.
13. **Testability** — hidden effects, global state, clocks/randomness, process/environment coupling, difficult seams, over-mocking, nondeterministic fixtures.
14. **Test-suite health** — critical-path gaps, unrealistic mocks, missing error/cancellation cases, flaky retries, absent type or package-consumer tests.
15. **Performance and efficiency** — algorithmic cost, event-loop blocking, bundle/startup cost, network waterfalls, memory retention, repeated parsing, build/type-check cost.
16. **Data access and persistence** — transactions, concurrency, idempotency, consistency, migrations, query shape, caching, recovery, domain/persistence separation.
17. **Robustness and error semantics** — error classification, causal context, cancellation, retries, partial success, graceful degradation, process exit behavior.
18. **Async, resources, and state** — races across `await`, floating promises, timers, listeners, streams, workers, child processes, backpressure, open handles, shutdown.
19. **Observability and durability** — traceability of state mutation, correlation, metrics, logs, source maps, redaction, replay and recovery evidence.
20. **Security and trust boundaries** — validation, injection, path/command/URL handling, DOM sinks, secrets, registry/install scripts, dependency and native-addon risk.
21. **Operational readiness** — clean build and install, startup/shutdown, configuration, migration, deployment, rollback, runtime support, source maps, package identity.
22. **Configuration complexity** — effective behavior spread across environment, package scripts, tsconfig inheritance, bundler config, feature flags, runtime overrides.
23. **Generated artifacts** — canonical source, generator identity, deterministic regeneration, stale output, schema/client/declaration drift.
24. **Documentation and onboarding** — public contract, domain assumptions, operational procedures, supported matrix, architecture and failure semantics.
25. **Abstraction return on investment** — whether packages, interfaces, services, wrappers, generics, decorators, middleware, helpers, and frameworks hide volatility or merely add surface area.
26. **Browser/UI concerns, when applicable** — accessibility, hydration, CSP/XSS, browser compatibility, state ownership, navigation, performance, progressive enhancement.
27. **Hypermedia or server-driven UI, when applicable** — assess only when it matches the declared architecture. Do not presume HTMX, Alpine, React, or another UI model is universally correct.

## TypeScript/JavaScript-specific distinctions

Never collapse these into one claim:

```text
semantic type check
transformation or emit
bundling
runtime execution
declaration resolution
packed package consumption
browser or host compatibility
```

Type declarations do not validate runtime inputs. A successful source-workspace test does not prove the packed artifact works. A bundler pass does not prove semantic type correctness. A TypeScript import resolving does not prove Node or a browser resolves it.

## Large codebases

Partition work by non-overlapping assertion families, runtime surfaces, or responsibility boundaries. Give each reviewer an exact charter. Deduplicate findings centrally.

Do not assign several broad reviewers to independently inspect the entire repository unless complementary independence is explicitly required. A broad survey may identify hotspots and recommend focused follow-up; it does not automatically trigger every specialist pack.

## Finding format

Return a prioritized list. For each finding use:

```text
Finding ID:
Class: OBSERVED_DEFECT | SUPPORTED_RISK | DESIGN_WEAKNESS | MISSING_EVIDENCE | ADVISORY | COVERAGE_GAP
Category:
Context/Location:
Observed evidence:
Issue:
Failure scenario or consequence:
Consequence: critical | high | medium | low
Likelihood: high | medium | low | unknown
Confidence: high | medium | low
Priority: block | now | next | backlog | advisory
Affected consumers or assertions:
Compatibility impact:
  source_types: none | compatible | breaking | unknown
  runtime_api: none | compatible | breaking | unknown
  module_resolution: none | compatible | breaking | unknown
  package_contents: none | compatible | breaking | unknown
  wire_or_schema: none | compatible | breaking | unknown
  persistence: none | compatible | breaking | unknown
  configuration_or_cli: none | compatible | breaking | unknown
  operational_behavior: none | compatible | breaking | unknown
Remedy cost: low | medium | high
Recommended remedy:
Recommended verification:
Change risk:
```

Use `not applicable` for compatibility dimensions that genuinely do not apply. Include a short code snippet only when it materially clarifies the change.

## Coverage summary

End with:

```text
Subject and revision:
Inspected:
Commands and evidence run:
Evidence reused:
Not inspected:
Focused packs considered:
Focused packs triggered:
Not applicable:
Coverage gaps:
Residual uncertainty:
Overall disposition: PASS | FAIL | BLOCKED | INCONCLUSIVE
```

`PASS` means the exact declared review assertions are satisfied. It does not mean the entire codebase is defect-free.

## Do not recommend

- abstractions with no credible volatility, isolation, authority, or testing benefit;
- splitting modules solely for size;
- framework or package-manager replacement without a demonstrated problem;
- dependency-injection frameworks where explicit parameters or constructors suffice;
- microservices without strong operational and organizational evidence;
- universal ESM/CommonJS dual publication;
- universal conversion of checked JavaScript to TypeScript;
- blanket strictness-flag changes without migration analysis;
- a schema library, test runner, bundler, linter, or UI framework merely because it is familiar;
- replacing substantial client code with hypermedia techniques unless the declared interaction and operating model support that choice.

## Alpha.4 structure survey

When structure contracts or execution slices exist, use them as review subjects rather than inventing a replacement design. Identify material differences in public/shared contracts, ownership, state/failure paths, effects, package consumers, and touchpoints. Preserve harmless private differences inside delegated freedom. A broad survey may recommend a focused structure review, but must not automatically fan out every TS/JS specialist.
