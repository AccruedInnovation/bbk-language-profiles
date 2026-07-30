---
name: python-implementation-structure-review
description: Compare a Python implementation candidate with one accepted generic ImplementationStructureContract, distinguishing fixed-decision or consequential-shape divergence from harmless private differences inside delegated freedom.
---

# Python Implementation Structure Review

Review one exact contract and candidate. The review is read-only and does not grant acceptance or release authority.

## Bind the subject

Require:

- generic contract ID, revision, canonical digest, applicability, and acceptance criteria;
- exact candidate manifest and digest;
- repository/preflight identity;
- actual inventory or a bounded static inventory derived from the candidate checkout;
- assurance tier and exact review coverage.

Return `BLOCKED` when the candidate, contract, inventory, or required environment cannot be tied to the exact subject.

## Compare consequential shape

Evaluate:

1. **Public and shared surfaces** — import paths, `__all__`, entry points, plugin groups, functions, classes, protocols, stubs, `py.typed`, runtime schemas, exception classes, serialization forms, and package metadata governed by the contract.
2. **State and ownership** — source of truth, mutation authority, resource lifetime, transaction ownership, task/process/queue ownership, cancellation, retry, cleanup, and recovery.
3. **Boundary truth** — where static annotations end and runtime validation begins; where external data becomes trusted domain data; where package, process, persistence, and native-extension boundaries sit.
4. **Behavior paths** — trigger, participants, calls or handoffs, success, partial failure, exceptions, cancellation, cleanup, retry, and recovery.
5. **Test and observability seams** — consumer fixtures, package subjects, fault paths, migration touchpoints, logs/metrics, and evidence identity.
6. **Fixed decisions** — compare only consequential decisions explicitly marked fixed. Name the exact fixed-decision ID when divergence is material.
7. **Delegated freedom** — do not fail private helper names, equivalent private module placement, local iteration, private test utility layout, or another internal form that preserves the fixed contracts and quality.
8. **Prohibited shortcuts** — identify a demonstrated prohibited shortcut and its affected contract or assertion.

## Dispositions

Use exactly:

- `CONFORMS` — the inspected consequential shape conforms; this is not a release pass.
- `ADVISORY_DIVERGENCE` — harmless or low-consequence drift, normally within delegated freedom or suitable for later contract refresh.
- `MATERIAL_DIVERGENCE` — an exact fixed decision, public/shared contract, ownership boundary, behavior path, effect boundary, slice, or verification obligation diverges.
- `BLOCKED` — exact comparison is impossible because required evidence is absent, stale, or not bound to the subject.
- `NOT_APPLICABLE` — the contract level is `none` or the subject is outside the Python profile.

## Finding requirements

Every material finding must name:

- planned reference and actual evidence;
- why the difference is outside delegated freedom;
- affected contract, owner, state model, effect boundary, assertion, or slice;
- smallest responsible route: implementation repair, contract impact review, interface review, migration review, evidence repair, or Wayfinder decision.

Do not use raw file-count equality or exact private tree equality as conformance. Do not reinterpret missing evidence as a defect in the candidate.

## Return

Return the namespaced structure-review result and planned/actual comparison, evidence coverage, limitations, advisories, blockers, and no-authority boundary. Preserve uncertainty honestly.
