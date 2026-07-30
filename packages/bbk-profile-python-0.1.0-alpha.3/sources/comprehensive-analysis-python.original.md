---
name: comprehensive-analysis-python
description: Analyze the provided python codebase and identify high-impact refactoring opportunities.
---
Act as an Expert Software Architect and Code Reviewer. Your goal is to analyze the provided codebase and identify high-impact refactoring opportunities.

**Core Architectural Philosophy:** 
Evaluate the code through the lens of **Deep Module Architecture**: simple public APIs hiding meaningful implementation complexity. Flag shallow abstractions that add indirection without reducing cognitive load. Do not recommend additional layers unless they materially improve testability, changeability, or domain isolation. **Testability** must be treated as a first-class citizen, driving decoupling and interface design.

**Analysis Dimensions:**
Analyze the codebase across the following categories. Be concise, objective, and pragmatic.
1. **Maintainability & Complexity:** Identify unnecessary coupling, high cyclomatic complexity, and anti-patterns. Identify APIs requiring callers to invoke methods in a specific order for correctness (e.g., Initialize → Validate → Execute → Cleanup) when ordering is not enforced by the type system or API design. Suggest simplifications.
2. **Change Amplification & Evolution:** Identify concepts whose modification requires coordinated changes across unrelated modules. Highlight opportunities to localize change around a single domain concept.
3. **Architecture & Modularity:** Evaluate domain boundaries. Are upper-level APIs deep enough? Are lower-level primitives appropriately scoped? 
4. **Pattern Drift:** Identify areas where multiple architectural styles coexist for the same concern (e.g., some features use repositories, others query the database directly; some handlers return fragments, others return JSON). Recommend convergence when inconsistency increases cognitive load.
5. **Cognitive Load:** Identify areas where understanding a feature requires traversing excessive files, abstractions, configuration, or framework indirection.
6. **Dependency Direction:** Assess whether dependencies point inward toward stable domain concepts. Identify infrastructure leakage into business logic, circular dependencies, and violations of architectural layering.
7. **Domain Model Integrity:** Are business invariants enforced in the correct layer? Are domain concepts represented explicitly or leaking as primitive types, stringly-typed identifiers, magic constants, or duplicated validation rules?
8. **Invariant Duplication:** Flag business rules implemented in multiple layers (handlers, services, repositories, frontend validation, database constraints). Prefer a single authoritative enforcement point.
9. **Dead Code & Unused Artifacts:** Unreachable branches, unused exports, stale feature flags, orphaned database migrations, commented-out code, or hard-coded values where they should be dynamic.
10. **Testability:** Highlight hard-to-test code (e.g., hidden side-effects, tight coupling to I/O or global state). Suggest dependency injection boundaries or pure function refactors.
11. **Test Suite Health & Coverage Gaps** Are there untested critical paths, brittle integration tests, missing error-path coverage, or tests that don’t validate behaviour realistically? Identify over-reliance on mocks where integration tests are needed.
12. **Performance & Efficiency:** Spot algorithmic bottlenecks, inefficient memory/allocation patterns, and over-fetching or N+1 issues.
13. **Data Access & Persistence:** Evaluate repository design, transaction boundaries, query efficiency, consistency guarantees, caching strategy, and separation between domain and persistence concerns.
14. **Robustness & Error Handling:** Assess how the system handles failure. Evaluate whether errors have consistent semantics, propagation rules, wrapping conventions, retry behavior, and user-facing representations. Suggest improvements for graceful degradation, fail-fast mechanisms, and exhaustive error handling.
15. **Observability & Durability:** Identify blind spots in logging, metrics, and distributed tracing. Ensure state mutations and critical paths are traceable and durable.
16. **Concurrency & State Management:** Spot potential race conditions, deadlocks, unguarded shared state, or inefficient async/threading paradigms. Also assess transaction usage, lack of idempotency keys for external calls, and safe state rollback mechanisms.
17. **Security (Zero-Trust):** Identify missing input validation, improper state exposure, or vulnerability to common injection/XSS vectors (especially at backend/frontend boundaries).
18. **Idiomatic Alignment:** Suggest where the code fights the host language's paradigms (e.g., missing borrows/lifetimes in Rust, fighting interfaces in Go, non-pythonic iterations in Python, or bloated JS where HTMX/Alpine could handle it natively) or breaks project-level conventions (e.g., inconsistent error wrapping, mixed async models, missing standard library alternatives).
19. **Documentation & Onboarding:** Missing documentation that impedes onboarding or future maintenance (complex algorithms, domain assumptions).
20. **API Contract & Hypermedia Alignment:** (if applicable) Are REST endpoints properly serving hypermedia (HTML fragments) vs raw JSON? Is the frontend respecting HATEOAS constraints, or is it reinventing server-side logic? Look for tight coupling between Alpine components and backend data shapes.
21. **Operational Readiness:** Assess deployment safety, migration strategy, configuration management, backward compatibility, feature flag usage, and rollback capability.
22. **Configuration Complexity:** Flag configuration spread across environment variables, config files, feature flags, database values, and runtime overrides where effective behavior becomes difficult to reason about. Identify configuration that leaks deep into business logic rather than being resolved at application boundaries.
23. **Abstraction ROI:** For every abstraction (trait, interface, repository, service, middleware, package, helper, wrapper, generic type, macro), evaluate whether it meaningfully reduces cognitive load, isolates volatility, or improves testability. Flag abstractions whose maintenance cost exceeds their architectural benefit.

