# Known limitations

- Static inventory is intentionally bounded and cannot infer every macro expansion, cfg-selected item, generated artifact, runtime registration, or downstream consumer.
- Planned-versus-actual comparison depends on the completeness of the supplied candidate manifest and inventory.
- Structure projection does not run Cargo unless a separate bounded tool invocation permits it.
- The profile does not install or qualify Miri, Loom, fuzzers, sanitizers, compatibility tools, audit tools, or `mutest-rs`.
- Performance and memory guidance remains evidence-driven; no universal optimization profile is imposed.
- Mixed non-software obligations are reported as adjacent responsibilities rather than claimed as Rust-owned.
