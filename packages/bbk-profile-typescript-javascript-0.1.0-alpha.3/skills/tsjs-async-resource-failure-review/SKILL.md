---
name: tsjs-async-resource-failure-review
description: Review promises, event-loop ordering, cancellation, timers, streams, workers, child processes, retries, idempotency, transactions, shutdown, and resource cleanup in TypeScript/JavaScript.
---

# TS/JS Async, Resource, and Failure Review

JavaScript's event loop does not remove concurrency. State can change across `await`, callbacks can race, workers and subprocesses add parallelism, and streams introduce backpressure and partial completion.

## Bind the execution model

Identify:

- runtime and version;
- async frameworks and schedulers;
- request/job/event ownership;
- transaction and persistence boundaries;
- cancellation and timeout mechanisms;
- streams, sockets, workers, child processes, timers, listeners, and other handles;
- retry, duplicate-delivery, and idempotency policy;
- shutdown and restart behavior;
- test scheduler, fake timers, and open-handle diagnostics.

## Promise and callback correctness

Review for:

- floating promises and ignored rejections;
- missing `await` or unintended sequentialization;
- callback/promise double completion;
- async constructors or initialization ordering;
- catch-and-log paths that lose failure;
- `Promise.all` partial effects and cancellation assumptions;
- `Promise.race` losers that continue running;
- result ordering assumptions;
- unhandled rejection and uncaught exception policy;
- stale closure state across `await`.

## Cancellation and deadlines

Trace cancellation end to end:

```text
request or parent signal
  → operation
  → nested calls
  → stream / worker / process / database call
  → cleanup
  → durable state after interruption
```

Check:

- `AbortSignal` propagation;
- timeout versus cancellation classification;
- cleanup handlers and listener removal;
- cancellation after partial side effects;
- late results after caller abandonment;
- whether retries respect the original deadline;
- whether cancellation can interrupt a critical commit and what state remains.

A timeout wrapper that stops waiting but leaves work running is not full cancellation.

## Streams and backpressure

Inspect:

- producer/consumer rate mismatch;
- ignored write return values;
- missing drain or pipeline completion handling;
- partial reads/writes;
- premature close and destroy semantics;
- error propagation across pipeline stages;
- cancellation and listener cleanup;
- memory buffering limits;
- object-mode assumptions;
- browser/Node/Web stream adaptation.

## Resources and lifecycle

Review ownership and cleanup of:

- timers and intervals;
- event listeners and subscriptions;
- sockets, files, database clients and transactions;
- workers and child processes;
- locks or distributed leases;
- caches and retained closures;
- test fixtures and temporary resources.

Every resource should have a clear owner and terminal cleanup path for success, failure, cancellation, timeout, and shutdown.

## State, retries, and durability

Check:

- state changes split by `await` without conflict control;
- duplicate messages or webhooks;
- retrying non-idempotent operations;
- lost acknowledgement windows;
- transaction scope and external calls inside transactions;
- partial batch success;
- restart/replay behavior;
- consistency of cache and durable state;
- optimistic concurrency and stale writes;
- compensation versus complete-forward recovery.

## Testing

Use applicable methods:

- deterministic fake clocks plus selected real-time tests;
- forced cancellation at each material boundary;
- duplicate and out-of-order delivery;
- stream backpressure and consumer failure;
- worker/process crash and late result;
- retry exhaustion and partial success;
- restart with persisted state;
- property or model-based state-machine tests;
- open-handle and resource-leak checks;
- fault injection around transactions and external effects.

Do not let fake timers become the only evidence for behavior dependent on real scheduler or I/O semantics.

## Output

Report ownership, cancellation, completion, durable-state, retry, and cleanup assertions separately. Classify findings as promise lifecycle, race/order, cancellation, backpressure, resource leak, retry/idempotency, transaction/durability, shutdown/recovery, or evidence gap.

## Implementation-structure projection

For alpha.4 contracts, compare planned and actual ownership of promises, AbortSignals, timers, listeners, subscriptions, streams, workers, child processes, transactions, caches, and shutdown. Moving an internal helper is harmless; changing who starts, cancels, joins, drains, retries, commits, or cleans a resource is normally material.
