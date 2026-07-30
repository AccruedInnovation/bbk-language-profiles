---
name: rust-implementation-structure
description: Project an accepted or proposed BBK ImplementationStructureContract into Rust workspace, crate, module, type, ownership, async, persistence, unsafe/FFI, test, package, and migration vocabulary without making the projection authoritative.
---

# Rust implementation structure

Use this skill when realization shape is material enough for `inline` or `contract` treatment.

## Procedure

1. Validate the generic `ImplementationStructureContract`; preserve its ID, revision, digest, fixed decisions, delegated freedom, and prohibited shortcuts.
2. Bind the exact Cargo workspace, crate graph, features, targets, generated artifacts, package surfaces, and repository commands.
3. Project generic artifacts into workspace, crate, module, feature, target, generated-artifact, test, migration, and package concepts.
4. Project shared contracts into public types, traits, functions, macros, wire schemas, persistence formats, package-consumer surfaces, and unsafe/FFI/ABI boundaries.
5. Make state and ownership explicit: mutability, borrowing/lifetime expectations, async task ownership, channels, locks, cancellation, shutdown, durable state, transactions, replay, and recovery.
6. Apply the type-depth test. Recommend a newtype, enum, trait, constructor, capability-bearing type, or typestate only when it prevents a material invalid combination, localizes an invariant, clarifies ownership, stabilizes a boundary, improves change locality, or creates a meaningful test seam.
7. Preserve runtime limits: compiler/type-checker success does not prove protocol behavior, cancellation, persistence, unsafe soundness, package usability, or operational recovery.
8. Return a deterministic profile projection. Do not rewrite the generic contract or expand its scope.

## Applicability

- `none`: ordinary private change whose shape is already constrained.
- `inline`: one local but meaningful type, state, or ownership choice can be carried in the work unit.
- `contract`: public/shared API, multi-crate topology, async ownership, persistence/migration, unsafe/FFI, package-consumer shape, or hard-to-reverse realization.

## Avoid

- speculative generics;
- one trait per concrete type;
- typestate that makes normal evolution or diagnostics worse;
- wrapper types that protect no invariant;
- freezing private helper layout that belongs inside delegated freedom.
