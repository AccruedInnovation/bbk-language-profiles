# Rust alpha.4 structure design note

## 1. Meaningful type concepts

Rust structure projections distinguish identity newtypes, closed state/result enums, public and wire boundary types, ownership/lifetime and mutability boundaries, async task/channel/cancellation ownership, error/recovery classifications, and evidence dispositions. A type is recommended only when it blocks a material invalid combination, localizes an invariant, makes ownership clear, stabilizes a boundary, improves change locality, creates a useful seam, or hides consequential complexity.

## 2. Inline versus contract treatment

`inline` is appropriate for a bounded private change whose module ownership and external contracts remain stable. `contract` is normally selected for public/shared APIs, wire schemas, cross-crate ownership, async lifecycle, persistence/migration, unsafe/FFI/ABI, package-consumer shape, or difficult-to-reverse topology. Routine refactors remain `none` unless the generic object explicitly says otherwise.

## 3. Touchpoint vocabulary

Useful Rust touchpoints include a callable API, CLI path, protocol exchange, component/integration/consumer test, package built and consumed from its artifact, migration rehearsal, recovery trace, and measured benchmark tied to an explicit performance assertion.

## 4. Material planned/actual differences

Material differences alter a fixed public/shared type or trait, ownership/lifetime or async-task owner, wire/persistence schema, unsafe/ABI representation, effect boundary, migration contract, package consumer shape, or required slice touchpoint. Private module moves, helper names, local types, and file organization remain within delegated freedom unless deliberately fixed.

## 5. Evidence-method classification

- Deterministic: schema validation, manifest and lock digests, static projection, inventory comparison, selected repository checks.
- Agent-reviewed: responsibility depth, interface quality, abstraction usefulness, failure-path completeness.
- Tool-authoritative: rustc/Cargo, repository test tools, Miri/Loom/fuzz/sanitizers/compatibility tools within their qualified claims.
- Runtime/operational: protocol, persistence, cancellation, package consumer, deployment, and performance behavior.
- Human-reviewed: architecture trade-offs, public compatibility acceptance, residual risk, unsafe safety argument where needed.

## 6. Unsupported or unqualified areas

The profile does not establish universal support for `no_std`, embedded, kernel, GPU, specialized WASM, every nightly/tool plugin, every cross-target linker, or every production environment. It cannot turn compiler success into proof of runtime protocol, persistence, unsafe, or operational correctness.
