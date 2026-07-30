# BBK Rust Profile

`bbk-profile-rust` is an optional, independently versioned language profile for the **Blueprint Bootstrap Kit (BBK)**. It composes Rust-specific procedure, type- and ownership-aware implementation-structure projection, execution-slice guidance, focused review packs, deterministic preflight, and proportional gate recipes with a generic BBK role, task profile, work-unit scope, and assurance contract.

```text
BBK role constitution
+ task-kind profile
+ generic ImplementationStructureContract / ExecutionSlice, when applicable
+ bbk-profile-rust projection
+ exact work unit and assurance contract
= effective Rust worker or validator invocation
```

The generic BBK contract or slice remains the source object. A Rust projection is a deterministic, non-authoritative view that makes its meaning concrete in Rust vocabulary. It cannot broaden scope, grant tools or effects, lower assurance, declare a pass, or replace candidate-bound evidence.

## Version identities

The profile package version is `0.1.0-alpha.3` and the minimum compatible BBK core is `0.1.0-alpha.8`. Legacy projection fields containing `"bbk_version": "0.1.0-alpha.4"` identify the implementation-structure/execution-slice **contract dialect introduced in BBK alpha.4**; they do not report the installed core version. See `docs/METADATA-CONTRACT.md`.

## Release

- Profile ID: `rust`
- Package: `bbk-profile-rust`
- Version: `0.1.0-alpha.3`
- Maturity: `comprehensive-alpha`
- Required BBK core: `0.1.0-alpha.8` or a compatible successor
- Alpha.4 capability: `ImplementationStructureContract` and `ExecutionSlice` **supported**
- Prior release: `0.1.0-alpha.2`, retained as the immutable predecessor represented by the source-lineage records

Primary support includes ordinary `std` libraries, binaries, CLIs, Cargo workspaces, async services, public crates, persistence and migration work, and packaged Rust artifacts. Unsafe/FFI, proc macros, cross-target work, and WASM are conditional. `no_std`, embedded, kernel, GPU, and specialized WASM environments remain partial or unqualified.

## Included capabilities

- compact `bbk-rust` routing skill;
- 265-rule applicability-aware Rust reference corpus;
- broad architecture/codebase survey and focused API, correctness, testing, operations, security, unsafe/FFI, packaging, and evidence packs;
- Rust implementation-structure planning, execution slicing, and focused planned-versus-actual review;
- deterministic static workspace/toolchain preflight;
- changed-scope and materiality routing;
- proportional gate planning;
- profile locks carrying generic contract/slice and projection digests;
- Codex, OMP, Claude Code, and generic skill installation;
- optional OMP tools and commands for preflight, resolution, structure, slicing, and structure review.

## Type-driven development

The profile treats “type” as a practical boundary and invariant mechanism, not a goal by itself. It favors:

- newtypes for materially distinct identities or units;
- enums for closed states and outcomes;
- explicit error and recovery classifications;
- ownership and lifetime boundaries where they prevent ambiguity;
- task, cancellation, channel, lock, and shutdown ownership for async work;
- narrow traits at real substitution or test seams;
- runtime validation where compiler types cannot establish protocol, persistence, FFI, or environmental truth.

It warns against speculative generic abstraction, a trait for every concrete type, universal typestate, and wrappers that protect no meaningful invariant.

## Mutation testing

The selected mutation-testing integration is **`mutest-rs`**, normally invoked through a repository-qualified `cargo mutest run` command. It is selected only for high-value logic, an identified test-strategy gap, or an explicit assurance obligation. The profile does not install it, fetch a nightly, alter dependencies, or silently substitute another mutation framework.

## Quick start

Install BBK core `0.1.0-alpha.8` or a compatible successor first, then this profile:

```bash
python3 tools/install.py install --scope user --omp
bbk profile list
bbk profile inspect --id rust
```

Routine resolution remains minimal:

```bash
bbk-rust resolve \
  --root . \
  --role worker \
  --task-profile implementation \
  --assurance-tier routine \
  --path crates/core/src/lib.rs
```

Project a generic structure contract:

```bash
bbk-rust structure \
  --root . \
  --contract implementation-structure.json \
  --role architect \
  --task-profile implementation-structure \
  --assurance-tier consequential
```

Project an execution slice:

```bash
bbk-rust slice \
  --root . \
  --slice execution-slice.json \
  --role planning-wayfinder \
  --task-profile execution-slicing \
  --assurance-tier material
```

Compare a frozen candidate with fixed structure decisions while preserving delegated private freedom:

```bash
bbk-rust structure-review \
  --root . \
  --contract implementation-structure.json \
  --candidate candidate-manifest.json \
  --actual-inventory actual-rust-inventory.json \
  --assurance-tier consequential
```

See [Installation](docs/INSTALL.md), [Usage](docs/USAGE.md), [Boundaries](docs/BOUNDARIES.md), [Support matrix](docs/SUPPORT-MATRIX.md), [Design note](docs/DESIGN-NOTE.md), and [Qualification](docs/QUALIFICATION.md).

## Alpha.8 typed profile capability

This `0.1.0-alpha.3` package adds six read-only `bbk.profile-capability.v1` operations through `tools/profile.py`. It requires BBK `0.1.0-alpha.8` and preserves all alpha.2 skills and direct usage.
