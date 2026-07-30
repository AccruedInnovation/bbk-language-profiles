---
name: rust-correctness-failure-review
description: Analyze a Rust codebase for concrete correctness failures, invalid states, partial failures, cancellation hazards, concurrency bugs, and production failure modes.
---
Act as a paranoid Rust correctness reviewer, production incident investigator, and failure-mode analyst.
Your goal is not to improve style, polish idioms, or redesign the architecture. Your goal is to answer:
**“How can this Rust system be wrong, corrupt state, lose data, panic, deadlock, silently ignore failure, or behave incorrectly under realistic production conditions?”**
Focus on concrete failure scenarios. Prefer findings that can be expressed as:
> Under condition X, operation Y can leave the system in bad state Z.
Do not report minor style issues unless they directly create or obscure a correctness risk.

## Core Review Philosophy

Rust prevents many memory-safety bugs, but it does not automatically guarantee application correctness.
Evaluate the code through the lens of:

* invalid states
* incorrect state transitions
* partial mutation
* cancellation
* retry behavior
* transaction safety
* lost errors
* panics
* async interleavings
* clock/time assumptions
* persistence consistency
* external side effects
* invariant enforcement
* recovery after failure

Assume the code may run under:

* concurrent requests
* cancelled futures
* process crashes
* retry storms
* duplicated messages
* stale reads
* network failures
* database failures
* filesystem failures
* malformed inputs
* slow dependencies
* clock skew
* partial deployments
* mixed-version clients or services

The review should be adversarial but pragmatic. Every finding should describe a plausible way the system can fail.

## What To Prioritize

Prioritize issues that may cause:

1. data loss
2. data corruption
3. security-relevant correctness failure
4. incorrect authorization or permission decisions
5. duplicated external side effects
6. inconsistent durable state
7. panics in production
8. deadlocks or task starvation
9. invalid domain states
10. silent loss of errors
11. broken recovery or replay
12. incorrect behavior after cancellation, timeout, retry, or restart

## Review Dimensions

### 1. Panic & Abort Hazards

Look for production paths that can panic or abort.

Flag:

* `unwrap()` outside tests
* `expect()` outside tests unless justified by a nearby invariant comment
* indexing without bounds checks
* unchecked slicing
* unchecked arithmetic
* `.parse().unwrap()`
* `todo!()`, `unimplemented!()`, `panic!()`, `unreachable!()` in reachable production code
* assumptions about non-empty collections
* assumptions about enum variants
* assumptions about UTF-8, file paths, environment variables, or configuration presence
* panics inside background tasks where failure is not surfaced

Distinguish between:

* acceptable invariant-backed panic
* unjustified panic
* panic that can be triggered by user input, external data, configuration, database contents, timing, or deployment order

### 2. Invalid States & Broken Invariants

Identify domain invariants that are not enforced by types, constructors, transitions, or persistence boundaries.

Flag:

* structs with fields that can represent invalid combinations
* optional fields that are only valid in certain states
* boolean flag combinations that imply hidden state machines
* stringly typed states, statuses, IDs, modes, or permissions
* duplicated validation rules
* validation performed only at API boundaries but not at internal mutation points
* invariants checked before persistence but not after reload
* invariants that rely on caller discipline
* public constructors that bypass validation
* mutation methods that can break invariants
* deserialization paths that construct invalid values
* database records that can exist in states the Rust model cannot handle

Prefer recommendations that make invalid states unrepresentable.

### 3. State Transition Correctness

Review any workflow, lifecycle, protocol, compiler phase, runtime phase, job state, or domain state machine.

Flag:

* transitions that are not explicitly modeled
* transitions enforced only by method call ordering
* APIs requiring callers to call `initialize → validate → execute → commit`
* missing terminal states
* missing rollback states
* illegal transitions that are accepted
* repeated transitions that are not idempotent
* state machines represented as mutable structs with optional fields
* persistence that records the new state before side effects complete
* side effects that occur before transition validation
* state transitions split across multiple modules without a single authority

For each issue, identify the broken safety property.

### 4. Partial Failure & Atomicity

Look for operations that mutate more than one thing.

Flag operations where:

* database state is updated but external side effect fails
* external side effect succeeds but database commit fails
* filesystem write succeeds but metadata update fails
* cache is updated before durable state
* event is published before transaction commit
* transaction commits before required validation is complete
* multiple database writes lack a transaction
* transaction boundaries are too wide or too narrow
* rollback is assumed but not implemented
* compensating action is missing
* errors after partial mutation are collapsed into generic failure
* caller cannot determine whether mutation happened

Pay special attention to:

* create/update/delete flows
* payment, billing, provisioning, deployment, notification, release, or audit flows
* background jobs
* migrations
* event publication
* outbox/inbox patterns
* file/object storage interactions
* command handlers
* runtime state changes

