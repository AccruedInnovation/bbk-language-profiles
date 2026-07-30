# unsafe-miri-ci

> Use Miri as triggered dynamic evidence for unsafe, aliasing-sensitive, or dependency-boundary behavior when the selected tests and platform are supported.

## Why It Matters

Miri can detect many forms of undefined behavior during interpreted execution, including invalid memory access, uninitialized reads, alignment violations, some data races, and violations of its supported aliasing/provenance models. It is especially valuable for raw-pointer code, manual `Send`/`Sync`, custom allocation, and small FFI-adjacent components that can run under Miri.

A passing run is not a proof of soundness. It covers only the executed paths, selected configuration, dependencies, and Miri's supported environment. Safe local code may still exercise unsafe dependencies, while some system, FFI, async-runtime, or platform interactions may be unsupported.

## Triggered Gate

```yaml
trigger_any:
  - unsafe block or unsafe function changed
  - raw pointer or manual Send/Sync changed
  - custom allocator or aliasing invariant changed
  - a safe wrapper's contract over unsafe internals changed
requirements:
  - project-qualified nightly and Miri component
  - bounded compatible test subset
  - preserved toolchain, command, flags, and failures
```

Example, only after the project has qualified the toolchain and target:

```bash
cargo miri test -p my-crate --lib
```

Do not install a nightly, add Miri, change dependencies, or broaden the test surface silently. If the assurance contract requires Miri and the supported toolchain is unavailable, return `BLOCKED`. If Miri is merely recommended and unavailable, record an advisory and choose another adequate technique.

## Interpretation

- Reproducible Miri-detected undefined behavior is a critical correctness finding.
- An unsupported operation or tool failure is `BLOCKED` or `ERROR`, not a candidate failure.
- A passing targeted run is supporting evidence only.
- Preserve the exact test selection, `MIRIFLAGS`, toolchain identity, target, and any minimized reproducer.

## Complementary Methods

Use a documented safety argument and focused code review in all cases. Add sanitizers, Loom, fuzzing, ABI fixtures, or platform tests when they cover distinct risks. Do not run every technique merely because unsafe code exists.

## See Also

- [unsafe-safety-comment](unsafe-safety-comment.md)
- [unsafe-send-sync-manual](unsafe-send-sync-manual.md)
- [test-loom-concurrency](test-loom-concurrency.md)
