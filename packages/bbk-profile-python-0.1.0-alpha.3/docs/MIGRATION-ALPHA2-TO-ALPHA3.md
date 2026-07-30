# Migration from alpha.2 to alpha.3

`0.1.0-alpha.3` is an immutable additive successor requiring BBK `0.1.0-alpha.8`. Install it beside alpha.2, rerun profile resolution, inspect the typed dispatch result, and deliberately update project locks. Existing alpha.2 locks and evidence remain bound to their original package digest.

All alpha.2 skill IDs and direct skill contents are retained. Existing preflight, resolve, gate-plan, structure, slice, and structure-review interfaces remain available.
