---
name: rust-implementation-structure-review
description: Compare a Rust candidate and actual inventory with a generic ImplementationStructureContract, distinguishing fixed public/ownership decisions from harmless private differences.
---

# Rust implementation-structure review

Review one exact candidate against one exact contract.

## Evaluate

- workspace/crate/module responsibility and dependency direction;
- public types, traits, functions, macros, feature gates, wire schemas, and package-consumer shape;
- state, mutability, lifetime, task, channel, lock, cancellation, and shutdown ownership;
- error/failure/retry/recovery contracts;
- persistence, migration, transaction, replay, and idempotency boundaries;
- unsafe, FFI, ABI, layout, allocator, panic, and unwinding boundaries;
- test seams, observability, migration touchpoints, and early slice feedback.

## Classification

- **CONFORMS** — fixed decisions and consequential shape are represented.
- **ADVISORY_DIVERGENCE** — implementation differs within delegated freedom or the contract should be refreshed at the next safe point.
- **MATERIAL_DIVERGENCE** — a fixed public contract, state owner, effect boundary, behavior path, migration, unsafe boundary, assertion, or slice changed.
- **BLOCKED** — candidate or actual inventory is insufficient or stale.
- **NOT_APPLICABLE** — the generic contract explicitly says `none`.

Do not require exact private module trees, helper names, local variable choices, or incidental refactors. A material finding must cite the exact fixed decision, contract, owner, behavior path, assertion, or slice it affects.
