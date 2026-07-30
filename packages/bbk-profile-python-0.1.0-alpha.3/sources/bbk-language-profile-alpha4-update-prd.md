# BBK alpha.4 language and domain profile update PRD

**Document status:** Implementation-ready guidance  
**Target BBK core:** `0.1.0-alpha.4`  
**Target profile release:** normally `0.1.0-alpha.2` or another explicit successor  
**Audience:** the agents and maintainers who produced the Rust, Python, Go, TypeScript/JavaScript, and CODESYS profiles  
**Purpose:** add qualified, profile-specific projections and review support for `ImplementationStructureContract` and `ExecutionSlice` without changing BBK's authority boundary or turning the profiles into software-only planning systems

---

## 1. Product decision

BBK alpha.4 introduces one domain-neutral planning object and one domain-neutral sequencing object:

```text
Architecture and interfaces
  -> ImplementationStructureContract, when applicable
      -> Execution Slices
          -> Work Units
              -> exact Candidate / Validation Cohort
```

An `ImplementationStructureContract` records enough of the intended realization shape to coordinate independent work and review consequential implementation decisions before candidate freeze. It may describe software modules and types, but it may equally describe CODESYS objects, procedures, data products, hardware assemblies, document sets, handoffs, or mixed socio-technical realizations.

An `ExecutionSlice` is the smallest **coherent**, **inspectable**, **reviewable**, **independently verifiable**, and **contained or reversible** increment. “Atomic” means that splitting it further would destroy useful integrated feedback or create an artificial handoff; it does not mean “one file,” “one function,” “one agent,” or an arbitrary line count.

Language and domain profiles must project these generic objects into the vocabulary and evidence model of their subject. They must not replace the generic object, broaden authority, or make profile-specific fields canonical BBK semantics.

### 1.1 Why this change exists

The previous composition model was strong at role, task, toolchain, work-unit, candidate, gate, and evidence boundaries, but it left a gap between architecture and implementation. Agents could receive a bounded work unit while still having to invent consequential realization choices such as:

- where state lives;
- which public or shared types exist;
- which module, object, package, form, assembly, or procedure owns behavior;
- how control and failure paths cross boundaries;
- how several work units become an early integrated observation;
- what is fixed versus intentionally delegated to the implementer.

This update makes that missing middle explicit and inspectable.

---

## 2. Goals

Each updated profile must:

1. Interpret the generic contract in profile-appropriate vocabulary.
2. Encourage type-driven development without equating “type” with a particular programming-language construct.
3. Help planners create the smallest coherent execution slices with useful early touchpoints.
4. Help workers implement fixed structure decisions while preserving explicitly delegated freedom.
5. Help reviewers compare planned and actual realization shape without failing harmless private differences.
6. Add deterministic or agent-assisted checks only where the profile has evidence to support them.
7. Preserve alpha.3 profile behavior for ordinary preflight, resolution, and gate planning.
8. Remain independently versioned, installable, reproducibly packaged, and qualification-bounded.

## 3. Non-goals

The profile update must not:

- make Markdown, a profile projection, or an agent response authoritative BBK state;
- add a permanent language-specific role when a task pack or profile procedure is sufficient;
- require an `ImplementationStructureContract` for every routine change;
- freeze every private helper, local variable, internal file, or incidental implementation choice;
- turn type-driven development into ceremonial wrappers, speculative generics, universal typestate, or unnecessary interfaces;
- treat a line-count threshold as the definition of an atomic slice;
- ban justified horizontal foundation work;
- execute project tools during profile resolution unless the existing bounded `--run-tools` contract explicitly permits read-only interrogation;
- install toolchains, dependencies, plugins, or validators;
- grant filesystem, network, credential, publication, deployment, controller, migration, completion, readiness, verification, or release authority;
- infer that an alpha.3 profile supports structure merely because the generic BBK object validates;
- edit a previously released profile package in place.

---

## 4. Core semantic model profiles must preserve

### 4.1 Capability increment

An actor-visible or otherwise meaningful integrated ability. It answers what becomes possible or validatable. It is larger and more outcome-oriented than an execution slice.

