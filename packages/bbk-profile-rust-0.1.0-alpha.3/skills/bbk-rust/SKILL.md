---
name: bbk-rust
description: Route Rust work through deterministic project preflight, applicability-aware rule selection, proportional Cargo gates, focused review packs, and a BBK-compatible handoff. Use for Rust implementation, planning, review, validation, testing, packaging, or investigation.
---

# BBK Rust

Apply the Rust profile as procedure and evidence guidance. It never expands the work unit, grants tools or effects, lowers assurance, or declares a candidate passed.

## 1. Bind the project before giving Rust advice

Establish:

- Cargo workspace root, members, and default members;
- crate kinds, editions, declared `rust-version`, and toolchain pin;
- lockfile policy, dependency sources, `.cargo` configuration, and relevant environment inputs;
- target triples, supported feature configurations, and `std`/`no_std` posture;
- repository-owned format, lint, build, test, package, benchmark, fuzz, and release commands;
- changed packages, paths, interfaces, schemas, native dependencies, and generated artifacts.

Use `bbk-rust preflight` or `bbk profile resolve --id rust`. Do not assume that a bare `cargo check` covers the intended workspace, target, feature set, linker, or final code generation.

## 2. Resolve only applicable guidance

Compose:

```text
BBK role constitution
+ task-kind profile
+ Rust profile resolution
+ exact work unit and assurance contract
= effective agent instruction
```

Load `rust-skills` as a reference index, then use `rules-index.json` to select relevant rules. Correctness, soundness, ownership, error, API, and boundary guidance may be broadly useful; memory, performance, alternate crates, nightly features, feature matrices, Miri, fuzzing, Loom, mutation testing, and release tuning are triggered techniques.

Do not turn the 265-rule corpus into one checklist. A rule produces a finding only when it applies and the code demonstrates a consequential mismatch.

## 3. Prefer repository authority

- Use repository-declared commands and dependencies first.
- Treat `thiserror`, `anyhow`, Tokio, tracing, proptest, Loom, Criterion, and similar crates as options or established conventions, not mandatory additions.
- Never run `cargo install`, `rustup toolchain install`, dependency updates, registry publication, networked services, or credential-bearing commands without the work unit's effect authority.
- If a required tool is absent, return `BLOCKED`. If a recommended tool is absent, record an advisory.

The selected mutation-testing tool is **mutest-rs**, invoked through `cargo mutest run` after a project-qualified revision and nightly are available. Do not substitute another mutation framework silently.

## 4. Compile proportional gates

Routine work normally receives formatting, focused tests, an affected-package check, and repository-configured Clippy. Material work adds a real build and applicable integration, docs/example, generated-artifact, feature, or target checks. Consequential work may add release behavior, MSRV, public/wire/persistence compatibility, clean packaging, or triggered Miri, Loom, fuzzing, `mutest-rs`, sanitizer, or fault evidence.

Run cheap checks before expensive methods. Do not repeat a full workspace suite at worker, validator, integration, and release layers against the same candidate unless each run establishes a distinct assertion.

## 5. Separate worker and validator use

A worker receives this router, selected implementation rules, exact scope, repository commands, and handoff requirements. It normally does not receive the focused validator prompt that will later judge it.

A validator receives one exact candidate, assertion IDs, current deterministic receipts, one focused review pack, and read-only subject access. Additional validators are justified only for disjoint assertions or complementary methods.

`comprehensive-analysis-rust` is a broad survey. Use it for inherited-codebase assessment, architectural modernization, or hotspot discovery; do not automatically follow it with every focused review pack.

## 6. Preserve evidence

Record candidate and effective-profile digests, compiler/Cargo/target/configuration identity, exact commands, attempts, seeds, minimized failures, corpora, schedules, snapshots, mutants, benchmarks, and unavailable-tool dispositions. A retry does not erase a prior failure or flake.

Return the BBK result envelope: exact subject; selected Rust profile components and reasons; commands and evidence; changed artifacts; findings or disposition; coverage gaps; residual uncertainty; blockers; and the smallest valid next action.

## 7. Alpha.4 structure and slicing

When a work unit references an `ImplementationStructureContract` or `ExecutionSlice`, preserve the generic object identity and digest. Use `bbk-rust structure`, `bbk-rust slice`, and the focused `rust-implementation-structure-review` only when applicability and role require them. Routine private work must not gain a standalone structure reviewer. A profile projection is advisory procedure over the generic object, never a second authority.
