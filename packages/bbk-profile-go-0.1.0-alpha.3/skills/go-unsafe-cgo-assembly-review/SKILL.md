---
name: go-unsafe-cgo-assembly-review
description: Review Go unsafe pointers, cgo, assembly, callbacks, ABI, native libraries, compiler/runtime directives, and qualified dynamic checks against exact boundary assertions.
---

# Go Unsafe, cgo, Assembly, and ABI Review

Use only when the candidate contains or affects `unsafe`, `import "C"`, assembly, foreign callbacks, native libraries, custom build modes, or material `//go:` directives.

## Boundary inventory

Record:

- all `unsafe` imports and pointer conversions;
- cgo preambles and generated bindings;
- C/C++/assembly sources and libraries;
- exported or imported symbols and calling conventions;
- callbacks in both directions;
- compiler/runtime directives such as `//go:linkname`, `//go:nosplit`, `//go:noescape`, and export directives;
- target, CGO mode, Go compiler, C compiler, linker, flags, and native versions.

## Pointer and lifetime rules

Review:

- `unsafe.Pointer` conversion chains and arithmetic;
- pointer provenance and object liveness;
- `runtime.KeepAlive` placement;
- pinning and whether foreign code retains Go pointers;
- Go pointers stored in C memory;
- `runtime/cgo.Handle` ownership and deletion;
- C pointers retained by Go and their allocation lifetime;
- slices/strings mapped across foreign memory;
- moving, resizing, or freeing memory while referenced.

## Ownership and cleanup

Define who allocates, frees, closes, and invalidates every cross-boundary resource. Ensure allocator pairs match. Review callbacks after owner shutdown, finalizer assumptions, thread affinity, TLS, blocking foreign calls, and cancellation.

## Panic, signal, and thread behavior

Define behavior when Go or foreign code panics, throws, aborts, signals, blocks, or calls back on foreign threads. Do not let a panic cross a boundary whose ABI cannot support it. Review process-wide signal and runtime interaction.

## Layout and ABI

Review:

- struct size, alignment, padding, endianness, and integer width;
- unions, bitfields, packed data, enums, and ownership flags;
- assembly ABI, stack maps, register use, and runtime expectations;
- generated binding drift;
- supported targets and version compatibility;
- public exposure of package-local translated C types.

## Evidence

Choose complementary methods:

- focused unit/integration tests;
- `-gcflags=all=-d=checkptr=2` where supported;
- race-enabled tests for Go-visible concurrency;
- qualified address or memory sanitizers for supported CGO configurations;
- ABI/layout fixtures;
- fuzzing and malformed inputs;
- native leak/resource tests;
- manual invariant review.

No single check proves native-boundary correctness. Passing `checkptr`, race, or sanitizer evidence covers only the exercised configuration.

## Return

Return invariant-by-invariant disposition, exact toolchains/target, evidence, unsupported configurations, concrete failure scenario, severity, confidence, and required repair or containment. Do not mark ordinary tests as proof of ABI or pointer safety.
