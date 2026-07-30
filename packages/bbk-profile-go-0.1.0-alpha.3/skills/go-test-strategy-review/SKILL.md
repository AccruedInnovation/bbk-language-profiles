---
name: go-test-strategy-review
description: Design or review proportional Go test strategy, cache policy, concurrency tests, fuzzing, properties, fixtures, coverage, mutation, benchmarks, and reproducible evidence.
---

# Go Test Strategy Review

Design tests from assertions and failure modes rather than coverage targets or framework fashion.

## Establish the subject

Record:

- exact candidate and packages/modules;
- toolchain, workspace, tags, target, CGO, experiments, and PGO configuration;
- assertions and consequence;
- repository test commands;
- cache and retry policy;
- external services, clocks, randomness, files, ports, environment, and process state.

## Test levels

Select among:

- package-internal tests;
- external-package consumer tests;
- examples;
- integration and database tests;
- `httptest.ResponseRecorder` for handler logic;
- `httptest.Server` or real transport tests for streaming, cancellation, TLS, connection, redirect, and shutdown behavior;
- subprocess and signal tests;
- real-platform and cross-platform compile tests;
- downstream module fixtures;
- release-artifact smoke tests.

Mocks should isolate unstable external effects, not replace the integration behavior being asserted.

## Determinism and isolation

Review:

- `t.Cleanup`, `t.TempDir`, and `t.Setenv` use;
- parallel-test safety;
- global state, environment, working directory, ports, time, randomness, and shared databases;
- test order and `-shuffle` seed preservation;
- timeouts and deadlock diagnostics;
- fixture ownership and cleanup;
- generated and golden artifact review.

## Cache and flakiness

Candidate acceptance declares whether cached success is valid. Fresh execution commonly uses `-count=1` or a repository equivalent.

Retries retain every attempt. A sequence such as FAIL/PASS/PASS is `FLAKY`, not an unqualified pass. Preserve the failing output, seed, order, environment, and suspected cause.

## Concurrency methods

- Race detector for executed Go concurrency paths;
- `testing/synctest` for controlled time and contained goroutines on supported Go versions;
- repetition and shuffled order;
- deterministic clocks and failpoints;
- representative race-enabled workloads;
- state-machine/model tests for lifecycle protocols.

No one method proves complete concurrency correctness.

## Generative and adversarial methods

Use native fuzzing for parsers, decoders, paths, protocols, templates, and untrusted inputs. Preserve seed corpus, crash input, minimized reproducer, budget, and resource ceiling.

Use property, model-based, differential, or metamorphic testing when expected output can be derived from invariants or an independent implementation.

Use deterministic failpoints around persistence, migrations, multi-step effects, restart, and cleanup.

## Coverage, mutation, and benchmarks

- Coverage identifies unexercised paths; it is not a universal quality score.
- Mutation testing is triggered for high-value logic or weak assertions and uses a repository-qualified tool; preserve surviving mutants and timeouts.
- Benchmarks require stable workload, environment, samples, variance, and correctness guardrails.
- PGO and performance profiles are evidence artifacts with digest and provenance.

## Test receipt

Require:

```text
candidate and profile digest
exact Go version and directives
GOWORK/GOMOD, module and sum digests
GOOS/GOARCH/CGO/tags/experiments/GODEBUG/PGO
package selection and command argv
cache/retry policy
start/end and exit/signal
structured test output
seeds, corpora, traces, profiles, coverage, and artifacts
```

## Return

Return assertion coverage, selected methods and rationale, missing or duplicated tests, flakiness, environment gaps, evidence requirements, cost, and whether the planned strategy is proportionate.

## Execution-slice integration

For each slice, ensure the declared Go touchpoint is real in the exact module/workspace, toolchain, target, build-tag, and CGO configuration. Bind every assertion to candidate evidence. Preserve race reports, synctest assumptions, fuzz inputs, shuffle seeds, flaky attempts, generated diffs, downstream fixtures, package artifacts, and scaffolding disposition as applicable.