### 4.2 ImplementationStructureContract

The planned realization shape for a bounded subject. The generic contract owns:

- exact identity and revision;
- baseline and scope references;
- applicability level and rationale;
- artifact or object topology;
- key contracts;
- behavior, control, call, signal, or handoff paths;
- state and information ownership;
- effect boundaries;
- test seams, observability points, and migration touchpoints;
- fixed decisions;
- delegated freedom;
- prohibited shortcuts;
- review policy and acceptance criteria.

A profile projection may enrich this information. It may not silently change it.

### 4.3 ExecutionSlice

A coherent integrated step that creates an inspectable touchpoint and binds work, assertions, evidence, containment, and scaffolding disposition.

### 4.4 WorkUnit

One bounded responsibility assigned under exact scope, tools, effects, skills, dependencies, expected behavior, and handoff. A slice may include several work units. One work unit may contribute to more than one slice.

### 4.5 ValidationCohort

The exact candidate or tightly coupled candidate set evaluated together. It is an execution/evidence boundary, not a synonym for a slice.

---

## 5. Type-driven development requirements

The profile must define what “type” means in its domain and how explicit representations constrain invalid states and ambiguous ownership.

At minimum, profile guidance must cover:

- **identity types:** how distinct entities are prevented from collapsing into interchangeable strings, numbers, names, or paths;
- **state types:** how valid states and transitions are represented;
- **boundary types:** how data, commands, events, forms, signals, parameters, and results cross a boundary;
- **ownership types:** how mutation, stewardship, lifetime, and source-of-truth are made explicit;
- **failure types:** how absence, rejection, timeout, partial completion, stale data, degraded operation, and recovery are represented;
- **evidence types:** how a result distinguishes not-run, blocked, error, inconclusive, pass, and fail where relevant.

The guidance must also state where static notation is insufficient and runtime, tool, physical, human, or operational validation is still required.

### 5.1 Type-depth test

Recommend a type or abstraction only when it does at least one of the following:

- prevents a material invalid combination;
- localizes an invariant;
- makes ownership or authority unambiguous;
- stabilizes a boundary;
- improves change locality;
- creates a meaningful test seam;
- hides consequential complexity behind a smaller contract.

Do not recommend it merely because a language permits it.

---

## 6. Mandatory package changes

Every profile successor must include the following changes.

### 6.1 `PROFILE.json`

Retain the existing `bbk.language-profile.v1` schema and add:

```json
{
  "requires": {
    "bbk_minimum": "0.1.0-alpha.4"
  },
  "capabilities": {
    "implementation_structure": {
      "status": "supported",
      "artifact_kinds": [],
      "contract_kinds": [],
      "type_concepts": [],
      "touchpoint_kinds": [],
      "trigger_hints": []
    }
  },
  "entrypoints": {
    "structure": ["{python}", "tools/<profile-cli>.py", "--json", "structure"],
    "slice": ["{python}", "tools/<profile-cli>.py", "--json", "slice"],
    "structure_review": ["{python}", "tools/<profile-cli>.py", "--json", "structure-review"]
  }
}
```

#### Capability status

- `supported`: the profile has all required procedures, output schemas, fixtures, and qualification coverage.
- `partial`: the profile provides a bounded projection but declares material unsupported cases. `structure` is required; `slice` may fall back to generic BBK behavior.
- `unsupported`: the profile deliberately supplies no profile-specific projection. Do not advertise alpha.4 structure capability.

#### Authority block

The existing authority constraints remain unchanged. In particular, these fields must remain `false`:

```json
{
  "may_declare_pass": false,
  "may_expand_work_scope": false,
  "may_grant_tools_or_effects": false,
  "may_reduce_assurance": false
}
```

### 6.2 New output schemas

Add profile-namespaced schemas for:

1. `<profile>.implementation-structure-projection.v1`
2. `<profile>.execution-slice-projection.v1`
3. `<profile>.structure-review-result.v1`
4. `<profile>.planned-actual-structure-comparison.v1`, when the profile claims planned/actual comparison

The output must always include:

