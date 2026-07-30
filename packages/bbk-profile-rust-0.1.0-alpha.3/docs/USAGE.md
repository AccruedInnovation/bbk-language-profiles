# Using the BBK Rust profile

## 1. Preflight

Static preflight reads Cargo manifests, workspace membership, declared toolchain, lockfile policy, Cargo configuration, repository recipes, feature names, crate kinds, support signals, and relevant environment-variable digests.

```bash
bbk-rust preflight --root .
```

`--run-tools` permits bounded, read-only version and offline metadata interrogation. It does not build, test, fetch, install, or update.

## 2. Ordinary resolution

```bash
bbk-rust resolve \
  --root . \
  --role worker \
  --task-profile implementation \
  --assurance-tier routine \
  --path crates/parser/src/token.rs
```

Routine source work does not select a standalone structure reviewer merely because it is Rust.

## 3. Resolve with generic alpha.4 objects

Resolution may consume a generic contract or slice and carry their exact digests into the effective profile lock:

```bash
bbk-rust resolve \
  --root . \
  --role reviewer \
  --task-profile implementation-structure \
  --assurance-tier consequential \
  --structure-contract implementation-structure.json \
  --path crates/protocol/src/lib.rs
```

```bash
bbk-rust resolve \
  --root . \
  --role planning-wayfinder \
  --task-profile execution-slicing \
  --assurance-tier material \
  --execution-slice execution-slice.json
```

The resolver selects only applicable components. A broad survey does not automatically fan out every focused reviewer.

## 4. Structure projection

```bash
bbk-rust structure \
  --root . \
  --contract implementation-structure.json \
  --role architect \
  --task-profile implementation-structure \
  --assurance-tier consequential
```

The JSON projection includes:

- profile, BBK, generic object identity, revision, and digest;
- bounded preflight digest;
- workspace/crate/module/feature/target/test topology;
- public and shared contracts;
- ownership, async lifecycle, errors, persistence, unsafe/FFI, and test seams where applicable;
- unsupported or uncertain areas, advisories, blockers, and no-authority boundary;
- deterministic output digest.

## 5. Execution-slice projection

```bash
bbk-rust slice \
  --root . \
  --slice execution-slice.json \
  --role phase-wayfinder \
  --task-profile execution-slicing \
  --assurance-tier material
```

The projection identifies the Rust dependency closure, useful touchpoint, likely candidate and validation boundary, scaffolding risks, and whether a foundation exception is justified. It does not invent work absent from the generic slice.

## 6. Planned-versus-actual structure review

```bash
bbk-rust structure-review \
  --root . \
  --contract implementation-structure.json \
  --candidate candidate-manifest.json \
  --actual-inventory actual-rust-inventory.json \
  --assurance-tier consequential
```

Possible dispositions are:

```text
CONFORMS
ADVISORY_DIVERGENCE
MATERIAL_DIVERGENCE
BLOCKED
NOT_APPLICABLE
```

Material findings identify the affected fixed decision, public/shared contract, state or ownership boundary, behavior path, assertion, or slice. Private differences inside delegated freedom do not become material failures.

## 7. Gate planning

```bash
bbk-rust gate-plan --root . --assurance-tier material --path crates/core/src/lib.rs
```

Alpha.4 adds planned recipes for generic-contract validation, Rust projection validation, public/shared-contract and ownership drift, planned/actual comparison, slice touchpoint evidence, and temporary-scaffolding disposition. Selection does not execute a gate.

## 8. OMP commands

```text
/bbk:rust
/bbk:rust:preflight
/bbk:rust:gates
/bbk:rust:structure
/bbk:rust:slice
/bbk:rust:structure-review
```

The OMP extension invokes the installed deterministic CLI. It does not grant project mutation or execute planned Rust gates merely because a command is selected.
