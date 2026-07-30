# Alpha.4 Python profile design note

## 1. Meaningful type concepts

Python type-driven development uses domain identities, closed enum states, dataclass/value forms, typed mappings, consumer-defined protocols, abstract bases when runtime nominal behavior is required, runtime schemas, exception/result dispositions, resource and task owners, cancellation contracts, process messages, serialization shapes, public typing exports, and evidence dispositions that distinguish not-run, blocked, error, inconclusive, pass, and fail.

Static annotations are one evidence class. Runtime validation, package/consumer behavior, resource lifetime, process behavior, persistence, and operations still require runtime or operational evidence.

## 2. Inline versus contract treatment

Use `none` for routine private work whose shape is already constrained and low risk.

Use `inline` for a compact work-unit structure note when one package/module boundary or local state owner needs clarification but independent work does not require a separately accepted shared contract.

Use `contract` for public runtime or typing APIs, import/package subjects, runtime validation boundaries, state/resource/task/process ownership, persistence or migration, plugins, multi-package work, native extensions, effect/security boundaries, or difficult-to-reverse topology.

## 3. Touchpoint vocabulary

Python touchpoints include public imports, API calls, installed CLI entry points, clean wheel consumers, plugin discovery, runtime-validation positive/negative cases, async cancellation flows, process/job handoffs, migration rehearsals, package inspection, tests, reports, protocol traces, and deployed service observations.

## 4. Material planned/actual differences

Material differences include changed fixed decisions, public import/export or typing drift, changed entry-point groups, missing package subjects, changed runtime schema or serialization contract, changed state/task/process/resource owner, altered cancellation/recovery/effect boundary, or a slice whose required integrated touchpoint no longer exists.

Private helper names, equivalent internal module placement, iteration strategy, and private test utility layout are not material when they remain inside delegated freedom and preserve quality.

## 5. Evidence authority classes

- Deterministic: schema validation, canonical digests, static package/module inventory, candidate path comparison, profile resolution and lock generation.
- Agent-reviewed: abstraction depth, fixed-versus-delegated quality, behavior-path coherence, change locality, exception and ownership design.
- Tool-authoritative: repository formatter/linter/type checker/tests/build backend, package inspection, compatibility tools, migration runner, native toolchain.
- Simulator-based: project-specific service, queue, process, or external-system simulators.
- Human-reviewed: accepted structure contract, consequential trade-offs, authority, unsupported-risk disposition.
- Operational: installed artifact, deployment, startup/shutdown, migration, recovery, resource, and real consumer evidence.

## 6. Unsupported or unqualified areas

Embedded/mobile/WASM/GPU Python, OS-vendor packaging, undeclared alternative interpreters, complex scientific native stacks, and platform-specific native/free-threaded claims remain unqualified until tested in an exact environment.
