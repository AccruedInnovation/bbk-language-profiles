---
name: rust-package-release-gates
description: Verify clean Rust crate or binary packaging, package contents, install/startup/shutdown behavior, compatibility, provenance, diagnostics, rollback, and removal without treating workspace tests as release evidence.
---

# Rust Package and Release Gates

Use for publishable crates, shipped binaries, installers, archives, containers, native libraries, or release-profile changes.

## Crate package gate

Where publication is in scope:

1. inspect `cargo package --list` and declared include/exclude behavior;
2. run `cargo package --locked` under the qualified toolchain;
3. inspect the produced archive, metadata, licence, README, schemas, examples, and generated files;
4. build and test from the clean packaged source rather than the mutable workspace;
5. verify feature declarations, Cargo.lock policy, build-script behavior, and expected native inputs;
6. bind the package digest to the BBK candidate, source revision, toolchain, lockfile, and environment.

Do not publish unless separately authorized.

## Binary and service gate

Exercise the actual release artifact:

- version and provenance output;
- startup, readiness, normal shutdown, signal/cancellation, and crash diagnostics;
- missing, invalid, stale, and conflicting configuration;
- native/dynamic dependency discovery;
- filesystem permissions and path behavior;
- migration, downgrade, rollback, and mixed-version behavior where claimed;
- install, side-by-side coexistence, upgrade, uninstall, and cleanup;
- symbols/debug information and panic policy consistent with incident-response needs.

## Profile decisions

Do not bundle `opt-level`, LTO, codegen units, panic abort, stripping, or native CPU targeting as automatic production defaults. Each setting requires an explicit objective and measured operational consequences.

## Result

Return separate dispositions for package contents, clean build/test, runtime behavior, migration/rollback, provenance, and cleanup. A workspace test pass does not substitute for a clean package or installed-artifact gate.
