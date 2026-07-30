---
name: rust-unsafe-ffi-assurance
description: Review or design Rust unsafe, FFI, ABI, raw-pointer, pinning, manual Send/Sync, allocation, callback, and generated-binding boundaries with explicit invariants and proportional evidence.
---

# Rust Unsafe, FFI, and ABI Assurance

Use only when the changed scope or assertion includes unsafe Rust, a foreign boundary, ABI/layout claims, raw pointers, manual thread-safety traits, custom allocation, or generated bindings.

## Contract inventory

For every boundary, identify:

- caller and callee language, target, calling convention, symbol, and ownership;
- value layout, alignment, validity, discriminants, nullability, provenance, and lifetime;
- allocation/deallocation authority and compatible allocator;
- mutation, aliasing, thread affinity, reentrancy, unwind, and callback behavior;
- error representation, cancellation, shutdown, and partial initialization;
- generated binding source, version, command, and drift policy.

## Unsafe invariants

Inspect:

- each `unsafe fn` caller obligation and each unsafe operation's local justification;
- raw-pointer creation, offset, dereference, integer conversion, and provenance assumptions;
- `Pin`, projection, self-reference, and `Unpin` behavior;
- `MaybeUninit`, `ManuallyDrop`, partial initialization, panic paths, and drop order;
- manual `Send`/`Sync` and field changes that could invalidate the proof;
- `repr(C)`, `repr(transparent)`, `repr(packed)`, unions, enum layout, and niche assumptions;
- exported names, `unsafe extern` declarations, calling conventions, and panic/unwind boundaries;
- callbacks retained after return, cross-thread invocation, and teardown races;
- handles, buffers, strings, slices, lengths, and ownership transfer across the boundary.

Missing `// SAFETY:` or `# Safety` text is a reviewability defect. It becomes Critical only when the required invariant is absent, false, or demonstrably permits undefined behavior.

## Evidence selection

Use the cheapest adequate combination:

- static review and small layout/ABI assertions;
- C/Rust or host/guest compile-and-call fixtures;
- generated-binding diff and regeneration receipt;
- targeted Miri where supported;
- sanitizer builds on qualified targets;
- fuzzing for untrusted boundary inputs;
- Loom or deterministic concurrency tests for callback/shared-state ordering;
- fault tests for partial initialization, panic, cancellation, unload, and double-free paths.

A passing dynamic tool is evidence, not proof. Unsupported tool behavior is `BLOCKED` or `ERROR`, not a candidate failure.

## Required return

For each assigned assertion, return the exact boundary, invariant, evidence, failure scenario, consequence, confidence, remediation, regression test, and disposition. Do not broaden into a general crate review.
