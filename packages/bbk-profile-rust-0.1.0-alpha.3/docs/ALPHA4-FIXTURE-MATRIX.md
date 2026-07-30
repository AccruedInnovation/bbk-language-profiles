# Rust alpha.4 fixture matrix

| Fixture | Expected behavior |
|---|---|
| Routine internal refactor | No standalone contract reviewer; ordinary alpha.1 behavior |
| Public crate API | Structure projection and focused review selected |
| Async cancellation/resource ownership | Ownership, failure, and slice guidance selected |
| Persistence migration | Migration, recovery, evidence, and consumer obligations selected |
| Unsafe/FFI boundary | Unsafe/ABI contracts and focused review selected |
| Public consumer slice | Real consumer touchpoint and exact dependency closure |
| Migration rehearsal slice | Reversible migration touchpoint and evidence |
| Harmless private module divergence | `CONFORMS` or advisory, never material solely from private shape |
| Fixed public/ownership divergence | `MATERIAL_DIVERGENCE` with exact reference |
| Invalid contract | Schema/input failure, not invented confidence |
| Legacy alpha.1/alpha.3 profile | `legacy-unprojected` under alpha.4 |
| Broad survey | Does not automatically load every structure specialist |
