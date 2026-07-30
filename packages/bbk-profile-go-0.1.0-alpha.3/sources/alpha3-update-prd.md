# Go profile alpha.3 update PRD

**Document status:** implementation-ready update requirements  
**Target package:** `bbk-profile-go 0.1.0-alpha.3`  
**Required BBK core:** `0.1.0-alpha.8` or later compatible successor  
**Date:** 2026-07-24  
**Authority:** proposal and implementation assignment only; it grants no project mutation, external-effect, installation, evidence-sufficiency, review-closure, Blueprint, or release authority

## 1. Product decision

Publish an immutable alpha.3 successor to the current Go alpha.2 package. Preserve every existing alpha.2 procedure, skill, gate recipe, structure/slice capability, installer safeguard, package-integrity rule, and qualification boundary. Add typed State–Decision–Effect and Review Assurance integration through the BBK alpha.8 `bbk.profile-capability.v1` protocol.

Do not rewrite the existing comprehensive or focused skills merely to fit the new core. Add a thin dispatch/controller layer, explicit mappings, result adapters, and qualification fixtures. Improve an existing skill only where a real semantic gap is found and record the source change.

## 2. Exact source binding

| Field | Value |
|---|---|
| Source package | `bbk-profile-go 0.1.0-alpha.2` |
| Source archive SHA-256 | `23f3e92688d505de96e02ec10ca14d5ae4cf08b81b71e1296b6cd48e3c279bc8` |
| Source package root SHA-256 | `a8ac0e0d821cca94719fa47e8caf6bd32f43bf27e778ad9210e9ff6c0feee642` |
| Source manifested files | 110 |
| Existing skill count | 14 |
| Successor version | `0.1.0-alpha.3` |
| Minimum core | `0.1.0-alpha.8` |

Treat the alpha.2 package as immutable. Build alpha.3 from its exact extracted content and preserve historical digests in `SOURCE-CHANGES.md` and release evidence.

## 3. Goals

The successor must:

1. preserve all existing alpha.2 behavior and package layout unless an explicit migration is documented;
2. adopt the exact alpha.8 capability request/result protocol;
3. support all three State–Decision–Effect operations;
4. support the profile's declared logical review lenses at `supported` maturity;
5. compile a bounded, exact ReviewContextManifest rather than passing the entire repository by default;
6. adapt exact native/profile evidence to EvidenceReceipt v2 without inventing missing fields;
7. keep generic BBK authoritative for candidate identity, AssuranceContract interpretation, review planning, evidence eligibility, finding lifecycle, aggregation, and locks;
8. preserve routine minimality and select focused procedures only from exact work, risk, change, assertion, and lens inputs;
9. produce reproducible package, clean-extraction, installer, schema, positive, negative, and compatibility evidence.

## 4. Non-goals and authority constraints

The successor must not:

- grant tools or effects because a profile or skill is installed;
- mutate the reviewed subject from any of the six typed operations;
- install or upgrade language/domain toolchains, dependencies, runtimes, add-ons, or package managers;
- declare a generic assertion passed merely because a profile procedure completed;
- replace ReviewManifest or AssuranceContract semantics with a profile-local checklist;
- automatically launch every existing focused review;
- use a broad comprehensive-analysis skill followed by all focused reviewers by default;
- close findings, accept risk, waive required evidence, or create Blueprint authority;
- edit the alpha.2 package or old profile locks in place.

## 5. Required `PROFILE.json` successor contract

The capability object must refer to **entrypoint key names**. The entrypoint object contains argv arrays. Use this shape, adapting the executable filename to the package's existing controller when preferable:

