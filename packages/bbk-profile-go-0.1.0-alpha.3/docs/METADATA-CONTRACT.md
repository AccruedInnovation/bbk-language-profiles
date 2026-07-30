# Version and contract-dialect metadata

This package has three distinct version identities:

| Identity | Value | Meaning |
|---|---|---|
| Profile package | `0.1.0-alpha.3` | The independently manifested `bbk-profile-go` release. |
| Minimum compatible BBK core | `0.1.0-alpha.8` | The minimum core required for typed profile discovery and dispatch. Compatible successors are allowed. |
| Structure/slice contract dialect | `0.1.0-alpha.4` | The BBK release lineage that introduced the generic `ImplementationStructureContract` and `ExecutionSlice` formats used by these projections. |

The legacy `bbk_version` field in structure, slice, inventory, comparison, or review projection outputs identifies the **contract dialect**, not the installed BBK core version and not the minimum compatibility version. New integrations should use `PROFILE.json.contract_dialects` rather than infer compatibility from that legacy field.

Typed State–Decision–Effect and Review Assurance operations use `bbk.profile-capability.v1`, introduced in BBK `0.1.0-alpha.8`.

Current-release metadata must agree across `VERSION`, top-level `PROFILE.json.version`, `PROFILE.json.requires.bbk_minimum`, the current-release block in `README.md`, and `omp/extension/package.json`. Historical predecessor and source-lineage records deliberately retain their original versions.
