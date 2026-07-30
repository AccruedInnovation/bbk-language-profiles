# perf-release-profile

> Design and verify release profiles against an explicit operational objective; do not copy one universal "maximum optimization" block.

## Why It Matters

Cargo profile settings change runtime performance, binary size, startup, link time, incremental build behavior, panic semantics, overflow behavior, and diagnostic quality. The best setting depends on the shipped workload and failure policy. `opt-level = 3`, fat LTO, one codegen unit, panic abort, native CPU targeting, and stripping are independent decisions—not a bundle that every production binary should inherit.

## Procedure

1. Identify the actual artifact and objective: throughput, tail latency, startup, size, memory, diagnostic quality, portability, or build time.
2. Record the current effective profile, Cargo configuration, `RUSTFLAGS`, target, compiler, linker, and workload.
3. Compare one bounded alternative at a time.
4. Measure runtime distribution, binary size, build/link time, resource use, and operational consequences.
5. Preserve a symbols-enabled diagnostic or profiling path when incident response requires it.
6. Adopt only changes supported by repeatable evidence.

## Example Named Profiles

```toml
# Keep the repository's normal release behavior as the baseline.
[profile.release]
opt-level = 2

# An experiment for measured throughput work; not an implied default.
[profile.throughput-experiment]
inherits = "release"
lto = "thin"

# A diagnostic build close to release optimization but retaining symbols.
[profile.production-diagnostic]
inherits = "release"
debug = 1
strip = false
```

A project may choose different settings. `panic = "abort"` changes recovery and destructor behavior; stripping changes diagnostics; target-specific CPU features change portability; LTO and codegen units can materially increase build time; optimization level 3 can be slower than 2 for some workloads.

## Evidence Receipt

Preserve:

- candidate and profile digest;
- rustc/Cargo/linker/target identity;
- exact profile and environment overrides;
- workload and input digest;
- warmup, samples, variance, and resource ceiling;
- current versus proposed results;
- binary size and build/link time;
- diagnostic and failure-policy effects.

## See Also

- [opt-lto-release](opt-lto-release.md)
- [opt-codegen-units](opt-codegen-units.md)
- [opt-pgo-profile](opt-pgo-profile.md)
- [perf-profile-first](perf-profile-first.md)