```json
{
  "requires": {
    "bbk_minimum": "0.1.0-alpha.8"
  },
  "capabilities": {
    "state_decision_effect": {
      "status": "supported",
      "dispatch_protocol": "bbk.profile-capability.v1",
      "projection_entrypoint": "state_effect",
      "inventory_entrypoint": "state_effect_inventory",
      "review_entrypoint": "state_effect_review",
      "representations": [
        "defined identity types and typed constants",
        "explicit lifecycle structs and transition functions",
        "products of independent lifecycle dimensions",
        "interfaces at real consumer/effect boundaries"
      ],
      "formal_model_tools": [
        "table/property/model-based tests supported by the repository",
        "race detector and deterministic/synctest-style scheduling where qualified",
        "fuzzing for untrusted input and protocol boundaries",
        "optional external state-machine or Quint/TLA+ mappings"
      ],
      "limitations": [
        "The profile must not install or select a Go toolchain.",
        "A race-detector pass does not prove absence of all concurrency defects.",
        "Cross-compilation, CGO, platform tags, external services, performance and module-release claims require exact environment and consumer evidence."
      ]
    },
    "review_assurance": {
      "status": "supported",
      "dispatch_protocol": "bbk.profile-capability.v1",
      "context_entrypoint": "review_context",
      "review_entrypoint": "review_lens",
      "evidence_entrypoint": "evidence_adapter",
      "lens_ids": [
        "architecture-boundary",
        "interface-consumer-compatibility",
        "implementation-structure",
        "state-concurrency-effect-recovery",
        "security-privacy-supply-chain",
        "test-evidence",
        "operations-performance-resource",
        "package-install-migration-release"
      ],
      "context_selectors": [
        "changed-surface",
        "governing-contracts",
        "consumer-and-failure-closure"
      ],
      "evidence_adapters": [
        "profile-native-evidence-v1"
      ],
      "limitations": [
        "The profile must not install or select a Go toolchain.",
        "A race-detector pass does not prove absence of all concurrency defects.",
        "Cross-compilation, CGO, platform tags, external services, performance and module-release claims require exact environment and consumer evidence."
      ]
    }
  },
  "entrypoints": {
    "state_effect": [
      "{python}",
      "tools/profile.py",
      "--json",
      "state-effect"
    ],
    "state_effect_inventory": [
      "{python}",
      "tools/profile.py",
      "--json",
      "state-effect-inventory"
    ],
    "state_effect_review": [
      "{python}",
      "tools/profile.py",
      "--json",
      "state-effect-review"
    ],
    "review_context": [
      "{python}",
      "tools/profile.py",
      "--json",
      "review-context"
    ],
    "review_lens": [
      "{python}",
      "tools/profile.py",
      "--json",
      "review-lens"
    ],
    "evidence_adapter": [
      "{python}",
      "tools/profile.py",
      "--json",
      "evidence-adapter"
    ]
  }
}
```

A successful package inspection must report:

```text
stateDecisionEffectDispatch = typed-v1
reviewAssuranceDispatch     = typed-v1
```

For CODESYS, `review_assurance.status=partial` is intentional until the native environment is qualified; typed dispatch still operates and returns `BLOCKED`, `PARTIAL`, or `UNSUPPORTED` honestly when native proof is unavailable.

## 6. Common dispatch protocol

Every declared operation must accept:

```text
--request <path-to-bbk.profile-capability-request.v1>
```

The controller must:

1. load and validate the request schema;
2. verify `profile.id`, `profile.version`, package root, manifest digest, operation, subject and request digest;
3. resolve each input path relative to `Path(request_path).parent`;
4. treat `BBK_PROFILE_SOURCE_ROOT` as the actual read-only subject source and keep it outside stable result identity;
5. obey the request authority envelope;
6. return exactly one `bbk.profile-capability-result.v1` object bound to `requestDigest`;
7. keep temporary paths, timing, process IDs, stdout/stderr and runtime diagnostics out of the semantic payload unless they are themselves explicitly adapted evidence;
8. return `BLOCKED`, `UNSUPPORTED`, `PARTIAL`, or `ERROR` instead of fabricating a pass.

