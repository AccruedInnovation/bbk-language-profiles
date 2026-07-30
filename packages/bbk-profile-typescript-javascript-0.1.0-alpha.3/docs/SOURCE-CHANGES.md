# Source changes and exact predecessor binding

## Immutable predecessor

`bbk-profile-typescript-javascript 0.1.0-alpha.3` is an immutable additive successor to the exact alpha.2 package:

```text
archive SHA-256:      b5391b4d4c1c96f5e8acdd12b9063b34d2e1efc105dd788c706681b7daa29c5a
package-root SHA-256: e56a1d0e90bf1848b02332e381e2416067b998226cc53f7e98758be26a63fdf5
version:              0.1.0-alpha.2
```

The alpha.2 archive is not edited in place. Alpha.2 and alpha.3 install side by side and retain distinct package and lock identities.

## Preserved without semantic change

- all 13 shipped skill files are byte-identical to alpha.2;
- all existing skill IDs and direct standalone skill use;
- existing `preflight`, `resolve`, `gate_plan`, `structure`, `slice`, and `structure_review` entrypoints and output dialects;
- existing gate recipes, procedure routing, installer ownership/backup safeguards, package-integrity checks, and qualification boundaries;
- existing alpha.2 locks and evidence remain bound to the alpha.2 package digest.

## Additive alpha.3 changes

- minimum BBK version raised to `0.1.0-alpha.8`;
- exact `bbk.profile-capability.v1` request/result dispatch for `state-effect`, `state-effect-inventory`, `state-effect-review`, `review-context`, `review-lens`, and `evidence-adapter`;
- exact package-root, canonical profile-manifest, source-tree, request, input, subject, and authority fencing;
- profile-specific State–Decision–Effect projection, inventory, planned/actual review, proportional `NONE` / `INLINE` / `CONTRACT` routing, and shadow/ambient-state findings;
- focused Review Assurance lens routing and bounded `bbk.review-context-manifest.v1` generation;
- validator-compatible `bbk.evidence-receipt.v2` adaptation without invented evidence fields;
- six copied alpha.8 normative schemas, profile-specific operation schemas, mappings, fixtures, tests, OMP-adjacent tools/commands, migration guidance, limitations, and qualification planning;
- package tests retargeted only where the immutable successor version and additive OMP surface must be asserted.

No alpha.2 skill file was rewritten. Generic BBK remains authoritative for the State–Decision–Effect design, AssuranceContract, review manifest, evidence eligibility, findings, aggregation, locks, readiness, release, and Blueprint adoption.

## Controlling inputs

- update PRD: `sources/bbk-profile-typescript-javascript-0.1.0-alpha.3-update-prd.md` when present, otherwise the preserved alpha.3 update PRD under `sources/`;
- exact predecessor archive and package-root digests above;
- supplied BBK `0.1.0-alpha.8` schemas and profile dispatch behavior.

The exact shipped file set and every file digest are recorded in `PACKAGE-MANIFEST.json`.
