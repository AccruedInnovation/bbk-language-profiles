---
name: tsjs-api-module-package-review
description: Review public TypeScript/JavaScript APIs, ESM/CommonJS behavior, conditional and subpath exports, declaration resolution, package contents, clean installation, actual consumers, and compatibility.
---

# TS/JS API, Module, and Package Review

Review the artifact consumers actually receive, not only source files in the workspace.

## Bind the package contract

Record:

- package manager and lockfile;
- package name, version, privacy and publication policy;
- `type`, `main`, `module`, `browser`, `types`, `typesVersions`, `exports`, `imports`, `bin`, `files`, and `sideEffects`;
- source and output extensions: `.ts`, `.mts`, `.cts`, `.js`, `.mjs`, `.cjs`, `.d.ts`, `.d.mts`, `.d.cts`;
- TypeScript `module` and `moduleResolution`;
- transpiler, bundler, declaration emitter, minifier, and source-map policy;
- supported runtimes, bundlers, TypeScript versions, conditions, and consumers;
- whether ESM, CommonJS, or dual publication is actually claimed.

## Public API review

Inspect:

- root and subpath exports;
- runtime values versus type-only exports;
- declaration paths and module format;
- accidental exports through barrels;
- deep imports previously used by consumers;
- default/named export interop;
- callable/constructable behavior;
- thrown/rejected error contracts;
- callback, event, and async behavior;
- public data/schema compatibility;
- side effects at import time;
- tree-shaking declarations and reality;
- browser/server split.

A change may be source-type compatible but runtime-breaking, or runtime-compatible while declaration-breaking. Report these separately.

## Resolution surfaces

Evaluate applicable combinations:

```text
TypeScript NodeNext or Node16 consumer
TypeScript bundler-mode consumer
Node ESM import
Node CommonJS require, only when claimed
plain JavaScript consumer
browser bundler consumer
Bun/Deno/Worker consumer, only when claimed
custom export conditions
OMP or other exact host loader
```

Check condition ordering and whether unsupported consumers receive an explicit failure rather than an accidentally wrong implementation.

## Packaged artifact

Inspect a clean pack/dry-run result or equivalent:

- included and excluded files;
- generated declarations and maps;
- README/licence/package metadata;
- executable bins, shebangs and modes;
- stale source-only paths;
- undeclared dependencies hidden by workspace hoisting;
- missing runtime assets, schemas, WASM/native files, CSS, or templates;
- source maps referencing unavailable or sensitive sources;
- package size and unexpected secrets;
- lifecycle scripts and build assumptions.

Then install the packed artifact into a clean consumer when the assurance contract requires it. Do not use the source workspace as the only consumer.

## Compatibility dimensions

Assess independently:

- TypeScript source and inference;
- runtime API and behavior;
- module resolution;
- package contents;
- exported conditions and subpaths;
- CLI behavior;
- wire/schema or persistence contracts;
- supported runtime versions;
- mixed-version or migration behavior.

SemVer tooling is supporting evidence, not the sole compatibility authority.

## Gate guidance

Typical material or consequential evidence includes:

```text
semantic type check
clean build
built entry-point load
clean declaration emit
pack dry run and archive inspection
clean consumer install
ESM consumer
CommonJS consumer if claimed
TypeScript consumer configurations
CLI execution if applicable
browser/host load if applicable
```

Do not require dual-package testing when the package does not claim dual support.

## Output

Return exact package subject and digest, consumers tested, conditions exercised, declarations inspected, files included, compatibility dimensions, failures, and residual gaps. Distinguish packaging failure, resolver mismatch, declaration defect, runtime defect, unsupported consumer, and test-infrastructure failure.

## Implementation-structure projection

For alpha.4 contracts, treat package manifests, public entry points, conditional exports, declarations, runtime exports, browser/server splits, generated clients, and clean consumer fixtures as consequential artifact and contract topology. Compare planned and actual consumer shape, not merely source imports. A private module move is not material unless it changes ownership, public resolution, declarations, effects, behavior, or a fixed decision.
