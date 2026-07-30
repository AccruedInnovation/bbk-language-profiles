# Known limitations

`bbk-profile-go 0.1.0-alpha.3` is a statically and mock-qualified profile package requiring BBK `0.1.0-alpha.8` or a compatible successor. Its structure/slice outputs use the contract dialect introduced in core alpha.4; it is not an execution authority.

## Live environments not universally qualified

The release does not claim live compatibility with every:

- Go patch release, `GOOS`/`GOARCH`, architecture tuning level, build tag set, or `GODEBUG`/`GOEXPERIMENT` setting;
- CGO compiler, linker, native library, ABI, sanitizer, or cross-compilation environment;
- OMP release or host event payload;
- repository-specific formatter, linter, generator, vulnerability scanner, test runner, package proxy, or release system;
- downstream consumer, deployment platform, database, message broker, or operational environment.

## Static projection limits

Source inventory and type notation cannot prove:

- goroutine termination, race freedom, ordering, backpressure, cancellation, or shutdown correctness;
- runtime input validation, wire semantics, persistence durability, migration correctness, or recovery;
- CGO pointer lifetime, foreign ABI correctness, assembly behavior, or native resource ownership;
- module releasability, downstream compatibility, binary reproducibility, deployment safety, or operational outcomes.

These require the applicable deterministic tools, consumer fixtures, focused reviews, simulations, human review, or operational evidence.

## Partial subjects

Mixed subjects receive only a bounded Go projection. TinyGo, embedded, eBPF, mobile, specialized WASM, plugins, custom compiler forks, and unusual shared-library modes remain partial or unqualified.

## Review limits

Planned/actual review compares fixed decisions and consequential realization shape. It intentionally does not enforce exact equality for private files, helper names, local test utilities, or other details left within delegated freedom. Missing evidence at consequential or critical tiers is `BLOCKED`, not inferred as conformance.