`runQualifiedReadOnlyTools=true` authorizes only repository/profile-qualified read-only inspection or evidence commands. It does not authorize dependency installation, mutation, network use, publication, deployment, controller action, or secret access.

## 7. State–Decision–Effect requirements

### 7.1 Profile interpretation

The profile must explain and project these Go concepts:

- defined identity types and typed constants
- explicit lifecycle structs and transition functions
- products of independent lifecycle dimensions
- interfaces at real consumer/effect boundaries
- goroutine, channel, context, timer, mutex and shutdown ownership
- typed error/result, persistence, migration, generated-code and cgo boundaries

The generic StateDecisionEffectDesign remains authoritative. The projection must identify:

- generic design reference and digest;
- applicable profile representations and anti-patterns;
- fixed versus delegated implementation choices;
- actual inventory procedure;
- expected state owners, decision entrypoints, effect executors, retries, cancellation, acknowledgement, recovery and evidence;
- qualified property/model/trace tools and explicit limitations.

### 7.2 `state-effect`

Return a namespaced projection, not a replacement design. It should select relevant existing skills/rules and explain each selection. Routine `NONE`/`INLINE` cases must not expand into comprehensive review campaigns.

### 7.3 `state-effect-inventory`

Inspect only the exact subject and requested paths. Return a profile-namespaced actual inventory containing at least:

```text
inventory ID and subject digest
design reference and digest
state representations and canonical owners
derived or shadow state observations
decision entrypoints and hidden dependencies
effect executors/adapters and external boundaries
retry, cancellation, duplicate, timeout and acknowledgement mechanisms
persistence, migration, recovery and shutdown mechanisms
actual tests/traces/models discovered
unknown or unavailable inventory areas
source/evidence references
```

Unknown inventory blocks conformance; it is not a pass.

### 7.4 `state-effect-review`

Compare the exact generic design and exact inventory. Classify differences as delegated freedom, advisory drift, material divergence, blocked, or unknown. Do not mutate either input and do not reinterpret a generic fixed decision.

### 7.5 Formalization and trace tools

Candidate profile-specific techniques include:

- table/property/model-based tests supported by the repository
- race detector and deterministic/synctest-style scheduling where qualified
- fuzzing for untrusted input and protocol boundaries
- optional external state-machine or Quint/TLA+ mappings

All remain trigger-based and repository/environment-qualified. A passing property/model/trace run proves only its declared properties, assumptions, bounds, subject and environment.

## 8. Review Assurance requirements

### 8.1 Supported lens mapping

| Logical lens | Existing procedure/skill mapping |
|---|---|
| `architecture-boundary` | comprehensive-analysis-go, only for explicit broad surveys |
| `interface-consumer-compatibility` | go-api-module-boundary-review |
| `implementation-structure` | go-implementation-structure-review |
| `state-concurrency-effect-recovery` | go-correctness-concurrency-review |
| `security-privacy-supply-chain` | go-security-supply-chain-review; add go-unsafe-cgo-assembly-review when applicable |
| `test-evidence` | go-test-strategy-review |
| `operations-performance-resource` | go-operational-readiness-review |
| `package-install-migration-release` | go-package-release-gates |

Do not register a lens merely because an existing skill sounds related. Every registered lens needs a tested routing rule, bounded context selector, procedure, result shape, and limitations. `intent-outcome`, `specification-acceptance`, `feasibility-dependency`, and `cross-shard-integration` remain generic unless this profile adds real language/domain-specific value.

A comprehensive survey is a survey or architecture lens—not a mandatory precursor to every focused review. The smallest sufficient profile procedure set must be selected.

### 8.2 `review-context`

Compile context from exact ReviewManifest assignments and AssuranceContract assertions. Normal selectors should include:

- go.mod/go.work, toolchain directives and supported platforms/tags
- module/package/exported API and downstream consumers
- goroutine/channel/context/timer/synchronization owners
- generated code, build tags, persistence and migration
- unsafe, cgo, assembly and ABI surfaces
- tests, fuzz/race/synctest evidence and repository commands

