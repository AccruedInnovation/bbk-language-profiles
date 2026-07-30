# BBK Rust profile — OMP extension

This optional extension exposes the installed `bbk-profile-rust 0.1.0-alpha.2` deterministic CLI through OMP. It plans profile components and gates and projects generic BBK structure/slice objects. It does not install Rust tools, run Cargo gates by default, grant effects, or mark work passed.

Commands:

- `/bbk:rust [hint ...]`
- `/bbk:rust:preflight [run-tools]`
- `/bbk:rust:gates [routine|material|consequential|critical]`
- `/bbk:rust:structure <contract path>`
- `/bbk:rust:slice <slice path>`
- `/bbk:rust:structure-review <contract/candidate arguments>`

Tools:

- `bbk_rust_preflight`
- `bbk_rust_resolve`
- `bbk_rust_gate_plan`
- `bbk_rust_structure`
- `bbk_rust_slice`
- `bbk_rust_structure_review`

The extension finds a project-local profile first, then the user-level profile. `BBK_PROFILE_RUST_ROOT` or `BBK_RUST_CLI` may pin an explicit installation. Generic contracts and slices remain authoritative; OMP output is a projection.
