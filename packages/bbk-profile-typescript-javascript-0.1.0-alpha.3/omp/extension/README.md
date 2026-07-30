# BBK TypeScript/JavaScript OMP extension


Current profile package: `0.1.0-alpha.3`.
Registers tools and commands for the installed `bbk-profile-typescript-javascript` package.

## Tools

- `bbk_tsjs_preflight`
- `bbk_tsjs_resolve`
- `bbk_tsjs_gate_plan`
- `bbk_tsjs_structure`
- `bbk_tsjs_slice`
- `bbk_tsjs_structure_review`

## Commands

- `/bbk:tsjs`
- `/bbk:tsjs:preflight`
- `/bbk:tsjs:gates`
- `/bbk:tsjs:structure <contract.json>`
- `/bbk:tsjs:slice <slice.json>`
- `/bbk:tsjs:structure-review <contract.json> <candidate.json> [actual-inventory.json]`

All profile commands are non-authoritative. Structure and slice commands project generic BBK objects; they do not mutate them or execute planned gates. Structure review returns findings against an exact candidate and does not accept, waive, or repair it.
