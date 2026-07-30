# opt-codegen-units

> Treat codegen-unit count as a build-time/runtime trade-off and change it only with measured evidence.

## Why It Matters

Cargo can split a crate into several LLVM code-generation units to improve parallel build time. Fewer units may expose more optimization opportunities inside the crate, while increasing compile time and memory use. The magnitude and direction of the runtime effect are workload- and compiler-dependent.

## Bounded Experiment

```toml
[profile.release]
# Repository baseline remains authoritative.

[profile.cgu-experiment]
inherits = "release"
codegen-units = 1
```

Measure the current profile against one alternative. Keep LTO, optimization level, target CPU, linker, workload, and source candidate unchanged. Record build/link time, peak memory, runtime distribution, and binary size.

## Guidance

- Do not assert that one unit is universally best for production.
- Do not maximize dev codegen units blindly; incremental and dependency behavior matter.
- Re-evaluate after material compiler, crate-graph, or workload changes.
- Prefer the repository's current setting when no material performance assertion exists.

## See Also

- [opt-lto-release](opt-lto-release.md)
- [perf-release-profile](perf-release-profile.md)
- [perf-profile-first](perf-profile-first.md)