Return a valid `bbk.review-context-manifest.v1`, including exact content roots, omissions, exclusions, generated/untracked/external items, retrieval-only material, redaction, shards, cross-shard assertions, completeness, blockers and dependency closure. A profile context pack may add language-aware grouping but cannot omit required generic context.

### 8.3 `review-lens`

Receive exact lens and assignment IDs from the request. Return a namespaced result with:

```text
subject and request identity
lens and assignment IDs
assertion evaluations or procedure output
profile findings with evidence references
coverage gaps, blocked checks and limitations
recommended generic disposition, never authoritative closure
```

A result `PASS` means the profile operation completed successfully; assertion status remains inside the payload and is interpreted by generic BBK.

### 8.4 `evidence-adapter`

Use these existing or successor evidence procedures:

- repository-authoritative fmt/vet/static/test/build commands
- race, fuzz, synctest, consumer, module and release evidence when applicable
- cgo/unsafe/assembly evidence kept separately qualified
- go-evidence-reproducer as the principal EvidenceReceipt v2 adapter

A successful result must contain a valid `bbk.evidence-receipt.v2`. Preserve the original native evidence by digest. Do not invent command, exit status, timestamp, toolchain, environment, subject or completeness facts. Incomplete historical evidence becomes `LEGACY_IMPORTED` or `UNSTRUCTURED_OBSERVATION` with explicit missing fields.

## 9. Profile-specific limitations

- The profile must not install or select a Go toolchain.
- A race-detector pass does not prove absence of all concurrency defects.
- Cross-compilation, CGO, platform tags, external services, performance and module-release claims require exact environment and consumer evidence.

These limitations must appear in `PROFILE.json`, relevant result payloads, support matrix and qualification report. A required unavailable capability yields a bounded blocked result rather than silently downgrading assurance.

## 10. Required implementation changes

Use the existing package's controller and installer architecture where possible. Add or update:

```text
PROFILE.json
existing tools/<profile-controller>.py or a thin tools/profile.py adapter
mappings/state-effect-map.json
mappings/review-lens-map.json
mappings/review-context-map.json
mappings/evidence-adapter-map.json
schemas/<profile>-state-effect-projection-v1.schema.json
schemas/<profile>-state-effect-inventory-v1.schema.json
schemas/<profile>-state-effect-review-v1.schema.json
schemas/<profile>-review-lens-result-v1.schema.json
schemas/<profile>-evidence-adapter-result-v1.schema.json
fixtures/profile-dispatch/*
docs/PROFILE-DISPATCH.md
docs/MIGRATION-ALPHA2-TO-ALPHA3.md
docs/QUALIFICATION.md
docs/SOURCE-CHANGES.md
```

The exact file split may vary, but one controller must implement the same six semantic operations and all mappings must have one authoritative source.

Update the OMP profile extension only to expose the profile's typed procedures and diagnostics. It must not duplicate generic BBK request, assurance, evidence, finding, aggregation or locking logic.

## 11. Compatibility and migration

- Preserve existing `preflight`, `resolve`, `gate_plan`, `structure`, `slice`, and `structure_review` entrypoints and output dialects.
- Preserve all current skill IDs and direct standalone skill use.
- Preserve alpha.2 package and lock identity.
- Do not synthesize alpha.3 capability into an alpha.2 lock.
- Set `requires.bbk_minimum` to `0.1.0-alpha.8`.
- Publish alpha.3 side by side; project owners deliberately update locks.
- Profile-dependent evidence may be reused only when its declared closure, including profile package and dispatch protocol, is unchanged.

## 12. Fixtures and tests

At minimum provide:

### Contract and dispatch

