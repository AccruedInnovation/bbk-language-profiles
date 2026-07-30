---
name: python-runtime-correctness-review
description: Review Python runtime behavior, state mutation, exceptions, resources, async cancellation, threads, processes, time, data representation, persistence, retries, and recovery against exact assertions.
---

# Python Runtime Correctness and Failure Review

Use for stateful behavior, async services, retries, persistence, transactions, concurrency, resource ownership, data conversion, or failure/recovery changes.

## Bind the execution model

Identify:

- exact candidate and assertions;
- supported interpreter/version/platform;
- sync, `asyncio`, thread, process, subinterpreter, or free-threaded execution;
- persistent and external systems involved;
- timeout, retry, cancellation, idempotency, and recovery contracts;
- resource and transaction ownership.

## State and mutation

Inspect:

- mutable defaults and class/module shared state;
- aliasing and in-place mutation across boundaries;
- cache key, lifetime, invalidation, synchronization, and reset;
- descriptors, properties, dataclass/model defaults, lazy initialization, and monkeypatching;
- partial state after exceptions or cancellation;
- copy/deep-copy and serialization semantics;
- object finalization, weak references, and shutdown ordering.

## Exceptions and warnings

Check:

- coherent domain and boundary exception taxonomy;
- bare re-raise versus translated exception with explicit cause;
- swallowed or misleading errors;
- cleanup in `finally` and context managers;
- exception groups and task/process aggregation;
- warnings and deprecation policy;
- retry classification, backoff, limits, and terminal failure;
- public exception compatibility.

## Async correctness

Inspect:

- blocking calls in the event loop;
- ownership and lifetime of every created task;
- structured concurrency and task-group semantics;
- cancellation propagation and swallowed cancellation;
- cleanup under cancellation;
- timeout placement and nested timeout behavior;
- async generator and async context-manager finalization;
- executor handoff and context propagation;
- event-loop shutdown and pending tasks;
- retry/idempotency under cancellation or disconnect.

## Threads and free threading

Do not rely on “the GIL makes this safe.” Inspect:

- shared mutation and explicit synchronization;
- compound operations, lazy caches, callbacks, finalizers, and reentrancy;
- lock ordering and shutdown;
- native extension declarations and behavior;
- free-threaded compatibility only when claimed or required.

## Processes and pools

Inspect:

- start method and platform;
- import-safe process entry;
- picklability and serialization;
- inherited descriptors/resources;
- child initialization, signals, logging, and environment;
- queue/pipe/pool shutdown;
- worker crashes, duplicate work, partial effects, and retries;
- shared memory and semaphore cleanup.

## Time, text, numbers, and paths

Check:

- wall-clock versus monotonic time;
- timezone-aware values and daylight-saving transitions;
- locale and encoding;
- Unicode normalization;
- bytes/text boundaries;
- float/decimal/integer precision and units;
- path normalization, case sensitivity, symlinks, UNC and long paths;
- missing/null/default distinctions;
- ordering assumptions exposed outside the process.

## Persistence and external effects

Review transaction scope, isolation, autocommit, optimistic concurrency, retries, idempotency, outbox/inbox behavior, migrations, rollback, stale sessions, cache coherence, and crash recovery. A successful happy path does not prove correct partial-failure behavior.

## Validation methods

Select only applicable methods:

- focused examples and failure-path tests;
- property or state-machine tests;
- deterministic clocks and failpoints;
- cancellation and shutdown tests;
- selected process start-method tests;
- free-threaded execution where claimed;
- database crash/retry/migration fixtures;
- differential comparison to prior behavior;
- operational restart and recovery demonstration.

Return assertion-scoped findings with reproduction, environment identity, observed durable state, residual uncertainty, and exact repair/revalidation route. Do not repair the candidate.
## Structure-contract use

When a structure contract applies, compare actual state, task, process, queue, transaction, retry, resource, cancellation, cleanup, and recovery ownership to the named owners and behavior paths. Treat static annotations as insufficient evidence for runtime state and ownership. A different private helper is harmless when the fixed owner and observable behavior remain intact.
