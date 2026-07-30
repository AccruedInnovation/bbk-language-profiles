# BBK Python Profile

`bbk-profile-python` is an optional, host-neutral Python language profile for the Blueprint Bootstrap Kit (BBK).

**Version:** `0.1.0-alpha.3`  
**Required BBK:** `0.1.0-alpha.8` or a compatible successor  
**Maturity:** `comprehensive-alpha`

This alpha.3 package preserves the alpha.2 Python preflight, resolver, gates, structure/slice projections, installer, OMP extension, and focused review packs while adding typed State–Decision–Effect and Review Assurance dispatch through the BBK alpha.8 profile protocol.

## Version identities

The profile package version is `0.1.0-alpha.3` and the minimum compatible BBK core is `0.1.0-alpha.8`. Legacy projection fields containing `"bbk_version": "0.1.0-alpha.4"` identify the implementation-structure/execution-slice **contract dialect introduced in BBK alpha.4**; they do not report the installed core version. See `docs/METADATA-CONTRACT.md`.

## What alpha.4 adds

```text
Generic ImplementationStructureContract
  -> deterministic Python structure projection
      -> focused Python authoring/review guidance

Generic ExecutionSlice
  -> Python package/runtime touchpoint projection
      -> dependency closure, candidate/validation boundary and scaffolding disposition

Exact candidate + actual inventory
  -> planned-versus-actual Python structure comparison
      -> CONFORMS | ADVISORY_DIVERGENCE | MATERIAL_DIVERGENCE | BLOCKED | NOT_APPLICABLE
```

The generic BBK object remains authoritative. Python projections may add vocabulary and checks; they do not change identity, fixed decisions, delegated freedom, work scope, authority, or assurance.

## Commands

```bash
bbk-python preflight --root <project>
bbk-python resolve --root <project> --role worker --task-profile implementation --assurance-tier routine
bbk-python gate-plan --root <project> --role validator --assurance-tier consequential

bbk-python structure \
  --root <project> \
  --contract <ImplementationStructureContract.json>

bbk-python slice \
  --root <project> \
  --slice <ExecutionSlice.json> \
  --contract <optional-contract.json>

bbk-python structure-review \
  --root <candidate-checkout> \
  --contract <contract.json> \
  --candidate <candidate-manifest.json> \
  --actual-inventory <optional-python-inventory.json>
```

All projection and planning commands are non-executing. They do not create environments, install dependencies, run repository gates, mutate the project, or declare a pass.

## Skills

The package installs 15 skills, including the compact `bbk-python` router, the corrected broad `comprehensive-analysis-python` survey, three alpha.4 structure/slice skills, and focused API/package, runtime, typing, testing, operations, security, native-extension, release, evidence, and optional hypermedia packs.

## Profile-specific type concepts

The profile recognizes domain identities, enum states, dataclass/value forms, consumer-defined protocols, abstract bases where runtime nominal behavior is needed, typed mappings, runtime schemas, static annotations, exception/result dispositions, resource owners, async task/cancellation owners, process messages, serialization shapes, public typing exports, and evidence dispositions that distinguish not-run, blocked, error, inconclusive, pass, and fail.

Static typing is never treated as runtime validation. Runtime validation is still required at untrusted, persistence, process, serialization, and other material boundaries.

## Installation

```bash
python3 tools/verify_package.py --strict-mode
python3 tools/install.py install --scope user --omp
```

See `docs/INSTALL.md` and `docs/USAGE.md`.

## Authority boundary

This profile may add procedure, review criteria, and planned gate recipes. It may not:

- declare a pass, readiness, completion, acceptance, or release;
- expand work scope;
- grant tools, credentials, network, filesystem, publication, deployment, migration, or other effects;
- reduce assurance;
- replace the generic BBK contract or slice;
- silently install or upgrade project tooling.

## Alpha.8 typed profile capability

This `0.1.0-alpha.3` package adds six read-only `bbk.profile-capability.v1` operations through `tools/profile.py`. It requires BBK `0.1.0-alpha.8` and preserves all alpha.2 skills and direct usage.