- package verification and exact source-lineage check;
- capability declaration positive and negative fixtures;
- request digest mismatch, wrong profile/version, wrong subject and stale input rejection;
- relative request-path resolution from a different working directory;
- all six operations with valid typed results;
- stable repeated effective profile resolution;
- lock binding to stable dispatch result;
- no temporary/absolute path in stable payloads.

### State/effect

- `NONE`, `INLINE`, and `CONTRACT` routing;
- valid sum state and product-of-sums;
- shadow/duplicate state finding;
- hidden dependency/effect finding;
- retry, duplicate, cancellation, timeout, ambiguous acknowledgement and recovery fixture;
- inventory unavailable → blocked;
- harmless private divergence and material boundary divergence;
- applicable profile-specific property/model/trace evidence.

### Review

- routine work selects no unnecessary profile lens;
- each registered lens selects only its mapped procedure;
- unsupported lens remains unhandled by the profile;
- exact context completeness and declared exclusions;
- required missing context → blocked;
- blind versus targeted prior-finding visibility preserved;
- native evidence valid, incomplete, stale, wrong-subject and redacted cases;
- profile operation completion does not automatically pass generic assertions.

### Regression/package

- every alpha.2 package test still passes;
- all existing skills remain present and unchanged unless listed in source changes;
- OMP mock registration and adjacent CLI invocation;
- two byte-identical builds and clean-extraction rebuild;
- strict package manifest, safe paths/modes/symlinks;
- user/project install, forced-upgrade backup and uninstall preservation.

## 13. Acceptance criteria

The update is complete when:

1. the exact alpha.2 source is preserved and its changes are enumerated;
2. `PROFILE.json` validates under BBK alpha.8 and reports typed-v1 dispatch;
3. all six operations bind exact requests and typed results;
4. State–Decision–Effect projection, inventory and review are profile-specific but generic-authority preserving;
5. every registered lens has a tested mapping and bounded context;
6. evidence adaptation produces valid EvidenceReceipt v2 without invented facts;
7. routine work remains proportional;
8. unsupported/native-unavailable cases fail honestly;
9. all alpha.2 tests and new fixtures pass;
10. source and clean-extraction builds are byte-identical;
11. installation and removal preserve ownership and modified files;
12. package qualification and live toolchain qualification are stated separately.

## 14. Required delivery

Return:

```text
immutable bbk-profile-go-0.1.0-alpha.3.zip
SHA-256 companion
package manifest
release notes
migration guide
source-change record bound to alpha.2 digests
human and JSON qualification reports
qualification evidence archive and manifest
fixture matrix
typed PROFILE.json and operation schemas
known limitations
live OMP/toolchain qualification plan
```

## 15. Copy-paste implementation assignment

> Build `bbk-profile-go 0.1.0-alpha.3` as an immutable successor to the exact alpha.2 archive SHA-256 `23f3e92688d505de96e02ec10ca14d5ae4cf08b81b71e1296b6cd48e3c279bc8` and package-root SHA-256 `a8ac0e0d821cca94719fa47e8caf6bd32f43bf27e778ad9210e9ff6c0feee642`. Preserve all existing skills, procedures, gates, structure/slice behavior, installer safeguards, package integrity and direct standalone usage. Require BBK `0.1.0-alpha.8`; implement `bbk.profile-capability.v1` for `state-effect`, `state-effect-inventory`, `state-effect-review`, `review-context`, `review-lens`, and `evidence-adapter`; use entrypoint key names in capabilities; accept `--request`; resolve input paths relative to the request; return exact typed results bound to the request digest; keep all operations read-only and non-authority-bearing. Map only the tested logical lenses listed in this PRD, preserve generic AssuranceContract/review/evidence/finding/aggregation authority, and return blocked or partial results rather than fabricating native evidence. Add positive, negative, proportionality, compatibility, reproducibility, clean-extraction, OMP-mock and installer fixtures. Publish complete immutable release and qualification evidence without editing alpha.2 in place.
