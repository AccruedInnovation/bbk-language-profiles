---
name: go-implementation-structure-review
description: Compare a Go implementation candidate with a BBK ImplementationStructureContract and ExecutionSlice, distinguishing fixed-decision divergence, advisory drift, delegated private differences, unknown evidence, and non-applicability.
---

# Go Implementation Structure Review

Review one exact candidate against one exact generic contract. Do not mutate the candidate, rewrite the contract, infer authority, or require exact private tree equality.

## Review order

1. Verify contract, candidate, actual-inventory, profile, preflight, and environment digests.
2. Confirm applicability: `none`, `inline`, or `contract`. Return `NOT_APPLICABLE` for `none`; do not manufacture profile obligations for unsupported subjects.
3. Compare fixed decisions first: package/source-of-truth ownership, public and wire contracts, state and goroutine ownership, effect boundaries, compatibility, migration, recovery, and explicitly fixed topology.
4. Compare public/shared Go shape: module and import paths, exported declarations, consumer interfaces, method sets, error identity, build-tag variants, generated artifacts, command and package boundaries, downstream consumers, and native ABI where applicable.
5. Compare state and lifecycle shape: mutation authority, zero/nil behavior, context cancellation, goroutine joining, channel close/backpressure, timer/process/resource cleanup, synchronization, partial effects, retry, shutdown, restart, and recovery.
6. Compare planned behavior paths, test seams, observability, migration touchpoints, and execution-slice evidence.
7. Treat private helper, file, package, algorithm, and test-utility differences inside delegated bounds as `within delegated freedom`. Report them only when independently poor.
8. Return `BLOCKED` rather than guessing when consequential fixed-decision evidence is absent, a required inventory/tool is unavailable, or the candidate identity is uncertain.

## Dispositions

- `CONFORMS` — fixed decisions and consequential shape conform; delegated differences are harmless.
- `ADVISORY_DIVERGENCE` — non-blocking drift or contract/implementation documentation should converge.
- `MATERIAL_DIVERGENCE` — a fixed decision, public/shared contract, owner, state model, effect boundary, behavior path, assertion, or slice is materially different.
- `BLOCKED` — evidence is insufficient or required tooling/inventory is unavailable.
- `NOT_APPLICABLE` — the generic contract does not govern the observed detail.

Every material finding must name the fixed decision, contract, ownership boundary, path, assertion, or slice affected and the smallest valid review or change route.