```text
profile ID and version
BBK version
input generic object ID, revision and digest
repository/environment preflight digest, when relevant
applicability disposition
profile-specific projection
unsupported or uncertain areas
advisories and blockers
no-authority boundary
output digest
```

### 6.3 New or updated skills

At minimum add or update:

- the compact profile router;
- worker/authoring guidance;
- architecture or boundary review guidance;
- correctness/state/failure review guidance;
- test-strategy guidance;
- evidence/reproducer guidance;
- a focused implementation-structure review pack.

Do not preload the focused structure reviewer into every ordinary worker invocation. Route it by applicability and role.

### 6.4 Mappings

Update task and risk mappings so these task profiles are understood:

```text
implementation-structure
execution-slicing
```

Add triggers for profile-specific materiality. Trigger detection must be explainable and deterministic where possible.

### 6.5 Gate recipes

Profiles may add planned gate recipes for:

- generic contract validation;
- profile projection validation;
- public/shared contract drift;
- ownership or state-model drift;
- planned-versus-actual shape comparison;
- slice touchpoint evidence;
- temporary scaffolding disposition.

A planned gate must not execute merely because resolution selected it. Every actual run remains subject to repository authority, exact candidate identity, environment identity, effect permissions, and the existing gate executor boundary.

### 6.6 Documentation

Update:

- `README.md`
- `docs/BOUNDARIES.md`
- `docs/USAGE.md`
- `docs/QUALIFICATION.md`
- `docs/SUPPORT-MATRIX.md`, where present
- release notes
- source-change/provenance documentation

The documentation must explain that the profile projection is a view over the generic contract, not a second source of truth.

---

## 7. Entrypoint contracts

### 7.1 `structure`

Conceptual invocation:

```bash
<profile-cli> --json structure \
  --root <repository-or-subject-root> \
  --contract <ImplementationStructureContract.json> \
  --role <role> \
  --task-profile <task> \
  --assurance-tier <tier>
```

It must:

1. Validate or consume BBK's validation result for the generic contract.
2. Run only bounded profile preflight permitted by the invocation.
3. Project generic artifact kinds, key contracts, type concepts, paths, ownership, failure, and review criteria into profile vocabulary.
4. Identify unsupported, ambiguous, or repository-dependent areas.
5. Return JSON without mutating the repository or running planned gates.

### 7.2 `slice`

Conceptual invocation:

```bash
<profile-cli> --json slice \
  --root <root> \
  --slice <ExecutionSlice.json> \
  --role <role> \
  --task-profile <task> \
  --assurance-tier <tier>
```

It must:

- translate the generic touchpoint into profile-relevant inspection and evidence;
- identify the exact dependency closure needed to make the touchpoint real;
- identify profile-specific scaffolding and cleanup risks;
- identify likely candidate and validation boundaries;
- detect obviously horizontal sequencing that delays all integrated feedback, but allow a documented foundation exception;
- avoid inventing work scope absent from the slice.

### 7.3 `structure-review`

Conceptual invocation:

```bash
<profile-cli> --json structure-review \
  --root <root> \
  --contract <contract.json> \
  --candidate <candidate-manifest.json> \
  --actual-inventory <optional-profile-inventory.json> \
  --assurance-tier <tier>
```

The result must distinguish:

```text
CONFORMS
ADVISORY_DIVERGENCE
MATERIAL_DIVERGENCE
BLOCKED
NOT_APPLICABLE
```

Review must compare fixed decisions and consequential shape. It must not fail harmless differences inside delegated freedom. A material divergence must name the affected fixed decision, contract, ownership boundary, behavior path, assertion, or slice.

---

## 8. Applicability policy

A profile must not require a standalone contract for all work. It must support the three generic levels:

| Level | Profile behavior |
|---|---|
| `none` | no profile projection; ordinary task/profile behavior applies |
| `inline` | compact structure guidance may be carried in the work unit or resolver result |
| `contract` | profile projection and applicable structure review are required |

### 8.1 Common material triggers

Profiles should map relevant forms of:

