# BBK Go Profile

`bbk-profile-go` is an optional, independently versioned Go language profile for the Blueprint Bootstrap Kit. Version `0.1.0-alpha.2` targets BBK `0.1.0-alpha.4` and adds qualified projections for `ImplementationStructureContract` and `ExecutionSlice` while preserving alpha.1 preflight, resolution, gate planning, installer, and review behavior.

The generic BBK contract or slice remains authoritative. The Go projection is a deterministic, non-mutating view. It cannot grant tools, effects, scope, approval, readiness, validation, completion, or release authority.

## Main capabilities

- static and optionally tool-assisted Go module/workspace preflight;
- applicability-aware worker and focused reviewer routing;
- proportional Go gate planning;
- Go structure projection for modules, packages, commands, exported declarations, errors, generated artifacts, build variants, state/lifecycle ownership, native boundaries, and release subjects;
- execution-slice projection with Go touchpoints, dependency closure, assertion evidence, candidate/validation boundaries, foundation assessment, and scaffolding disposition;
- candidate-bound planned/actual structure comparison that tolerates delegated private differences;
- deterministic package installation, removal, building, verification, and qualification fixtures;
- optional OMP commands and tools.

## Commands

```bash
bbk-go preflight --root <repo>
bbk-go resolve --root <repo> --role worker --task-profile implementation --assurance-tier routine
bbk-go gate-plan --root <repo> --assurance-tier material

bbk-go structure --root <repo> --contract <ImplementationStructureContract.json>
bbk-go slice --root <repo> --slice <ExecutionSlice.json>
bbk-go inventory --root <repo>
bbk-go structure-review --root <repo> --contract <contract.json> --candidate <candidate.json> [--actual-inventory <inventory.json>]
```

`--run-tools` is opt-in and uses bounded, offline read-only tool interrogation. Resolution never installs tools and never runs planned project gates.

## Package layout

```text
PROFILE.json
skills/
references/
mappings/
gates/
schemas/
fixtures/
templates/
omp/extension/
tools/
tests/
sources/
```

See `docs/USAGE.md`, `docs/BOUNDARIES.md`, `docs/DESIGN-NOTE.md`, `docs/SUPPORT-MATRIX.md`, `docs/KNOWN-LIMITATIONS.md`, `docs/ALPHA4-FIXTURE-MATRIX.md`, and `docs/QUALIFICATION.md`.

## Alpha.8 typed profile capability

This `0.1.0-alpha.3` package adds six read-only `bbk.profile-capability.v1` operations through `tools/profile.py`. It requires BBK `0.1.0-alpha.8` and preserves all alpha.2 skills and direct usage.
