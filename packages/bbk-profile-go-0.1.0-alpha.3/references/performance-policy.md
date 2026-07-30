# Go performance policy

Performance findings require an explicit assertion, workload, environment, and evidence.

Do not infer performance from folklore such as “pointers are faster,” “goroutines are free,” or “preallocate everything.” Account for allocation, escape, aliasing, cache behavior, scheduler effects, GC, I/O, contention, and operational limits.

For material claims preserve:

- exact Go version, target, tags, CGO mode, PGO profile, and build flags;
- benchmark workload and dataset;
- samples, variance, and comparison method;
- CPU and memory environment;
- profiles and traces where applicable;
- correctness checks preventing optimized-but-wrong results.

PGO input is a build dependency. Record its digest and provenance; do not let an unnoticed `default.pgo` silently change candidate identity.
