# BBK Go profile — OMP extension


Current profile package: `0.1.0-alpha.3`.
This optional extension exposes the installed `bbk-profile-go` resolver and alpha.4 structure/slice projection commands through OMP. It does not install tools, run planned gates during resolution, grant effects, broaden scope, reduce assurance, or declare a pass.

Commands:

- `/bbk:go [hint ...]`
- `/bbk:go:preflight [run-tools]`
- `/bbk:go:gates [routine|material|consequential|critical]`
- `/bbk:go:structure <contract.json>`
- `/bbk:go:slice <slice.json>`
- `/bbk:go:structure-review <contract.json> <candidate.json> [actual-inventory.json]`

Tools:

- `bbk_go_preflight`
- `bbk_go_resolve`
- `bbk_go_gate_plan`
- `bbk_go_structure`
- `bbk_go_slice`
- `bbk_go_structure_review`

The extension finds a project-local profile before the user-level profile. `BBK_PROFILE_GO_ROOT` or `BBK_GO_CLI` may pin an explicit installation.
