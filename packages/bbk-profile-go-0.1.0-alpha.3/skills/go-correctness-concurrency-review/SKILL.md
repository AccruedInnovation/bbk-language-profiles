---
name: go-correctness-concurrency-review
description: Review Go correctness, goroutine lifecycle, cancellation, channels, synchronization, nil and aliasing behavior, persistence, retry, and failure recovery against exact candidate assertions.
---

# Go Correctness and Concurrency Review

Review one exact candidate and assigned behavioral assertions. Do not repair it.

## State and failure model

Establish:

- owned mutable state and invariants;
- operation preconditions, success, partial success, failure, retry, cancellation, and recovery;
- durable versus in-memory state;
- idempotency and duplicate behavior;
- transaction and external-effect boundaries;
- panic, process-exit, restart, and shutdown behavior.

## Goroutine lifecycle

For every material goroutine determine:

```text
owner
creation trigger
maximum count
cancellation source
wait/join owner
error destination
resource ownership
shutdown behavior
whether it may outlive its parent
```

Flag unbounded spawning, detached work without policy, ignored errors, leaked timers/tickers, child work escaping cancellation, goroutines retained by blocked I/O, and shutdown that returns before owned work is contained.

## Channels and backpressure

Review:

- send/receive and close ownership;
- nil-channel behavior;
- blocked send/receive and cancellation;
- buffer rationale and overload policy;
- fan-in/fan-out completion;
- send-after-close or concurrent close;
- dropped, duplicated, or reordered work;
- queue growth and memory pressure.

Buffered and unbuffered channels can both be correct. Judge the protocol.

## Synchronization

Review:

- mutex ownership and lock order;
- values copied after locks/atomics/conditions/once state are used;
- `WaitGroup` add/wait ordering;
- condition predicates and wake loops;
- `sync.Once` behavior after panic or partial initialization;
- atomic ordering and multi-field invariants;
- concurrent maps, slices, caches, and publication;
- race-free but logically invalid interleavings.

## Context, time, and cancellation

- Is context propagated to I/O, database, network, and subprocess work?
- Are deadlines and cancellation causes preserved?
- Are loops, retries, timers, and backoff cancellation-aware?
- What partial effects remain when cancellation wins?
- Does test time depend unnecessarily on wall-clock sleeps?
- Are fake clocks or `testing/synctest` appropriate and supported?

## Go semantic hazards

Review:

- typed nil inside non-nil interfaces;
- nil map, slice, channel, function, and pointer behavior;
- zero-value validity;
- slice aliasing, capacity, and `append` ownership;
- map iteration nondeterminism;
- value/pointer receiver method sets;
- copying aliased slices/maps or synchronization state;
- defer argument evaluation and cleanup ordering;
- partial reads/writes;
- integer overflow or narrowing;
- JSON nil/empty, unknown, duplicate, and precision behavior;
- monotonic versus wall-clock time assumptions.

## Persistence and effects

- transaction ownership and isolation;
- commit ambiguity, rollback fallback, and retry safety;
- `Rows.Close`/`Rows.Err` and resource cleanup;
- atomic file update, permissions, flush/durability, rename, symlink, and interruption behavior;
- exactly-once versus at-least-once external effects;
- restart reconciliation after partial completion.

## Evidence selection

Use only methods required by the assertion:

- focused deterministic tests;
- race-enabled tests and representative workloads;
- `testing/synctest` for controlled time/contained goroutines when supported;
- state-machine, property, differential, or metamorphic tests;
- deterministic failpoints and restart tests;
- goroutine dumps, traces, or profiles;
- real database, filesystem, subprocess, or network fixtures.

A passing race run covers only executed paths. A passing unit test does not prove shutdown, platform, transport, or restart behavior.

## Return

For each assertion, return expected and observed behavior, a concrete failure scenario, evidence, reproducibility, severity, confidence, affected state/effects, and the smallest next disposition. Preserve `BLOCKED`, `ERROR`, `INCONCLUSIVE`, and `FLAKY` distinctly.

## Structure-contract integration

Treat state, goroutine, channel, context, timer, synchronization, shutdown, retry, effect, and recovery ownership as planned realization shape when the contract fixes it. A material divergence names the exact fixed decision or ownership record. A passing race run does not by itself establish lifecycle conformance.