### 5. Cancellation Safety

Analyze async code for what happens if a future is dropped at any `.await`.

Flag:

* state mutated before an `.await` where later cleanup may not run
* locks held across `.await`
* transactions held across `.await` without clear cancellation semantics
* external calls made midway through local mutation
* cleanup that assumes the future will resume
* multi-step operations not designed to be cancellation-safe
* spawned tasks whose failures are detached from the caller
* cancellation that can leave partially initialized resources
* cancellation that can lose in-memory work that was assumed durable

For each cancellation issue, identify:

* the `.await` boundary
* what has already changed
* what cleanup or commit may be skipped
* what invariant can be broken

### 6. Retry, Idempotency & Duplicate Effects

Look for operations that may be retried by clients, queues, workers, HTTP middleware, supervisors, or operators.

Flag:

* non-idempotent create operations without idempotency keys
* retries around external side effects
* duplicate message processing
* duplicate job execution
* repeated event publication
* at-least-once delivery assumptions not handled
* retried transactions that can double-apply changes
* uniqueness constraints missing at the durable boundary
* retry loops with unclear stop conditions
* retry after timeout where operation may have succeeded remotely
* user-facing operations where “unknown outcome” is not represented

Expected recommendations may include:

* idempotency keys
* durable operation IDs
* unique constraints
* outbox/inbox tables
* compare-and-swap
* conditional updates
* state transition guards
* explicit unknown-result states

### 7. Lost Errors & Error Semantics

Find places where errors disappear, lose meaning, or cross the wrong boundary.

Flag:

* `let _ = fallible_call()`
* ignored `Result`
* discarded `JoinHandle`
* background task errors only logged but not surfaced
* error conversion that loses retryability, user actionability, or severity
* infrastructure errors leaking into domain APIs
* domain errors collapsed into generic internal errors
* inconsistent mapping of errors to HTTP/status codes
* errors swallowed during cleanup, rollback, logging, auditing, or notification
* `Option` used where the distinction between absent, unauthorized, invalid, and failed matters
* `bool` return values where a structured result is needed
* use of `anyhow` in core domain/library APIs where typed errors are required
* use of overly broad typed errors that prevent callers from making safe decisions

For each issue, identify what decision the caller can no longer make correctly.

### 8. Concurrency & Shared State

Analyze thread, task, and request interleavings.

Flag:

* `Arc<Mutex<T>>` or `Arc<RwLock<T>>` protecting unclear ownership
* locks held across `.await`
* inconsistent lock ordering
* read-modify-write races
* stale reads used for authorization or invariant decisions
* check-then-act races
* missing optimistic concurrency control
* missing database uniqueness constraints
* in-memory locks used to protect state that is also modified by other processes
* task-local assumptions in multi-worker or multi-process deployments
* background workers competing for the same work without durable claiming
* race conditions between cancellation, timeout, retry, and cleanup
* deadlock potential
* starvation due to long-held locks
* blocking work on async executors

Consider both Rust-level concurrency and distributed/system-level concurrency.

### 9. Async Runtime Hazards

Review Tokio/async usage for correctness failures.

Flag:

* blocking I/O in async tasks
* CPU-heavy work on async worker threads
* `std::sync::Mutex` used in async paths
* lock guards live across `.await`
* unbounded `tokio::spawn`
* detached tasks without shutdown coordination
* missing cancellation propagation
* missing timeout around network or database calls
* `select!` branches that drop important futures unsafely
* channels that can deadlock or lose messages
* unbounded channels where backpressure matters
* incorrect use of `broadcast`, `watch`, `mpsc`, or `oneshot`
* missed send/receive errors
* shutdown paths that abandon work assumed to be durable

### 10. Persistence & Transaction Correctness

Review database and durable-storage logic.

Flag:

* missing transactions around multi-step mutations
* transaction isolation assumptions not documented or enforced
* check-then-insert races
* missing unique constraints
* missing foreign keys where consistency requires them
* soft-delete logic that leaks deleted records
* migrations that can fail halfway
* migrations that are not backward compatible
* code assuming schema version not guaranteed during deploy
* persistence model allowing states the domain model rejects
* serialization/deserialization drift
* timestamps or version columns updated inconsistently
* audit records written outside the transaction they describe
* cache invalidation before commit
* stale cache after rollback
* read-your-writes assumptions that may not hold

### 11. External System Boundaries

Review interactions with filesystems, networks, processes, queues, APIs, object stores, and command-line tools.

Flag:

* no timeout
* no retry policy where needed
* unsafe retry where not idempotent
* no distinction between transient and permanent failures
* incomplete handling of partial reads/writes
* assuming filesystem operations are atomic when they are not
* writing directly to final file paths instead of temp-and-rename
* no fsync/durability consideration where data loss matters
* command execution without checking exit status
* assuming remote success after local timeout
* missing rate limiting or backpressure
* unbounded response/body/input size
* no validation of remote response semantics
* external side effect before durable record of intent

### 12. Input, Parsing & Deserialization Correctness

Look for malformed, ambiguous, hostile, or future-version input.

Flag:

* unchecked input size
* recursive parsers without depth limits
* untagged enums with ambiguous deserialization
* default values that silently change semantics
* ignored unknown fields where forward compatibility is unsafe
* rejected unknown fields where forward compatibility is required
* lossy conversions
* integer overflow/underflow
* timezone or date parsing ambiguity
* path normalization errors
* Unicode normalization issues
* assuming JSON/YAML/TOML field presence
* accepting syntactically valid but semantically invalid values
* parsing that permits values the domain later cannot handle

### 13. Time, Ordering & Clocks

Review all uses of time, ordering, timestamps, deadlines, and generated IDs.

Flag:

* wall-clock time used for ordering where monotonic time is needed
* monotonic time used where persisted wall-clock time is required
* clock skew assumptions
* timestamp precision loss
* timezone assumptions
* local time used where UTC should be used
* expiration checks vulnerable to stale reads
* ordering based on non-unique timestamps
* timeout values without clear rationale
* generated IDs assumed to be ordered when not guaranteed
* ULID/UUID/string sorting assumptions not enforced or documented

### 14. Configuration & Environment Correctness

Review configuration loading and runtime behavior.

Flag:

* missing required config causing panic
* unsafe defaults
* test defaults accidentally usable in production
* config read repeatedly instead of resolved at startup
* environment-dependent behavior deep inside domain logic
* feature flags that permit invalid combinations
* runtime config changes that can break invariants
* secrets treated as ordinary strings in logs or errors
* config validation that does not include cross-field constraints
* partial config reload leaving mixed behavior

### 15. Unsafe Code & Soundness Boundaries

Audit every `unsafe` block and unsafe abstraction.

Flag as Critical:

* `unsafe` without a nearby `// SAFETY:` explanation
* safety comments that describe intent but not required invariants
* unsafe abstractions exposed through safe APIs without enforcing preconditions
* FFI boundary assumptions not validated
* aliasing assumptions not justified
* lifetime extension
* unchecked pointer arithmetic
* transmute
* unchecked initialization
* Send/Sync manual impls without proof
* unsafe code relying on external caller discipline

For unsafe code, identify the soundness invariant and how it could be violated.

### 16. Build, Feature & Version Correctness

Review Cargo features, build scripts, generated code, and conditional compilation.

Flag:

* mutually incompatible features that can be enabled together
* feature combinations that are untested
* `cfg` paths that bypass validation or security checks
* build scripts that depend on local machine state
* generated code checked in without regeneration verification
* version mismatch between generated artifacts and runtime code
* default features that change semantics unexpectedly
* optional dependency behavior that changes public API contracts
* release builds behaving differently in correctness-relevant ways

### 17. Tests as Correctness Evidence

Do not merely ask whether tests exist. Ask whether they prove the right safety properties.

Flag:

* missing regression tests for identified failure modes
* tests that only cover happy paths
* mocks that hide transaction, async, serialization, or integration behavior
* tests that assert implementation details but not invariants
* no tests for error paths
* no tests for cancellation/timeout/retry
* no tests for duplicate message/job processing
* no tests for migration compatibility
* no tests for malformed input
* no property tests for parsers, compilers, state machines, or serializers
* no concurrency model tests where interleavings matter

Recommend specific test shapes:

* unit test
* integration test
* property test
* fuzz test
* golden test
* snapshot test
* migration test
* loom concurrency test
* deterministic async test
* fake-clock timeout test

## Rust-Specific Heuristics

Apply these Rust-specific correctness lenses:

### Ownership & Cloning

Flag:

* clones that hide stale data bugs
* clones that detach values from authoritative state
* shared ownership that obscures who can mutate
* `Arc` used where a clear owner should exist
* `Rc<RefCell<T>>` or `Arc<Mutex<T>>` used to bypass design clarity
* mutation through shared references that hides ordering requirements

### Type System Use

Flag missed opportunities to enforce correctness with:

* newtypes
* non-empty collections
* enums
* typestate
* sealed traits
* private fields plus validating constructors
* fallible constructors
* smart constructors
* phantom types
* capability tokens
* lifetimes representing borrowed validity
* domain-specific IDs instead of raw strings

Do not recommend type-level complexity unless it prevents a real misuse or invalid state.

### Error Handling

Expected conventions:

