# Testing and evidence policy

## Evidence classes remain separate

- type-check and type-fixture evidence;
- lint/format evidence;
- transformation/build evidence;
- declaration evidence;
- runtime component/integration evidence;
- built-artifact evidence;
- package-consumer evidence;
- browser/host evidence;
- fault/security evidence;
- performance/resource evidence.

No one class substitutes for all others.

## Reuse fingerprint

Evidence reuse requires unchanged:

```text
candidate
profile lock
toolchain and package manager
lockfile and dependencies
package/target/runtime/module condition
configuration and environment
fixture and assertion semantics
evidence method
```

## Nondeterministic methods

Preserve seeds, minimized failures, corpora, traces, all retry attempts, browser/runtime identity, benchmark samples and variance. Use semantic receipts rather than byte equality when output is nondeterministic.

## Proportional selection

- Routine: cheap focused checks.
- Material: real build and applicable integration/artifact checks.
- Consequential: clean installation, package consumers, compatibility and triggered fault/security methods.
- Critical: complementary methods and independent assertion ownership.

Coverage percentage is diagnostic, not an automatic quality verdict.
