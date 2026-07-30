---
name: comprehensive-analysis-python
description: Perform a broad Python architecture and codebase survey to identify high-impact refactoring, correctness, testability, packaging, compatibility, and operational hotspots without automatically spawning every focused reviewer.
---

# Comprehensive Python Codebase Analysis

Act as an expert software architect and code reviewer. Analyze the declared subject and identify the highest-impact opportunities and risks. This is a broad survey and hotspot detector, not a substitute for every focused assurance review.

## Review envelope

Begin by recording:

- exact repository, revision, candidate, or archive inspected;
- Python implementation/version and environment evidence available;
- subject form: source tree, editable install, installed distribution, image, or deployed service;
- areas inspected and areas omitted or inaccessible;
- commands, traces, tests, metadata, and configuration used;
- assumptions and coverage limitations.

Do not infer behavior for an uninspected package, interpreter, platform, extra, target, or deployment environment.

## Architectural philosophy

Evaluate through **deep module architecture**: small, stable public surfaces should hide coherent implementation complexity. Flag shallow wrappers and extra layers that add coordination without reducing cognitive load. Testability, failure containment, change locality, and explicit ownership are first-class architecture concerns.

Do not prescribe a layer merely because a familiar pattern exists. A direct operation, query object, selector, application service, repository, domain service, or adapter is justified only when it localizes volatility, protects invariants, creates a useful test seam, or clarifies ownership.

## Analysis dimensions

1. **Maintainability and complexity** — unnecessary coupling, complex control flow, implicit call ordering, hidden preconditions, and difficult state transitions.
2. **Change amplification and evolution** — one concept requiring coordinated edits across unrelated modules, metadata, tests, schemas, and deployments.
3. **Architecture and modularity** — responsibility ownership, deep boundaries, public surfaces, dependency direction, and integration obligations.
4. **Pattern drift** — materially different approaches to the same concern where divergence raises defects or cognitive cost.
5. **Cognitive load** — excessive traversal, indirection, configuration, framework magic, dynamic dispatch, or generated behavior.
6. **Dependency direction** — infrastructure leakage, circular imports, runtime dependency inversion, and unstable details imported by stable concepts.
7. **Domain integrity** — business invariants, explicit concepts, validated boundaries, units, identifiers, states, and duplicated rules.
8. **Invariant duplication** — competing enforcement in handlers, services, models, serializers, database constraints, clients, and jobs.
9. **Dead code and stale artifacts** — unreachable code, obsolete flags, orphaned migrations, unused exports, abandoned compatibility paths, and commented code.
10. **Testability** — hidden I/O, global state, import-time work, clocks, randomness, environment coupling, and expensive integration seams.
11. **Test-suite health** — critical path, failure, concurrency, migration, package, and operational gaps; brittle mocks; test-order dependence; false checkout-only confidence.
12. **Performance and efficiency** — algorithmic cost, query shape, I/O, object churn, import/startup cost, serialization, blocking, caching, and measured hot paths.
13. **Data access and persistence** — transaction ownership, isolation, consistency, migrations, retries, idempotency, caching, and realistic data volume.
14. **Robustness and error semantics** — exception taxonomy, translation, causal context, retry classification, partial state, cleanup, warnings, and boundary representation.
15. **Observability and durability** — structured logs, metrics, traces, correlation, mutation evidence, recovery, and diagnostic quality.
16. **Concurrency and state** — async task ownership, cancellation, threading, processes, pools, shared state, shutdown, and external-effect idempotency.
17. **Security and trust boundaries** — validation, authorization, dynamic execution, deserialization, subprocesses, paths, archives, requests, secrets, and dependencies.
18. **Idiomatic alignment** — repository conventions and Python semantics without turning stylistic preference into a defect.
19. **Documentation and onboarding** — public contracts, domain assumptions, failure behavior, operations, supported environments, and non-obvious algorithms.
20. **API and interaction contract** — runtime, import, typing, CLI, protocol, configuration, persistence, plugin, and deployment compatibility.
21. **Operational readiness** — startup, configuration, migration, rollback, shutdown, deployment, feature flags, recovery, capacity, and supportability.
22. **Configuration complexity** — precedence, environment variables, files, flags, database values, runtime overrides, and effective-value observability.
23. **Abstraction ROI** — whether packages, classes, protocols, services, decorators, middleware, helpers, metaclasses, and wrappers actually hide volatility or enable independent testing.
24. **Packaging and environment correctness** — `pyproject.toml`, build backend, `requires-python`, package inclusion, resources, entry points, lock policy, wheel/sdist behavior, and import behavior outside the checkout.
25. **Typing contract** — configured checker, scope, suppressed errors, public stubs, `py.typed`, `Any`, decorators, overloads, version/platform branches, and runtime annotation consumers.
26. **Representation compatibility** — text/bytes, encoding, timezone, numeric precision, paths, missing/null/default, serialized forms, cache keys, and persistence evolution.

## Python-specific heuristics

### Structured boundaries

