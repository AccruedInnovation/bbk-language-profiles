---
name: python-test-strategy-review
description: Review Python test architecture, isolation, fixtures, installed-artifact coverage, properties, state machines, fuzzing, mutation, concurrency, migrations, flakiness, coverage interpretation, and evidence preservation.
---

# Python Test Strategy Review

Use for test-system work, consequential behavior changes, weak regression protection, package/release claims, concurrency, persistence, parsers, or explicit assurance design.

## Start from assertions and failure models

For each material behavior identify:

- observable assertion;
- exact subject and environment;
- cheapest sufficient method;
- oracle and fixtures;
- expected failure modes;
- evidence and reproducer;
- completing work unit and independence need.

Do not substitute a test count or coverage percentage for assertions.

## Test layers

Assess the appropriate mix of:

- unit/example tests for local deterministic behavior;
- integration tests for database, filesystem, network, framework, subprocess, and service boundaries;
- contract tests for packages, APIs, plugins, protocols, and consumers;
- end-to-end or operational tests for actor-visible flows;
- property-based tests for invariants over input spaces;
- state-machine/model-based tests for lifecycles and protocols;
- differential tests against prior or independent behavior;
- metamorphic tests where exact outputs are hard to enumerate;
- fuzzing for parsers, decoders, archives, protocols, and untrusted data;
- deterministic failpoints for persistence and multi-step effects;
- mutation testing for high-value logic and test-strategy gaps;
- snapshot/golden tests with an explicit review and update policy;
- performance and resource regression tests with representative workloads.

## Isolation and realism

Inspect:

- test-order dependence;
- leaked globals, caches, environment, monkeypatches, logging, and event loops;
- fixture scope and cleanup;
- real clocks, sleeps, randomness, and preserved seeds;
- network access in unit tests;
- database transaction rollback assumptions;
- mock behavior that cannot expose real integration failures;
- temporary paths, permissions, case sensitivity, locale, timezone, and encoding;
- checkout import versus installed package;
- editable versus normal installation;
- selected Python versions, interpreters, platforms, extras, and dependency ranges.

## Async and concurrency tests

Test cancellation, timeout, task ownership, shutdown, thread/process crashes, start methods, duplicate work, partial effects, and cleanup. Preserve schedules, seeds, timeouts, and attempt history. Do not represent a flaky retry as a clean pass.

## Packaging tests

Release-sensitive projects should build sdist and wheel, inspect contents, install cleanly, import outside the checkout, test entry points/resources, and where applicable build a wheel from the sdist. Distinguish artifact evidence from source-tree evidence.

## Coverage and mutation

Coverage is a gap-finding aid, not a universal quality score. Mutation testing is triggered for high-value logic or a declared gap; surviving mutants, equivalent mutants, timeouts, and tool failures remain distinct. The profile does not install a mutation tool silently.

## Evidence preservation

Preserve:

- property seeds and minimized examples;
- fuzz corpus/crash input/minimized reproducer and budget;
- model states or schedules;
- every flaky retry;
- snapshot predecessor/successor and disposition;
- mutation details and surviving mutants;
- migration initial/final/rollback states;
- artifact and environment digests;
- benchmark workload, samples, variance, and baseline.

Return coverage of assigned assertions, duplicate or missing methods, realism gaps, flakiness, evidence quality, and a proportional test plan. Do not require every method for every project.
## Structure and slice evidence

For a structure contract, ensure each consequential key contract, ownership boundary, behavior path, failure/recovery path, and fixed decision has an appropriate seam. For an execution slice, verify the declared integrated touchpoint rather than only its component files. Preserve exact candidate, interpreter, package subject, environment, seed, corpus, process-start method, and scaffolding disposition where relevant.
