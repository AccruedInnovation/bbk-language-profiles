# BBK Rust profile boundaries

## Authority and source of truth

The generic BBK `ImplementationStructureContract` and `ExecutionSlice` remain authoritative BBK planning objects. Rust projections are deterministic views over those objects. Markdown, resolver output, OMP rendering, inventories, and reviewer prose are not independent authority.

The profile may inspect bounded repository facts, select procedure, project generic concepts into Rust vocabulary, plan gates, produce locks, and report divergence. It may not:

- grant tools, filesystem scope, network access, credentials, publication, deployment, migration, or destructive effects;
- install or update Rust, Cargo components, nightlies, Cargo subcommands, or dependencies;
- override repository-owned commands, MSRV, feature, target, packaging, or release policy silently;
- broaden a work unit or reduce an assurance contract;
- declare candidate acceptance, close a finding, accept risk, or authorize release;
- treat compiler success as proof of protocol, persistence, unsafe, operational, or outcome correctness;
- fail harmless private implementation differences that lie within explicit delegated freedom.

## Structure applicability

The profile supports three generic applicability levels:

- `none`: ordinary alpha.1 profile behavior; no projection or focused structure review;
- `inline`: compact Rust structure guidance may travel with the work unit;
- `contract`: deterministic projection and applicable structure review are required.

A standalone contract is normally material for public/shared APIs, wire schemas, ownership or async-lifecycle changes, persistence or migration, unsafe/FFI/ABI, multi-crate topology, package-consumer shape, or hard-to-reverse realization decisions. Routine private refactors remain minimal.

## Worker and reviewer boundary

Workers implement fixed decisions while retaining explicitly delegated freedom. They do not automatically receive the focused reviewer prompt that will later judge the candidate.

A structure reviewer compares consequential shape and fixed decisions. It classifies differences as conforming, advisory, material, blocked, or not applicable. Exact private file trees, helper names, and file counts are not conformance criteria unless the generic contract deliberately fixes them.

## Toolchain boundary

Repository configuration wins over generic recipes. Adding a dependency, nightly, tool, lint level, target, feature combination, release profile, or CI step is a project decision and effect. Required unavailable tooling produces `BLOCKED`; optional tooling remains advisory.

## Maturity boundary

`comprehensive-alpha` means broad procedure, resolver, structure-projection, and fixture coverage. It does not mean every Rust target, runtime, dependency ecosystem, or production environment has been live-qualified. See `docs/SUPPORT-MATRIX.md`.