- public/shared interface changes;
- schema or wire changes;
- state ownership or lifetime changes;
- concurrency, scheduling, cancellation, retry, or recovery changes;
- persistence and migration;
- multi-package, multi-module, multi-object, multi-device, or multi-repository work;
- security, safety, authority, or effect-boundary changes;
- packaging or consumer-shape changes;
- difficult-to-reverse topology;
- consequential uncertainty about where behavior belongs.

### 8.2 Foundation exception

A horizontal or foundation-first slice is allowed when:

- a vertical touchpoint is impossible or misleading at that point;
- the foundation retires a named feasibility or safety risk;
- it has an inspectable technical or domain touchpoint of its own;
- the plan states what integrated slice it enables next;
- the work does not become an indefinite layer-by-layer sequence.

---

## 9. Profile-specific requirements

## 9.1 Rust

The Rust projection should describe:

- workspace, crate, module, feature, target, generated artifact, and test topology;
- public types, traits, functions, macros, wire schemas, and feature-gated contracts;
- ownership, borrowing, lifetime, mutability, and concurrency boundaries where consequential;
- task, future, channel, lock, cancellation-token, and shutdown ownership for async work;
- error enums, `Result` contracts, retryability, source preservation, and recovery;
- persistence, migration, transaction, idempotency, and replay boundaries;
- unsafe, FFI, ABI, representation, allocator, panic, and unwinding boundaries;
- test seams across pure logic, component, integration, consumer, and package surfaces.

Type-driven guidance should favor:

- newtypes for materially distinct identities or units;
- enums for closed states and outcomes;
- exhaustive transition handling;
- capability-bearing types or constructors where they prevent invalid use;
- narrow traits at true substitution/test seams;
- explicit ownership of async tasks and cancellation.

It must warn against:

- speculative generic abstraction;
- a trait for every concrete type;
- typestate that makes ordinary evolution or diagnostics worse;
- excessive wrapper types with no protected invariant;
- treating compiler success as proof of runtime protocol, persistence, or unsafe correctness.

Required Rust fixtures:

1. routine internal refactor with no standalone contract;
2. public crate API change;
3. async service with cancellation and resource ownership;
4. persistence migration;
5. unsafe/FFI boundary;
6. planned/actual harmless private module divergence;
7. planned/actual material public type or ownership divergence.

## 9.2 Python

The Python projection should describe:

- distribution, package, module, namespace, plugin, migration, generated artifact, and test topology;
- public import surface and `py.typed`/typing-package implications;
- dataclasses, enums, `Protocol`, abstract bases, typed mappings, models, and domain identities;
- the distinction among static annotations, runtime schemas, validation libraries, and unvalidated dynamic data;
- sync/async boundaries, task ownership, cancellation, context managers, process boundaries, queues, and serialization;
- exception taxonomy, retryability, partial failure, cleanup, and context preservation;
- packaging subjects: source tree, editable install, wheel, sdist-derived wheel, and deployed environment;
- plugin discovery, import side effects, entry points, and compatibility.

Type-driven guidance should favor:

- explicit domain identities and enums where strings would be ambiguous;
- `Protocol` at genuine consumer-defined seams;
- runtime validation at external and persistence trust boundaries;
- context managers for resource lifetime;
- explicit async/process result and cancellation contracts.

It must warn against:

- mistaking type-checker success for runtime validation;
- deep inheritance where composition or a small protocol is clearer;
- unbounded `Any` at consequential boundaries;
- DTO/model duplication without distinct semantics;
- framework-specific schemas leaking into the stable domain without need.

Required Python fixtures:

1. pure library internal change;
2. public typed package API;
3. external JSON/runtime validation boundary;
4. asyncio resource/cancellation flow;
5. multiprocessing or job handoff;
6. plugin entry point;
7. package artifact/consumer slice;
8. planned/actual public import drift.

## 9.3 Go

The Go projection should describe:

- module, workspace, package, command, generated code, build-tag, internal package, and test topology;
- exported structs, interfaces, functions, constants, sentinel/typed errors, wire types, and compatibility;
- package ownership and dependency direction;
- consumer-owned interfaces only at real seams;
- `context.Context` propagation and cancellation ownership;
- goroutine, channel, timer, ticker, pool, lock, and shutdown ownership;
- zero-value semantics, nil behavior, map-order assumptions, copy/alias behavior, and concurrency safety;
- CGO, unsafe, assembly, ABI, and platform boundaries;
- module release, downstream consumer, and `go.work` implications.

