---
name: rust-evidence-reproducer
description: Capture reproducible Rust test, property, fuzz, Loom, Miri, mutest-rs, benchmark, snapshot, crash, and failpoint evidence in a candidate- and profile-bound BBK result.
---

# Rust Evidence and Reproducer

Preserve enough identity to rerun or honestly classify every material check.

## Common receipt

Record:

- candidate, source, work-unit, assertion, and effective Rust-profile digests;
- rustc, Cargo, host, target, linker, profile, features, packages, and test targets;
- Cargo.lock and relevant `.cargo`/environment digests;
- exact command, current directory, timeout, resource ceiling, and attempt number;
- start/completion time, exit status, stdout/stderr artifact references, and disposition;
- tool version/revision and whether network, credentials, services, or external state were used.

Use distinct states: `PASS`, `FAIL`, `BLOCKED`, `ERROR`, `INCONCLUSIVE`, `NOT_APPLICABLE`, and `SKIPPED_BY_POLICY`.

## Technique-specific artifacts

- Property tests: seed, minimized case, shrink history where available, and committed regression.
- Fuzzing: corpus digest, crash input, minimized reproducer, duration, executions, and resource ceiling.
- Loom: model configuration, bound, failing schedule/trace, and deterministic regression.
- Miri/sanitizer: toolchain, flags, selected tests, target, and unsupported-operation record.
- Snapshots/goldens: old/new bytes or semantic form and explicit review disposition.
- `mutest-rs`: tool revision, nightly, operators/configuration, selected package/targets, baseline result, mutant inventory, surviving mutants, timeouts, crashes, and each disposition.
- Benchmarks: workload/input digest, environment, warmup, samples, distribution, variance, baseline, and operational significance.
- Crash/failpoint: fault location, durable state before/after, restart trace, and cleanup.
- Flaky checks: retain every attempt. A later pass does not erase a prior failure.

## Reuse

Reuse evidence only when the candidate, profile, toolchain, configuration, dependencies, fixture semantics, environment, and assertion are unchanged. Nondeterministic outputs need a fresh-run semantic receipt rather than byte-equality claims.

## Alpha.4 planning-object identity

When applicable, bind receipts to the generic structure-contract digest, execution-slice digest, Rust projection digest, and planned/actual comparison digest. Preserve whether a difference was within delegated freedom, advisory drift, material divergence, blocked, or not applicable.
