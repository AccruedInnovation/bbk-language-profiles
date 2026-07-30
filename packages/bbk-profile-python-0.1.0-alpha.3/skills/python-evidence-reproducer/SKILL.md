---
name: python-evidence-reproducer
description: Define and preserve Python interpreter, environment, package, test, seed, corpus, retry, migration, benchmark, artifact, and reproducer evidence for BBK assertions.
---

# Python Evidence and Reproducer

Use evidence to prove one declared assertion against one exact subject.

## Minimum identity

Record:

- candidate and Python-profile digests;
- interpreter implementation, exact version, executable identity, ABI, GIL/free-threaded state;
- operating system, architecture, locale, timezone, encoding, and relevant environment;
- environment manager, lock/resolution digest, installed-distribution inventory digest;
- build backend and version;
- subject mode: source, editable, wheel, sdist-derived wheel, image, or service;
- selected extras, dependency groups, checker targets, process start method, and native toolchain where relevant;
- exact command, configuration, inputs, output, exit state, and time.

Redact secret values; record only necessary names, provenance, or digests.

## Special evidence

Preserve:

- property/state-machine seed, minimized example, and regression artifact;
- fuzz corpus digest, crash input, minimized reproducer, budget, and tool version;
- concurrency schedule controls, timeouts, task/process trace, and start method;
- every flaky retry and its environment;
- snapshot/golden predecessor, successor, and approval disposition;
- mutation operator, surviving mutant, timeout, equivalent-mutant rationale, and tool failure separately;
- migration initial state, data volume, forward result, rollback result, and interruption point;
- sdist/wheel digest, tags, file lists, installed files, and clean environment;
- benchmark workload, warmup, samples, variance, baseline, interpreter, flags, and resource conditions;
- native crash symbols, extension digest, platform, and sanitizer/debugger output.

## Reuse

Reuse a prior pass only when the assertion, candidate, profile, interpreter, environment, lock, artifact, configuration, tool, fixture, and evidence semantics are unchanged. A source-only pass cannot be reused for an installed-wheel assertion.

## Dispositions

Keep `PASS`, `FAIL`, `BLOCKED`, `ERROR`, `INCONCLUSIVE`, `NOT_APPLICABLE`, and `SKIPPED_BY_POLICY` distinct. Retrying does not erase prior failures.

Return the assertion, subject, evidence identity, reproduction command, result, reuse decision, and residual gap.
## Alpha.4 projection evidence

Bind structure and slice evidence to the generic object ID, revision, canonical digest, Python projection digest, preflight digest, candidate digest, profile version, and BBK version. Planned-versus-actual comparison evidence must distinguish missing evidence, delegated private variation, advisory drift, and material fixed-decision divergence. A projection or comparison disposition never grants acceptance, readiness, verification, or release authority.
