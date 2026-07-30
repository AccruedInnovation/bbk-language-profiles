# Boundaries

## Authority

The Python profile is a procedure and evidence-planning package. It does not own BBK semantic state and cannot grant authority.

The following remain false in `PROFILE.json`:

```json
{
  "may_declare_pass": false,
  "may_expand_work_scope": false,
  "may_grant_tools_or_effects": false,
  "may_reduce_assurance": false
}
```

## Generic versus profile-specific state

The generic `ImplementationStructureContract` and `ExecutionSlice` remain the source of truth. Profile output is a deterministic view under `python` vocabulary. It may not silently alter:

- object identity or revision;
- baseline or scope references;
- fixed decisions;
- delegated freedom;
- prohibited shortcuts;
- work-unit membership;
- assertions or assurance;
- approval or acceptance.

## Static versus runtime truth

Python annotations and type-checker results establish configured static assertions only. They do not prove runtime validation, resource lifetime, process safety, cancellation, persistence, packaging, or operational correctness.

## Structure-review boundary

`CONFORMS` means only that the inspected consequential shape did not materially diverge under the supplied evidence. It is not a verification or release pass.

The reviewer must not fail:

- private helper names;
- equivalent private module placement;
- local iteration strategy;
- private test utility layout;
- another internal representation inside delegated freedom that preserves the fixed contracts and quality.

## Supported subject boundary

Primary qualification covers ordinary Python libraries, CLIs, applications, services, asyncio code, pyproject-based distributions, and sdist/wheel subjects. Conditional or partial areas are listed in `docs/SUPPORT-MATRIX.md`.
