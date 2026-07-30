---
name: go-skills
description: Apply practical, applicability-aware Go implementation and review guidance. Use for ordinary Go code changes after repository module, workspace, toolchain, target, tag, and assurance context are known.
---

# Go Skills

Use repository policy first. These are defaults and review prompts, not universal laws.

## Package and module design

- Keep packages cohesive around one responsibility or domain capability; avoid `util`, `common`, `helpers`, and cycle-breaking grab bags.
- Prefer a small exported surface and substantial hidden implementation. Export only contracts intended for external package use.
- Define interfaces where substitution, independent ownership, or testing boundaries justify them. Interfaces often belong near consumers, but public extension points and shared contracts may warrant provider-owned interfaces.
- Return concrete types ordinarily. Return interfaces when the public contract genuinely requires abstraction.
- Keep `internal/` boundaries intentional. Avoid package cycles by repairing responsibility direction rather than creating an arbitrary shared package.
- Treat module paths, `/v2` major-version suffixes, `go` and `toolchain` directives, and `replace` entries as compatibility and release decisions.

## Types, zero values, nil, and ownership

- Define whether zero values are useful, invalid, or require construction; enforce the contract consistently.
- Distinguish nil interfaces from interfaces containing typed nil pointers.
- Account for nil maps, slices, channels, functions, and pointers having different legal operations.
- Choose pointer or value receivers from identity, mutation, method set, copy safety, aliasing, and measurement—not a universal size threshold.
- Never copy values containing `sync.Mutex`, `sync.RWMutex`, `sync.Once`, `sync.Cond`, atomics, or other no-copy state after first use.
- Make slice aliasing and capacity-sensitive `append` behavior explicit when ownership crosses boundaries.
- Do not depend on map iteration order unless it is sorted or otherwise normalized.
- Use generics when they remove meaningful duplication without obscuring domain semantics; do not use type parameters as an abstraction trophy.

## Errors and panics

- Add actionable context at boundaries without duplicating noise at every stack frame.
- Use `%w` only when callers are intentionally allowed to inspect the underlying error through `errors.Is` or `errors.As`; wrapping may expose an implementation contract.
- Preserve sentinel or concrete error identity only when it is part of the API.
- Distinguish temporary, retryable, permanent, validation, authorization, conflict, and partial-success outcomes where callers need different behavior.
- Check meaningful close, flush, commit, and write errors. `defer` is the normal cleanup mechanism after successful acquisition, but explicit close may be necessary in loops or when ordering/error handling matters.
- Do not use panic for ordinary expected errors. Define explicit invariant, startup, callback, goroutine, HTTP/RPC, and process-boundary panic policy.

## Context and cancellation

- Pass `context.Context` explicitly as the first parameter for request-scoped work; do not store it in long-lived objects by default.
- Propagate cancellation and deadlines through I/O, database, subprocess, and child work.
- Check cancellation in loops and before expensive or irreversible steps where appropriate.
- Domain arguments remain explicit. Context values are reserved for genuinely request-scoped cross-API metadata such as trace or authentication identity, not arbitrary business state.
- Define what partial effects remain after cancellation and who cleans them up.

## Goroutines, channels, and synchronization

For every goroutine, establish owner, count bound, cancellation, join/wait behavior, error path, and resource cleanup.

- A blocked goroutine is not garbage collected merely because nobody references it.
- Define who sends, receives, closes, and handles blocked operations for each channel.
- Buffered and unbuffered channels are both valid; assess the protocol, backpressure, cancellation, and shutdown semantics.
- Avoid sending on or closing a channel from multiple uncoordinated owners.
- Protect shared invariants with the simplest correct synchronization. Channels are for communication and ownership transfer; mutexes and atomics are appropriate for protected shared state.
- Define lock ordering, atomic multi-field invariants, `WaitGroup` sequencing, timer/ticker cleanup, worker-pool bounds, and retry behavior.
- Treat race freedom and logical concurrency correctness as separate assertions.

## I/O and resource boundaries

- Close HTTP response bodies, database rows, files, pipes, and other resources after successful acquisition.
- Bound untrusted reads and decompression. Validate paths, archive entries, destinations, redirects, and subprocess arguments.
- Use `exec.CommandContext` for cancellable subprocesses; define process-tree cleanup, stream backpressure, environment, working directory, and exit/signal interpretation.
- For files, define atomic write, permissions, durability expectations, rename behavior, symlink handling, and interruption cleanup.
- For `database/sql`, check `Rows.Err`, transaction `Commit`, rollback fallback, context cancellation, pool limits, NULL semantics, and idempotency/retry behavior.

## HTTP and RPC

- Set server and client timeout policies intentionally. Bound request bodies and response sizes.
- Close and reuse response bodies correctly. Define redirect, proxy trust, TLS, forwarded-header, and SSRF policies.
- Test transport-level behavior separately from handler-only behavior where streaming, cancellation, TLS, connection reuse, or graceful shutdown matters.
- Keep middleware dependencies and error behavior explicit; request context should not become a hidden service locator.

## Testing

- Use package tests, external-package tests, integration tests, subprocess tests, real HTTP servers, database fixtures, and platform tests according to the assertion.
- Use `t.Cleanup`, `t.TempDir`, and `t.Setenv` to restore process state.
- Ensure parallel tests do not share mutable globals, ports, directories, environment, clocks, or database state unsafely.
- Preserve seeds and failing inputs for fuzz, shuffled, property, and randomized tests.
- Treat cached results, retries, flaky outcomes, race results, and coverage honestly.

## Performance

Measure first. Preserve correctness under the measured workload.

- Consider allocation, escape, cache locality, GC, contention, scheduler behavior, I/O, and operational limits.
- Preallocate only when size knowledge and evidence justify it.
- Preserve PGO profile provenance and include it in build identity.
- Benchmark end-to-end behavior when microbenchmarks omit meaningful I/O, contention, or lifecycle cost.

## Tool and effect discipline

Do not install analyzers, modify the toolchain, run networked dependency acquisition, alter `go env`, or change module files merely because this skill mentions a technique. Required absent capabilities are `BLOCKED`; optional techniques remain advisory.

## Implementation structure

For alpha.4 work, apply the Go type-depth test before adding abstractions. Defined types, structs, typed constants, interfaces, generics, errors, and wrappers are justified only when they protect a material invariant, clarify ownership, stabilize a boundary, improve change locality, create a real seam, or hide consequential complexity.

Make package ownership and runtime lifetime explicit. A goroutine, channel close, context cancellation, timer, ticker, pool, lock, process, file, socket, transaction, and retry loop must have an accountable owner and termination/recovery behavior. Static Go typing does not prove those runtime facts.

