---
name: go-evidence-reproducer
description: Capture reproducible Go test, race, fuzz, synctest, flaky, coverage, mutation, benchmark, profile, crash, module, cgo, and release evidence bound to an exact candidate and profile resolution.
---

# Go Evidence and Reproducer

Every evidence item proves one stated assertion against one stated subject.

## Required identity

Capture:

```text
candidate digest
effective BBK Go profile digest
exact Go version and go/toolchain directives
GOWORK, GOMOD, go.mod/go.sum/vendor digests
GOOS, GOARCH, architecture tuning, CGO, CC/CXX
tags, GOFLAGS, GOEXPERIMENT, relevant GODEBUG
PGO profile digest
selected modules/packages and command argv
cache and retry policy
environment and external fixture identity
start/end, exit/signal, logs, and artifacts
```

Redact secrets while retaining enough identity to detect incompatible reruns.

## Technique-specific evidence

- **Race:** full report, conflicting stacks, goroutine creation stacks, target, workload, and every attempt.
- **Fuzz:** seed corpus digest, crash input, minimized reproducer, target, duration, limits, and regression fixture.
- **Synctest:** controlled-time assumptions, bubble contents, blocked/wake behavior, and deadlock result.
- **Shuffle/repetition:** exact seed, count, order, and all outcomes.
- **Flaky:** all attempts and environment; never collapse FAIL/PASS into PASS.
- **Golden/snapshot:** prior and proposed artifact plus review disposition.
- **Coverage:** instrumented package set, unit/integration scope, mode, and critical uncovered paths.
- **Mutation:** tool/version, mutants, surviving/killed/timeout/tool-error dispositions, and selected scope.
- **Benchmark/PGO:** workload, samples, variance, CPU/memory environment, baseline, profiles, and correctness guardrails.
- **Crash/failpoint:** fault location, durable state before/after, restart trace, and reconciliation.
- **Module:** workspace mode, replacements, vendor/proxy state, graph, and downstream fixture.
- **cgo/native:** Go and C toolchains, libraries, target, sanitizer/checkptr mode, and ABI fixture.
- **Release:** artifact digest, `go version -m`, flags, VCS state, package/archive manifest, install/remove result.

## Result semantics

Keep these distinct:

```text
PASS
FAIL
BLOCKED
ERROR
INCONCLUSIVE
NOT_APPLICABLE
SKIPPED_BY_POLICY
FLAKY
```

Evidence reuse requires the same candidate, profile, command, configuration, toolchains, dependencies, fixtures, and assertion semantics.

## Return

Return assertion, subject, evidence identity, result, reproduction command, preserved artifacts, reuse decision, coverage gap, and residual uncertainty.

## Structure evidence

Record generic contract/slice digests, Go projection digests, preflight digest, actual-inventory digest, candidate digest, fixed-decision evidence, delegated differences, and the exact planned-versus-actual comparison. Keep unknown evidence separate from conformance and do not let a profile projection become canonical BBK state.

