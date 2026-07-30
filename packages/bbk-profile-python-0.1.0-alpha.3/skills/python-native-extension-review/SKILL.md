---
name: python-native-extension-review
description: Review Python native-extension and FFI boundaries including CPython C API, Cython, cffi, ctypes, PyO3/maturin, reference ownership, GIL/thread state, free threading, buffers, callbacks, ABI, shared libraries, and wheel tags.
---

# Python Native Extension Review

Use only when native or foreign code is present or materially affected.

## Bind the boundary

Identify:

- implementation technology and source;
- CPython/PyPy or other supported interpreters;
- Python versions, ABI or limited-API claims, architectures, and platforms;
- build backend and native toolchain;
- wheel tags and shared-library dependencies;
- GIL-enabled and free-threaded support claims;
- exact candidate and assertions.

## Memory and object lifetime

Review:

- owned versus borrowed references;
- reference increments/decrements and failure paths;
- partial initialization and cleanup;
- callback and capsule lifetime;
- buffer-protocol ownership and mutation;
- allocator consistency across boundaries;
- object retention, cycles, weak references, and interpreter shutdown;
- Rust/PyO3 or C++ ownership translation.

## Exceptions and callbacks

Inspect:

- exception creation, preservation, and return conventions;
- foreign exceptions or panics crossing the Python boundary;
- callbacks into Python and reentrancy;
- thread affinity and interpreter state;
- failure cleanup and partial external effects.

## GIL, threads, and free threading

Review:

- GIL acquisition/release and blocking calls;
- thread-state ownership;
- shared global/module state;
- explicit synchronization under free threading;
- extension declarations and fallback behavior;
- subinterpreter and module-state support;
- callback concurrency and finalization.

Do not claim free-threaded support because a GIL build passes.

## ABI and distribution

Inspect:

- stable ABI or `abi3` claims;
- CPython API use inconsistent with the declared ABI;
- exported symbols and shared-library lookup;
- platform and architecture wheel tags;
- bundling or external dependency assumptions;
- debug/release build differences;
- source distribution ability to build on claimed platforms;
- generated binding drift.

## Validation

Select applicable evidence:

- clean native build and wheel install;
- import and smoke tests on claimed Python/platform combinations;
- debug-build or reference-leak checks where available;
- native sanitizers with a qualified toolchain;
- crash and callback tests;
- free-threaded and subinterpreter tests where claimed;
- buffer lifetime and concurrent access fixtures;
- ABI and shared-library inspection;
- wheel-content and tag verification.

Passing one local build is not cross-platform or ABI qualification. Return exact unsupported configurations, evidence gaps, memory/threading hazards, package implications, and the smallest safe repair and revalidation plan.