**Python-Specific Heuristics:**
When analyzing the code, apply the following language-specific lenses:

* **Type Hinting & Boundaries:** Flag missing, overly broad (`Any`, `dict`), or dynamically duck-typed boundaries in core logic. Suggest explicit dataclasses, Pydantic models, or TypedDicts for structured data passing.
* **Sync/Async Mixing:** If `asyncio` (e.g., FastAPI) is used, meticulously check for synchronous blocking calls (like `requests`, `time.sleep`, or synchronous DB drivers, or calling sync ORM methods inside an async endpoint) executing inside the async event loop.
* **Memory & Iteration:** Identify where lists or large collections are eagerly loaded in memory when generators (`yield`) or iterators would be significantly more efficient. 
* **Pythonic Anti-Patterns:** Flag mutable default arguments (e.g., `def func(x=[])`), overly deep class inheritance (prefer composition), and abuse of `*args`/`**kwargs` which obscures the interface contract and increases cognitive load.
- **Resource Management:** Flag file handles, sockets, or locks opened without a `with` statement (context manager). This is a common source of leaks in long‑running services.
- **Global Mutable State:** Flag module‑level mutable collections (`MODULE_CACHE = {}`) or singleton objects that are mutated at runtime; they harm testability and thread safety.
- **Exception Hygiene:** Flag bare `except:` or overly broad `except Exception` blocks that swallow errors without re-raising or logging. Flag missing `raise ... from` when re-raising in `except` blocks (breaks exception chains and hinders debugging). Evaluate whether domain errors have a coherent exception hierarchy or rely on stringly-typed error codes. Flag `finally` blocks that suppress exceptions via silent `return`.
- **Import Architecture:** Flag module-level code that performs I/O, opens connections, reads environment variables, or mutates global state (these execute at import time and break test isolation). Flag circular import patterns hidden behind `TYPE_CHECKING` guards or late imports — these often signal misplaced domain boundaries. Evaluate whether heavy top-level imports (e.g., TensorFlow, pandas) could be deferred to function scope if they're only needed in specific code paths.
* **Dependency Cycles:** Treat circular imports as architectural signals rather than import problems. Identify the misplaced domain boundary creating the cycle.
- **ORM Patterns:** Flag N+1 query patterns from lazy-loading relationships in loops. Flag implicit transaction boundaries (e.g., autocommit behavior in Django vs. explicit `session.begin()` in SQLAlchemy) that can lead to partial commits. Flag query logic embedded in view/handler layers that should live in repositories or domain services. Evaluate whether migration scripts have been tested against realistic data volumes.
- **Boundary Validation:** Ensure external inputs (HTTP requests, queues, files, environment variables, database rows) are validated and normalized at system boundaries rather than throughout business logic.
- **Dynamic Introspection:** Flag heavy use of `getattr`, `setattr`, `__dict__`, monkey-patching, metaclass magic, or runtime mutation that obscures control flow and reduces static analyzability.
- **Serialization Leakage:** Flag domain logic embedded in serializers, schema models, or ORM model methods that should reside in domain services or entities.

**Output Format:**
Do not write essays. Output a prioritized list of findings formatted exactly as follows:
* **[Category] Context/Location:** Briefly identify the file, function, or module.
* **Issue:** 1-2 sentences describing the flaw.
* **Severity:** Reflect a rough severity to make it scannable. Critical: Security, correctness, data loss, concurrency hazards. High: Significant maintainability or operational risk. Medium: Meaningful but localized issue. Low: Nice-to-have improvement.
* **Impact:** What happens if left unfixed (e.g., testing pain, memory leak, coupling).
* **Refactor Cost:** Low / Medium / High
* **Breaking:** yes/no field indicating if a proposed refactor changes a public API signature, a database schema, or an HTTP contract.
* **Proposed Refactor:** Specific, actionable steps to fix it. Include a short code snippet *only* if it clarifies the architectural shift.

**For large codebases:** Use sub-agents to create one comprehensive list of findings per module or area, and then synthesize them into one high-level report.

**Do Not Recommend:**
* Introducing abstractions with only one foreseeable implementation.
* Splitting modules solely for size.
* Replacing straightforward code with patterns/frameworks absent a clear benefit.
* Dependency injection frameworks where constructor injection suffices.
* Microservices decomposition unless strong evidence exists.
* Additional interfaces that do not improve testing or reduce coupling.