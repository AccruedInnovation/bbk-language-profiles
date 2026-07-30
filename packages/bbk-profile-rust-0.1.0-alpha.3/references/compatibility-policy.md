# Rust compatibility policy

Compatibility claims are scoped and directional. Select only the dimensions implicated by the work:

- source/public API and SemVer;
- trait implementation and generic/lifetime behavior;
- feature-set behavior;
- target-specific API;
- serialized or wire representation;
- persistent state and migration;
- configuration and environment;
- CLI syntax, output, exit status, and automation behavior;
- operational behavior and rollout/rollback.

A static API tool is one evidence source, not the authority. Pin its version with the toolchain, distinguish tool failure from a detected break, test relevant feature/target configurations, and supplement with downstream compile fixtures and behavioral contracts.