Type-driven guidance should favor:

- small explicit structs and closed constants/enums where practical;
- typed errors or result classification when callers need stable handling;
- ownership comments/contracts for goroutines and channels;
- APIs whose zero value is useful or explicitly invalidated;
- interfaces defined by consumers at actual substitution points.

It must warn against:

- interface-first design without multiple behaviorally meaningful implementations;
- hidden goroutine ownership;
- passing `context` through stored fields without a justified lifecycle;
- stringly typed state machines;
- assuming race-detector absence proves concurrency correctness.

Required Go fixtures:

1. internal package refactor;
2. exported API/wire change;
3. context cancellation and goroutine shutdown;
4. channel ownership and backpressure;
5. module/downstream consumer slice;
6. CGO/unsafe boundary;
7. planned/actual package ownership divergence.

## 9.4 TypeScript and JavaScript

The TypeScript/JavaScript projection should describe:

- workspace, package, module, entry point, export map, declaration, build output, browser bundle, server runtime, generated artifact, and test topology;
- exported types, functions, classes, components, events, messages, schemas, and package-consumer contracts;
- the boundary among TypeScript static types, checked JavaScript/JSDoc, transpile-only code, and runtime validation;
- discriminated unions, branded/nominal identities, state machines, and exhaustive handling;
- ESM/CommonJS and dual-package behavior;
- async resource, abort-signal, stream, timer, subscription, worker, and cleanup ownership;
- frontend/server trust boundaries and serialized data;
- package manager, lockfile, lifecycle-script, bundler, and browser/host extension implications.

Type-driven guidance should favor:

- discriminated unions for closed states and results;
- branded identities only when they protect a real invariant;
- runtime schemas at untrusted boundaries;
- explicit `AbortSignal` and cleanup contracts;
- exported type and runtime behavior kept in sync;
- consumer tests for package/export-map changes.

It must warn against:

- believing erased TypeScript types validate runtime data;
- duplicating the same schema independently at several layers;
- broad `any` or unsound assertions at trust boundaries;
- hidden subscription or timer lifetime;
- “type-only” changes that alter emitted declarations or consumer compatibility;
- treating transpilation as type checking or execution verification.

Required TS/JS fixtures:

1. strict TypeScript library;
2. checked JavaScript;
3. transpile-only TypeScript;
4. public ESM package;
5. dual ESM/CommonJS package;
6. browser application with runtime data boundary;
7. async resource/abort flow;
8. OMP or other host extension;
9. planned/actual export-map or runtime-schema drift.

## 9.5 CODESYS Structured Text

The CODESYS projection must remain domain-specific rather than forcing software repository concepts onto the engineering model. It should describe:

- project tree, library, application, folder, POU, FB, program, function, method, property, action, interface, DUT, enum, GVL, task, visualization or generated artifact topology as supported;
- canonical repository representation, including DEC/IMP pairing and nested-object ownership;
- interface, method, FB, DUT, GVL, library, package, task, and I/O contracts;
- scan-cycle call paths, task scheduling, state-machine paths, command/status flow, and arbitration;
- `VAR_INPUT`, `VAR_OUTPUT`, `VAR_IN_OUT`, references, pointers, inheritance, interfaces, retained/persistent state, and initialization ownership;
- fault, abort, reset, restart, power-cycle, warm/cold start, simulation, and degraded behavior;
- MCP/IDE provisional mutation followed by read-back and canonical repository comparison;
- ScriptEngine, PLCOpenXML, compile, Static Analysis, CoUnit, Test Manager, simulator, and physical-target touchpoints;
- candidate-bound serialized native validation and evidence freshness.

Type-driven guidance should favor:

- DUTs and strict enums for domain state and units;
- interfaces for stable behavioral contracts;
- explicit FB ownership of state and scan behavior;
- clear distinction among input, output, in-out, retained, persistent, and local state;
- state transitions that are visible and testable;
- explicit command/status and fault/recovery contracts.

