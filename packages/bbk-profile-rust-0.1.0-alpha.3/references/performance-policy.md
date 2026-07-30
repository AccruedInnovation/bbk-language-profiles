# Rust performance policy

Performance guidance is activated by an explicit objective or measured hotspot. Do not treat allocation reduction, smaller types, alternate collections, inline attributes, LTO, codegen units, PGO, panic policy, stripping, native CPU targeting, or optimization level as universal improvements.

A valid comparison holds candidate, toolchain, target, workload, and unrelated settings constant; records distributions rather than one number; includes build/link time, binary size, memory, startup, diagnostic, portability, and failure-policy consequences; and states the operational significance of the observed difference.

Performance evidence expires when the workload, compiler, target, architecture, profile, or materially relevant dependency changes.
