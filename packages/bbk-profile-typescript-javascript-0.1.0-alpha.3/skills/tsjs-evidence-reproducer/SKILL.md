---
name: tsjs-evidence-reproducer
description: Capture reproducible TypeScript/JavaScript preflight, type, build, test, package, browser, fuzz, performance, and failure evidence with exact subject and environment identity.
---

# TS/JS Evidence and Reproducer

Evidence proves one declared assertion against one exact subject.

## Required identity

Capture as applicable:

```text
candidate digest
BBK effective profile digest
repository revision and dirty state
package/workspace selection
runtime and version
TypeScript CLI/compiler API/language-service versions
package manager and lockfile digest
transpiler, bundler, declaration emitter, linter and test runner
module and resolution modes
runtime/export conditions
browser/OS/architecture
environment and configuration digests
command and working directory
artifact or tarball digest
assertion and fixture version
```

Redact secrets; record their presence and binding identity without values.

## Evidence classes

Keep separate:

- semantic type-check receipt;
- lint/format receipt;
- transformation/build receipt;
- declaration receipt;
- built-artifact load receipt;
- test receipt;
- packed-artifact/consumer receipt;
- browser/host receipt;
- security/fault receipt;
- performance or resource receipt.

Do not reuse one class as another.

## Nondeterministic evidence

Preserve:

- every retry and disposition;
- random seed and minimized failing input;
- fuzz corpus/crash digest and budget;
- property counterexample;
- browser trace, screenshot or network log where authorized;
- async/fault injection point and durable state;
- benchmark workload, samples, variance, baseline and machine state;
- mutation inventory and surviving-case disposition;
- test infrastructure failures separately from candidate failures.

Use fresh-run semantic receipts for nondeterministic output; do not demand byte equality unless bytes are part of the claim.

## Reuse

Reuse a prior pass only when the complete dependency closure remains unchanged: candidate, profile, toolchain, package graph, lockfile, conditions, environment, fixture, assertion and evidence method. Explain the reuse decision.

## Return

Provide assertion, subject, environment, command, result, evidence references, reuse status, limitations, and exact reproduction steps. `SKIPPED`, `BLOCKED`, `ERROR`, `INCONCLUSIVE`, and `PASS` remain distinct.

## Structure and slice evidence

Also capture:

```text
generic structure-contract/slice digest
TS/JS projection digest
planned-versus-actual inventory digest
fixed-decision and delegated-freedom references
exact package/export/declaration/runtime-schema observations
slice touchpoint and integration owner
scaffolding disposition
candidate/validation-cohort identity
```

A source-tree inventory may establish path presence but not semantic conformance. Public declarations require declaration/consumer evidence; runtime schemas require representative runtime evidence; async/resource ownership may require fault/cancellation evidence; host extensions require exact-host loading.