It must warn against:

- treating an IDE object path as stable semantic identity without repository binding;
- implicit scan-order assumptions;
- shared mutable GVL state without accountable ownership;
- hidden retained/persistent state;
- pointer/reference aliasing without lifetime and nullability expectations;
- using generic external IEC tools as the authoritative CODESYS compiler;
- equating a passing compile with runtime, target, safety, or restart correctness.

Required CODESYS fixtures:

1. local ST method change with inline structure only;
2. FB plus interface/method signature change;
3. DEC/IMP and nested method topology;
4. scan-cycle state and retained-state change;
5. inheritance/interface obligation change;
6. CoUnit touchpoint slice;
7. MCP provisional edit plus read-back/candidate freeze;
8. ScriptEngine/native validation cohort;
9. simulator observation;
10. physical-target requirement marked blocked when no qualified target evidence exists;
11. planned/actual object ownership or signature divergence.

---

## 10. Non-software and mixed-subject behavior

Even profiles named for programming languages may be composed into mixed work. They must not assume that every slice ends in executable code.

A valid mixed slice might end in:

- an approved procedure walkthrough;
- a generated and inspected configuration package;
- a schema plus consumer fixture;
- a simulator trace;
- a physical test point measurement;
- an operator-facing recovery exercise;
- a reviewable document package;
- a migration rehearsal;
- a protocol exchange between software and equipment.

Where the language profile covers only one portion, it must return a bounded projection and identify adjacent obligations rather than pretending to own the whole system.

---

## 11. Review and validation behavior

### 11.1 Structure quality review

The focused reviewer should evaluate:

- responsibility and ownership clarity;
- depth of modules or domain objects;
- interface width and stability;
- type and state-model integrity;
- change locality;
- failure, cancellation, recovery, restart, or degraded paths;
- test seams and observability;
- migration and compatibility;
- whether fixed decisions are truly consequential;
- whether delegated freedom is sufficient;
- whether the design creates early integrated feedback.

### 11.2 Planned-versus-actual comparison

Classify differences as:

- **within delegated freedom** — no finding unless quality is independently poor;
- **advisory drift** — update the contract or implementation at the next safe point;
- **material divergence** — affected fixed decision, interface, owner, state model, effect boundary, slice, or verification must be reviewed before acceptance;
- **unknown** — evidence or inventory is insufficient;
- **not applicable** — the contract did not govern the observed detail.

Do not use raw file-count equality or exact private tree equality as the primary conformance rule.

### 11.3 Slice review

A slice is acceptable only when it:

- advances integrated behavior or retires a named foundation risk;
- has a domain-appropriate touchpoint;
- has one integration owner;
- names the work and interfaces involved;
- contains explicit assertions and evidence;
- has failure containment, rollback, or safe disposition;
- names temporary scaffolding and its removal or successor;
- enables a clear next slice or capability.

---

## 12. Qualification requirements

The successor profile may claim alpha.4 structure support only after all applicable checks pass.

### 12.1 Package and reproducibility

- two independent source builds produce byte-identical archives, manifests, checksum companions, and release notes;
- clean extraction passes strict package verification;
- no unexpected files, symlinks, unsafe paths, duplicate members, or mode drift;
- the package declares BBK alpha.4 compatibility;
- installer user/project round trips preserve ownership boundaries and modified files;
- OMP extension, if present, parses, registers, and invokes the installed CLI in a mock environment.

### 12.2 Schema and resolver

- every new JSON schema parses;
- positive and negative structure fixtures behave as expected;
- routine resolution remains minimal;
- structure review does not fan out every specialist;
- profile output is deterministic for the same inputs;
- effective profile locks include generic contract/slice digests and profile projection digests;
- an alpha.3 profile still resolves as `legacy-unprojected` under alpha.4;
- an alpha.4 profile returns its declared support status accurately.

### 12.3 Selection fixtures

At minimum prove:

