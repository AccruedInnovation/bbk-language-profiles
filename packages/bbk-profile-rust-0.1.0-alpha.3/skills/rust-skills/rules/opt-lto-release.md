# opt-lto-release

> Evaluate LTO for a measured release objective; do not assume thin or fat LTO is automatically faster or smaller.

## Why It Matters

LTO can enable cross-crate optimization and dead-code elimination, but it also increases link work and may provide little or negative benefit for a particular workload. Its interaction with codegen units, linker choice, incremental builds, debug information, and binary distribution must be measured.

## Bounded Comparison

```toml
[profile.release]
lto = false

[profile.lto-experiment]
inherits = "release"
lto = "thin"  # or "fat" in a separate experiment
```

Compare one option against the current shipped baseline using the same compiler, target, workload, and environment. Record build/link time, runtime distribution, binary size, memory, startup, and diagnostic effects.

## Selection Guidance

- Use no LTO when build latency or iteration dominates and evidence shows no material runtime loss.
- Consider thin LTO as a bounded trade-off experiment.
- Consider fat LTO only when the measured gain justifies link time and release complexity.
- Libraries normally should not prescribe downstream final-link policy unless the distribution owns that final artifact.

Do not combine LTO, codegen-unit, panic, strip, and target-CPU changes into one experiment; their effects become uninterpretable.

## See Also

- [opt-codegen-units](opt-codegen-units.md)
- [perf-release-profile](perf-release-profile.md)
- [perf-profile-first](perf-profile-first.md)