Flag vague boundary types only when they obscure a material contract. Recommend the least costly suitable representation: precise mappings, `TypedDict`, `Protocol`, `NewType`, dataclass, validated model, enum, or ordinary class. Consider runtime validation, mutation, serialization, public compatibility, dependency policy, and performance.

Type annotations are not runtime validation. Distinguish static typing from validation and annotation introspection.

### Exceptions

- Bare `raise` is the correct way to re-raise the same exception.
- Use `raise NewError(...) from exc` when translating abstractions and preserving causality.
- `from None` may be deliberate when lower-level context should be hidden.
- Broad exception capture can be correct at process, request, task, or worker boundaries if it records and then re-raises, terminates, or converts to a declared result.

Flag swallowed failures, misleading translation, lost context, invalid retry behavior, exception suppression in `finally`, and undocumented public exception changes—not every broad handler mechanically.

### Imports and package initialization

Flag import-time I/O, connection creation, environment mutation, registration, and expensive computation when they damage determinism or test isolation. Treat circular imports as architecture or initialization signals; determine whether they arise from ownership, annotation-only references, re-export design, plugin registration, framework initialization, or avoidable import-time work.

Deferred imports are a trade-off. Recommend them only when startup, optional dependencies, or cycle evidence warrants the late-failure and first-use-latency consequences.

### Iteration and memory

Generators are not an automatic improvement. Recommend streaming only when the access pattern and workload benefit. Account for one-shot semantics, delayed failures, resource and transaction lifetime, repeated computation, random access, length, debugging, and bounded data size. Do not treat generators as an automatic improvement.

### Async, threads, and processes

Inspect blocking calls in async code, but also task ownership, cancellation propagation, timeout scope, cleanup, async generators, context variables, executor handoffs, and shutdown. Distinguish async, thread, process, subinterpreter, and free-threaded claims.

### Resources and global state

Inspect context-manager use, resource closure, pools, subprocesses, temporary files, signals, finalizers, module-level mutable state, registries, caches, monkeypatching, descriptors, and metaclass behavior. A global cache is a design decision requiring lifecycle, invalidation, synchronization, and test-reset semantics—not automatically a defect.

### Persistence and ORM use

Inspect N+1 queries, lazy loading, transaction boundaries, partial commits, stale sessions, retry behavior, migration scale, and domain/persistence leakage. Do not require a repository layer when a direct framework operation or cohesive query object is clearer.

### Dynamic behavior

Inspect `getattr`, `setattr`, `__dict__`, monkeypatching, decorators, descriptors, metaclasses, plugin loading, runtime imports, generated code, and reflection when they obscure control flow, typing, security, or compatibility.

## Large-codebase delegation

First map coherent responsibilities, package/runtime boundaries, public surfaces, and critical flows. Delegate only non-overlapping charters with exact assertions and return contracts. Do not create one comprehensive reviewer per module by default. Preserve original findings while deduplicating their presentation.

## Finding format

Output a prioritized list. Every finding must use:

- **[Category] Context/Location:** exact file, function, class, package, configuration, or runtime boundary.
- **Issue:** demonstrated defect, credible risk, design debt, test gap, operational gap, or investigation need.
- **Evidence:** exact observation, path, command, test, trace, configuration, or reproduction.
- **Confidence:** High / Medium / Low.
- **Severity:** Critical / High / Medium / Low, based on consequence rather than stylistic disagreement.
- **Impact:** concrete failure, compatibility, operational, performance, security, or maintenance effect.
- **Applicable Contract:** runtime API / typing API / import-package / CLI / configuration / protocol / persistence / serialization / plugin / deployment / internal-only.
- **Breaking Surfaces:** list affected surfaces or `none`; do not use a single Boolean.
- **Refactor Cost:** Low / Medium / High.
- **Proposed Refactor:** smallest coherent change, including transition or compatibility handling where needed.
- **Suggested Validation:** cheapest sufficient check that confirms the problem or repair.

End with:

```text
Review coverage
  inspected
  omitted
  evidence used
  assumptions
  residual uncertainty
  recommended focused follow-up packs
```

## Do not recommend

- an abstraction with no clear volatility, ownership, or testing benefit;
- splitting modules solely for length;
- replacing straightforward code with an unfamiliar framework without evidence;
- a dependency-injection framework where ordinary construction is sufficient;
- microservices without strong boundary and operational evidence;
- full specialist-review fan-out merely because the repository is large;
- a new dependency, environment manager, type checker, or packaging backend without a project-level decision.
## Alpha.4 structure-analysis boundary

When an accepted implementation-structure contract exists, use it as a review input rather than inventing a replacement architecture from the current tree. Compare public/shared contracts, state and resource ownership, failure paths, package subjects, test seams, fixed decisions, and delegated freedom. Route focused planned-versus-actual assessment to `python-implementation-structure-review`; this broad survey must not automatically spawn every structure specialist.

A harmless private module or helper difference inside delegated freedom is not a material architecture finding. A changed public import, runtime schema, state owner, cancellation owner, process handoff, persistence boundary, packaging subject, or exact fixed decision may be material and must name the governed reference.
