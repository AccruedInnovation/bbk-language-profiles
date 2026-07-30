# ImplementationStructureContract and execution slicing

## 1. Purpose

Architecture answers which responsibilities, boundaries and interfaces should exist. An `ImplementationStructureContract` answers what shape the realization should take sufficiently to coordinate bounded work. It is not source code, a substitute for architecture, or a demand to freeze every helper.

The contract should make the consequential implementation decisions visible before candidate freeze:

- artifact or object topology;
- key types, schemas, signatures or structured forms;
- important behavior, call, control or handoff paths;
- state, information and effect ownership;
- failure, cancellation, recovery and degraded behavior;
- test seams, observability points and migration touchpoints;
- fixed decisions, delegated freedom and prohibited shortcuts.

## 2. Applicability

Use the least ceremony sufficient for the decision.

| Level | Use |
|---|---|
| `none` | Routine local change whose realization shape is already constrained and low risk |
| `inline` | A compact structure note embedded in the work unit |
| `contract` | A separate accepted contract for material cross-boundary, stateful, irreversible or multi-artifact work |

Common triggers include public interface changes, ownership changes, stateful orchestration, concurrency, recovery, migration, multi-module or multi-repository work, hard-to-reverse topology and consequential uncertainty about where behavior belongs.

## 3. Fixed decisions and delegated freedom

A useful contract distinguishes:

**Fixed decisions** — a worker may not change them without the applicable impact/change process.

Examples: state ownership, public signature, durability boundary, idempotency rule, source-of-truth location, safety interlock, migration sequence.

**Delegated freedom** — the worker may choose inside stated bounds.

Examples: private helper names, local iteration style, small refactors that preserve ownership and behavior, exact placement of a private test utility.

The contract should not contain pseudocode merely to simulate certainty.

## 4. Type-driven development

A profile should define its meaningful “type” vocabulary. The generic discipline is:

1. Name important identities, states and outcomes explicitly.
2. Represent permitted transitions and ownership.
3. Define boundary shapes before independent work begins.
4. Prefer representations that prevent invalid composition where practical.
5. Validate at runtime where static notation cannot establish facts.
6. Keep types deep: they should hide or constrain meaningful complexity, not add ceremonial wrappers.

## 5. Execution slices

An `ExecutionSlice` is the smallest coherent step that:

- advances an integrated behavior rather than only one technical layer;
- creates an inspectable touchpoint;
- has one accountable integration owner;
- can be reviewed and verified against explicit assertions;
- has containment or rollback behavior;
- identifies temporary scaffolding and its disposition.

A touchpoint may be a CLI operation, API exchange, rendered view, procedure walkthrough, protocol trace, simulation observation, physical measurement, generated package, document review or another domain-appropriate observation.

Do not use a universal line-count ceiling. Slice by change surface, coupling, risk and reviewer cognitive load.

## 6. Relationship among objects

```text
Capability Increment
  -> ImplementationStructureContract when applicable
      -> Execution Slices
          -> Work Units
              -> Exact Candidate / Validation Cohort
```

One slice may require several work units. A work unit may contribute to several slices. The slice owns integrated feedback; the work unit owns bounded execution responsibility.

## 7. Review checks

A structure review should ask:

- Is every consequential behavior located under one clear owner?
- Do key contracts make illegal or ambiguous interactions harder?
- Does the artifact topology reduce or merely relocate complexity?
- Are state lifetime, mutation authority and recovery explicit?
- Are failure and cancellation paths designed, not inferred?
- Do slices expose useful feedback early?
- Is temporary scaffolding named and dispositioned?
- Are fixed decisions no broader than needed?
- Is delegated freedom sufficient for competent implementation?
- Can the actual implementation be compared to the plan without treating harmless private differences as violations?