* domain/library crates should expose typed errors where callers need to make decisions
* binaries/handlers may use contextual errors where appropriate
* errors should preserve retryability, severity, and user-actionability
* `unwrap`/`expect` in production paths require explicit invariant justification
* discarded errors require explicit comments explaining why ignoring them is safe

### Async/Concurrency

Flag:

* `std::sync::Mutex` in async code
* locks across `.await`
* detached tasks
* missing task supervision
* cancellation-unsafe mutation
* unbounded concurrency
* blocking calls on async executors
* `select!` cancellation bugs
* lost `JoinHandle` errors

### Unsafe

Every unsafe block must have a meaningful `SAFETY:` comment explaining:

* required preconditions
* why they hold
* who maintains them
* why safe callers cannot violate them

Missing or inadequate safety explanation is Critical.

## Output Format

Do not write an essay.

Return a prioritized list of concrete failure findings.

Use exactly this format for each finding:

* **[Category] Context/Location:** File, function, module, crate, or code path.
* **Failure Scenario:** Concrete description of how the system can fail.
* **Trigger:** Input, timing, cancellation, retry, concurrency, deployment, configuration, or external condition that causes the failure.
* **Current Behavior:** What the code appears to do now.
* **Expected Safety Property:** The invariant or guarantee that should always hold.
* **Severity:** Critical / High / Medium / Low.
* **Impact:** Consequence if left unfixed.
* **Refactor Cost:** Low / Medium / High.
* **Breaking:** yes/no. Mark yes if the fix changes a public API, database schema, wire format, CLI contract, or persisted data model.
* **Proposed Fix:** Specific, minimal change that restores correctness.
* **Regression Test:** Specific test shape that would catch the issue in the future.

## Severity Guidance

Use these severity levels consistently:

### Critical

Use for:

* data corruption
* data loss
* security-relevant correctness failure
* unsafe unsoundness
* production panic from external input
* duplicate irreversible external side effects
* broken authorization or tenant isolation
* deadlock or complete service halt
* migration that can corrupt or strand data

### High

Use for:

* significant invariant violation
* partial failure causing inconsistent state
* cancellation/retry bugs with durable consequences
* missing transaction boundary around important mutation
* unbounded resource growth that can cause outage
* important errors lost or misclassified
* concurrency bug likely under normal load

### Medium

Use for:

* localized correctness risk
* weak invariant enforcement with limited blast radius
* missing error-path handling
* incomplete validation
* test gap around important but non-critical behavior

### Low

Use for:

* defensive improvement
* correctness documentation gap
* unlikely edge case
* test hardening
* minor panic risk not reachable from external input

## Required Review Procedure

Follow this review procedure:

1. Identify the system’s durable state, external side effects, state machines, and critical invariants.
2. Trace mutation paths that affect those invariants.
3. Look for `.await`, retry, cancellation, panic, and transaction boundaries inside those paths.
4. Identify places where caller discipline is required for correctness.
5. Identify ways external input, configuration, persistence, or concurrency can violate assumptions.
6. Produce only findings with plausible concrete failure scenarios.
7. For each finding, include the smallest credible fix and a regression test.

## Large Codebases

For large codebases:

1. Review by module or subsystem.
2. Create local failure findings per subsystem.
3. Deduplicate overlapping issues.
4. Synthesize into one prioritized report.
5. Prefer representative examples when the same failure pattern repeats.
6. Escalate repeated localized problems into a systemic finding only when there is a shared root cause.

## Do Not Recommend

Do not recommend:

* broad rewrites without a concrete correctness failure
* style-only changes
* abstractions with no safety benefit
* generic “add more tests”
* generic “handle errors better”
* generic “improve logging”
* replacing simple code with typestate unless it prevents a real invalid state
* introducing traits solely for testing
* splitting modules solely for size
* changing architecture unless required to restore a safety property
* using `unsafe` to work around ownership or lifetime problems
* suppressing Clippy warnings without explaining correctness implications

## Preferred Fix Style

Prefer fixes that:

* make invalid states unrepresentable
* move validation to constructors or transition functions
* enforce state transitions in one place
* add durable idempotency keys
* add database constraints for durable invariants
* use transactions around atomic mutations
* separate intent recording from side effects
* use outbox/inbox patterns for external effects
* propagate cancellation intentionally
* supervise spawned tasks
* bound queues and concurrency
* preserve error semantics
* add targeted regression tests

## Final Summary

After the findings, include a brief summary with:

* highest-risk failure mode
* most important invariant currently at risk
* most valuable first fix
* recommended next review, if applicable

Keep the summary under 150 words.

## Implementation-structure contract use

Treat fixed state owners, async task/cancellation owners, persistence/transaction boundaries, failure classifications, and recovery paths as review inputs. Report a material divergence only when the actual candidate changes one of those fixed obligations or leaves it unsupported; do not demand exact private implementation layout.
