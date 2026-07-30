# Using the BBK TypeScript/JavaScript profile

## 1. Preflight

```bash
bbk-tsjs preflight --root .
```

Static preflight reads package/workspace manifests, lockfiles, package manager declaration, scripts, tsconfig/jsconfig chains, source modes, runtime signals, exports, declarations, lifecycle scripts, build/test tooling and relevant configuration digests.

Use installed version commands only when bounded read-only tool execution is permitted:

```bash
bbk-tsjs preflight --root . --run-tools
```

`--run-tools` invokes version reporting only. It does not install, fetch, type-check, build, test, package or run lifecycle scripts.

## 2. Resolve an effective profile

Routine implementation:

```bash
bbk-tsjs resolve \
  --root . \
  --role worker \
  --task-profile implementation \
  --assurance-tier routine \
  --path src/index.ts
```

Runtime schema change:

```bash
bbk-tsjs resolve \
  --root . \
  --role validator \
  --task-profile interface-schema-migration \
  --assurance-tier consequential \
  --change-class schema \
  --hint runtime-validation \
  --path src/api/schema.ts
```

Public package change:

```bash
bbk-tsjs resolve \
  --root . \
  --role validator \
  --task-profile packaging-release \
  --assurance-tier consequential \
  --hint public-api \
  --hint package \
  --path package.json \
  --path src/index.ts
```

Broad inherited-codebase survey:

```bash
bbk-tsjs resolve \
  --root . \
  --role reviewer \
  --task-profile investigation-prototype \
  --assurance-tier material \
  --hint broad-analysis
```

The broad resolution selects only `bbk-tsjs` and `comprehensive-analysis-tsjs`; it does not automatically load every focused pack.

## 3. Resolve through BBK core

```bash
bbk profile resolve \
  --id typescript-javascript \
  --role worker \
  --task-profile implementation \
  --assurance-tier material \
  --path src/index.ts \
  --write-lock
```

BBK stores the resolver-provided lock in `.bbk/profile-lock.json`. A profile update may leave candidate bytes unchanged while invalidating profile-dependent evidence.

## 4. Gate planning

```bash
bbk-tsjs gate-plan --root . --assurance-tier material --path src/index.ts
```

The plan prefers repository scripts. It does not run them.

Typical progression:

| Tier | Normal plan |
|---|---|
| Routine | configured formatting/lint, semantic check for checked code, focused tests |
| Material | routine plus actual build, emitted-artifact load, applicable declarations, integration and generated checks |
| Consequential | material plus frozen install, packed consumers, module/runtime matrix, runtime contracts, fault/security/browser/host evidence as triggered |
| Critical | consequential plus complementary methods and independently owned assertions |

## 5. Evidence classes

Keep these distinct:

```text
type check
transformation/build
bundling
declaration emit
runtime execution
packed consumer
browser/host compatibility
```

A pass in one class does not establish the others.

## 6. Implementation structure

```bash
bbk-tsjs structure --root . --contract contract.json
```

The output maps generic artifacts, contracts, paths, ownership, failures, effects, seams, fixed decisions and delegated freedom into TS/JS vocabulary. It does not mutate or accept the contract.

## 7. Execution slicing

```bash
bbk-tsjs slice --root . --slice slice.json
```

The output identifies the touchpoint evidence, dependency closure, integration owner, candidate/validation boundary, sequencing risk and scaffolding disposition.

## 8. Planned-versus-actual review

```bash
bbk-tsjs structure-review \
  --root . \
  --contract contract.json \
  --candidate candidate-manifest.json \
  --actual-inventory actual-inventory.json
```

The optional explicit inventory supplies tool- or reviewer-backed observations for public contracts, fixed decisions, state owners and effect owners. Without it, path and package observations may be available while consequential semantic assertions remain `BLOCKED` rather than guessed.

Resolver integration:

```bash
bbk-tsjs resolve --root . --role reviewer \
  --structure-contract contract.json \
  --execution-slice slice.json \
  --assurance-tier consequential
```

The effective lock includes generic object and projection digests.
