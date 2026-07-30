---
name: go-implementation-structure
description: Project or author a BBK ImplementationStructureContract and ExecutionSlice in Go vocabulary, including packages, commands, exported declarations, type concepts, ownership, failure, test seams, touchpoints, and delegated implementation freedom.
---

# Go Implementation Structure

Use this procedure only when BBK applicability is `inline` or `contract`. A profile projection is a view over the generic BBK object, never a second authority.

## Authoring sequence

1. Bind the generic contract or slice identity, revision, digest, baseline, scope, role, and assurance tier.
2. Inventory the effective `go.work`, modules, packages, commands, generated code, build tags, toolchain, targets, CGO policy, and repository-owned commands.
3. Project topology using Go concepts: workspace, module, package, command, source/generated artifact, test package, build-tag variant, module release, binary, or native boundary.
4. Define consequential contracts: exported structs/functions/constants, consumer-owned interfaces at real seams, request/result forms, stable error classifications, wire forms, module paths, and generated artifacts.
5. Apply the type-depth test. Recommend a Go type or abstraction only when it prevents a material invalid combination, localizes an invariant, clarifies authority or ownership, stabilizes a boundary, improves change locality, creates a test seam, or hides consequential complexity.
6. Describe package and runtime ownership. Name who owns state mutation, goroutines, channel close, context cancellation, timers, tickers, pools, locks, subprocesses, files, network resources, shutdown, retry, and recovery.
7. Keep static and runtime truth separate. Go types do not prove runtime input validity, goroutine termination, race freedom, ordering, persistence, CGO pointer lifetime, migration correctness, or operational recovery.
8. Separate fixed decisions from delegated freedom. Public/module paths, source-of-truth, state and lifecycle ownership, wire forms, compatibility, migration, and recovery may be fixed. Private helpers, local file layout, iteration details, and ordinary refactors should normally remain delegated.
9. Define test seams and observations at package, command, downstream-consumer, HTTP/RPC, generated-artifact, module-release, binary, race, synctest, fuzz, or native-boundary surfaces as applicable.
10. For an ExecutionSlice, name one integrated touchpoint, the minimum dependency closure, one integration owner, candidate/validation boundary, assertions, containment, and scaffolding disposition.

## Type concepts

- **Identity:** defined Go types for materially distinct IDs, units, states, names, or paths; conversion from external text stays at the boundary.
- **State:** explicit structs and typed constants for closed states; useful or explicitly invalid zero values; transition authority in one package.
- **Boundary:** request/result structs, consumer interfaces only at real substitution seams, stable error classification, runtime schemas for untrusted data.
- **Ownership:** package owner plus documented goroutine, channel, context, timer, process, and resource lifetime.
- **Failure:** distinguish absence, rejection, cancellation, timeout, stale data, partial completion, retryable failure, degraded operation, and recovery.
- **Evidence:** preserve NOT_RUN, BLOCKED, ERROR, INCONCLUSIVE, PASS, FAIL, FLAKY, and NOT_APPLICABLE.

## Slice checks

A slice must create integrated feedback or retire a named foundation risk. A foundation-first slice is acceptable only when a vertical touchpoint would be false or impossible, the risk is named, the slice has its own inspectable technical touchpoint, and it identifies the next integrated slice. Line count and file count do not define atomicity.

Return the generic object digest, Go projection digest, unsupported adjacent obligations, advisories, blockers, and the no-authority boundary.