| Scenario | Expected behavior |
|---|---|
| routine private change | no standalone structure reviewer |
| material public/shared contract | structure projection and focused review selected |
| state/concurrency/recovery change | ownership and failure review selected |
| explicit execution-slicing task | slice projection selected |
| consequential migration | structure, migration, evidence, and applicable consumer checks selected |
| broad survey | does not automatically trigger every structure specialist |
| unsupported subject | bounded `unsupported`/`partial` result, not invented confidence |
| unavailable required tool | `BLOCKED`, not silently skipped |
| harmless private divergence | no material conformance failure |
| fixed decision divergence | material finding with exact affected reference |

### 12.4 Live qualification boundary

Static/package qualification must not claim live compatibility with every toolchain, runtime, IDE, compiler, package manager, browser, controller, simulator, or target. Record the exact live environment tested and everything that remains project-specific.

---

## 13. Release and compatibility policy

1. Release a new immutable profile version; do not alter alpha.1 artifacts.
2. Normally use `0.1.0-alpha.2` for this additive profile contract.
3. Set `requires.bbk_minimum` to `0.1.0-alpha.4`.
4. Install versions side by side.
5. Preserve old profile locks and evidence against their original effective digests.
6. Require projects to rerun resolution and deliberately update locks.
7. Document whether support is `supported`, `partial`, or `unsupported`.
8. Preserve source provenance and exact changes from the prior profile.
9. Do not claim that a BBK core upgrade automatically upgrades a profile.

---

## 14. Definition of done

A profile update is complete when:

- `PROFILE.json` declares accurate alpha.4 capability and entrypoints;
- the generic contract and slice digests survive resolution and lock generation;
- profile-specific projections are schema-valid and deterministic;
- type-driven guidance is domain-specific, proportional, and explicit about runtime limits;
- the structure reviewer distinguishes fixed decisions from delegated freedom;
- slices have domain-appropriate touchpoints and evidence;
- positive, negative, legacy, unsupported, and planned/actual fixtures pass;
- ordinary work remains minimal and does not fan out specialists;
- package, installer, reproducibility, clean extraction, and mock OMP checks pass;
- qualification boundaries are written plainly;
- release artifacts include archive, checksum, package manifest, release notes, and human/machine-readable qualification reports.

---

## 15. Required handoff from each profile agent

Return one package containing:

```text
successor profile source tree
successor immutable release archive
SHA-256 companion
package manifest
release notes
qualification report (Markdown and JSON)
qualification evidence archive and manifest
source-change/provenance record
alpha.4 fixture matrix
known limitations and next live-qualification steps
```

Also return a concise design note that answers:

1. What are the profile's meaningful type concepts?
2. What structure changes trigger `inline` versus `contract` treatment?
3. What is the profile's touchpoint vocabulary?
4. Which planned/actual differences are material?
5. Which checks are deterministic, agent-reviewed, tool-authoritative, simulator-based, human-reviewed, or operational?
6. What remains unsupported or unqualified?

---

## 16. Copy-paste assignment prompt

> Update the `<PROFILE>` BBK profile from its current immutable alpha.1 release to an independently versioned alpha.4-compatible successor, normally `0.1.0-alpha.2`. Use BBK core `0.1.0-alpha.4` and this PRD as the controlling product requirements. Preserve the existing profile's qualified behavior, package integrity, resolver minimality, authority boundary, source provenance, and repository-first policy. Add accurate `ImplementationStructureContract` and `ExecutionSlice` capability declarations; profile-specific `structure`, `slice`, and `structure-review` entrypoints; deterministic namespaced output schemas; type-driven development guidance; focused structure review; planned-versus-actual comparison; proportional mappings, gates, fixtures, and qualification. Do not edit the prior release in place, add a permanent language-specific BBK role, run or install project tools during resolution, broaden effects or authority, equate type notation with runtime truth, require a structure contract for every task, or define atomicity by line count. Prove legacy alpha.3 interoperability, routine non-fan-out, material routing, positive and negative fixtures, harmless delegated divergence, material fixed-decision divergence, reproducible builds, clean extraction, safe installer round trips, and static/mock OMP installed-CLI execution. Return the complete immutable release and qualification/evidence package plus a concise design note answering the six questions in Section 15.

