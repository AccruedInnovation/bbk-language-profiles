# BBK TypeScript/JavaScript Profile

`bbk-profile-typescript-javascript` is an optional language profile for the **Blueprint Bootstrap Kit (BBK)**. It composes TS/JS-specific repository preflight, worker guidance, focused review packs, deterministic selection, and proportional gate recipes with an existing BBK role, task profile, work-unit scope, and assurance contract.

```text
BBK role constitution
+ task-kind profile
+ bbk-profile-typescript-javascript resolution
+ exact work unit and assurance contract
= effective TS/JS worker or validator invocation
```

This is a temporary development-method package. It is not the real Blueprint TypeScript adapter, AgentSpec compiler, Host Protocol, release authority, readiness authority, semantic store, or OMP qualification record.

## Version identities

The profile package version is `0.1.0-alpha.3` and the minimum compatible BBK core is `0.1.0-alpha.8`. Legacy projection fields containing `"bbk_version": "0.1.0-alpha.4"` identify the implementation-structure/execution-slice **contract dialect introduced in BBK alpha.4**; they do not report the installed core version. See `docs/METADATA-CONTRACT.md`.

## Release

- Profile ID: `typescript-javascript`
- Package: `bbk-profile-typescript-javascript`
- Version: `0.1.0-alpha.3`
- Maturity: `comprehensive-alpha`
- Required BBK core: `0.1.0-alpha.8` or a compatible successor
- CLI: `bbk-tsjs`

## Included skills

- `bbk-tsjs` — compact routing and assurance entry point;
- `tsjs-development-practices` — worker-oriented implementation reference;
- `comprehensive-analysis-tsjs` — updated broad architecture and codebase survey;
- `tsjs-implementation-structure-review` — focused planned/actual structure and execution-slice review;
- `tsjs-type-contract-review`;
- `tsjs-runtime-data-contract-review`;
- `tsjs-api-module-package-review`;
- `tsjs-async-resource-failure-review`;
- `tsjs-test-strategy-review`;
- `tsjs-security-supply-chain-review`;
- `tsjs-operational-release-review`;
- `tsjs-browser-ui-review`;
- `tsjs-evidence-reproducer`.

The broad survey does not automatically fan out into every focused review. Selection is driven by exact task, role, change class, scope, runtime, language mode, package surface, and assurance tier.

## Deterministic capabilities

The profile provides:

- package/workspace discovery;
- TypeScript, checked-JavaScript, transpile-only, unchecked-JavaScript, and mixed-mode detection;
- runtime and package-kind detection;
- package manager and lockfile discovery;
- tsconfig/jsconfig inheritance and strictness observations;
- TypeScript/checker, transpiler, bundler, declaration, lint and test-tool observations;
- ESM/CommonJS, exports, declarations and consumer-surface observations;
- static scope scanning and trigger resolution;
- proportional non-executing gate plans;
- content-addressed profile locks;
- Codex, OMP, Claude Code and generic skill installation;
- deterministic `ImplementationStructureContract` and `ExecutionSlice` projections;
- planned-versus-actual structure comparison that preserves delegated private freedom;
- an optional OMP extension exposing preflight, resolution, gate planning, structure, slice, and structure-review entrypoints.


## Alpha.4 implementation-structure capability

```text
Architecture and interfaces
  → generic ImplementationStructureContract when applicable
    → TypeScript/JavaScript projection
      → Execution Slices
        → Work Units
          → exact Candidate / Validation Cohort
```

The generic BBK objects remain authoritative. The profile projects package, module, export-map, declaration, runtime-schema, state/effect, async-resource, consumer, browser/host, test, and generated-artifact concerns. It reviews fixed consequential shape while treating equivalent private helper layout as delegated freedom.

```bash
bbk-tsjs structure --root . --contract .bbk/structure/contract.json
bbk-tsjs slice --root . --slice .bbk/slices/slice-1.json
bbk-tsjs structure-review --root . --contract .bbk/structure/contract.json --candidate .bbk/candidates/C-1/manifest.json --actual-inventory actual.json
```

## Core rules

1. Repository-declared runtime, package manager, lockfile, commands, toolchain, consumers and conventions take precedence.
2. Type checking, transformation, bundling, declaration emit, runtime execution and packed-consumer behavior are separate evidence classes.
3. Type annotations do not validate runtime values.
4. Workers normally receive procedure; validators receive exact focused assertion packs.
5. Required unavailable checks produce `BLOCKED`; optional unavailable checks are advisory.
6. The profile never installs dependencies, runs package lifecycle scripts, changes lockfiles, or grants effects merely because it is selected.
7. A passing language or package gate does not establish BBK or Blueprint completion.

## Quick start

Install BBK core `0.1.0-alpha.8` or a compatible successor, then:

```bash
python3 tools/install.py install --scope user --omp
bbk profile list
bbk profile inspect --id typescript-javascript
```

Resolve a routine Node TypeScript worker:

```bash
bbk profile resolve \
  --id typescript-javascript \
  --role worker \
  --task-profile implementation \
  --assurance-tier routine \
  --path src/index.ts \
  --write-lock
```

Resolve a consequential package validator:

```bash
bbk profile resolve \
  --id typescript-javascript \
  --role validator \
  --task-profile interface-schema-migration \
  --assurance-tier consequential \
  --change-class interface \
  --change-class packaging \
  --hint public-api \
  --path package.json \
  --path src/index.ts
```

See [Installation](docs/INSTALL.md), [Usage](docs/USAGE.md), [Boundaries](docs/BOUNDARIES.md), and [Qualification](docs/QUALIFICATION.md).

## Alpha.8 typed profile capability

This `0.1.0-alpha.3` package adds six read-only `bbk.profile-capability.v1` operations through `tools/profile.py`. It requires BBK `0.1.0-alpha.8` and preserves all alpha.2 skills and direct usage.
