---
name: bbk-go
description: Route Go work through the BBK Go profile. Use for Go module/workspace preflight, implementation guidance, focused review selection, proportional gate planning, evidence handling, and profile locking without granting effects or declaring success.
---

# BBK Go

Apply Go-specific procedure inside the existing BBK role, task, scope, and assurance contract.

## Start with the effective build context

Before material work, determine:

- active `go.mod`, parent `go.work`, and workspace members;
- module paths, `go` and `toolchain` directives, and exact effective Go patch;
- `GOOS`, `GOARCH`, `CGO_ENABLED`, build tags, experiments, PGO input, and relevant `GODEBUG`;
- `go.mod`, `go.sum`, `replace`, `exclude`, `retract`, vendor, private-module, and generation policy;
- repository-owned format, lint, test, generation, integration, and release commands.

Use `bbk-go preflight` or `bbk profile resolve --id go`. Do not invoke Go tools unless the work or `--run-tools` explicitly permits it. Resolver-owned probes are offline and disable automatic toolchain download.

## Route by task and assertion

- implementation workers receive `go-skills` and only applicable concern guidance;
- broad architecture assessment uses `comprehensive-analysis-go` as a survey;
- public API, method-set, module, wire, or error-contract assertions use `go-api-module-boundary-review`;
- goroutine, channel, context, synchronization, retry, persistence, or lifecycle assertions use `go-correctness-concurrency-review`;
- testing design uses `go-test-strategy-review`;
- deployment, shutdown, configuration, migration, and operations use `go-operational-readiness-review`;
- dependencies, generators, private modules, untrusted input, commands, files, and network boundaries use `go-security-supply-chain-review`;
- `unsafe`, `cgo`, assembly, callbacks, and `//go:` directives use `go-unsafe-cgo-assembly-review`;
- HTMX/Alpine conventions use `go-web-htmx-review` only when that stack is actually selected;
- module or binary release uses `go-package-release-gates`;
- race, fuzz, flaky, benchmark, coverage, profile, crash, and reproducer artifacts use `go-evidence-reproducer`.

Do not follow a broad survey with every focused reviewer. Select only packs that own distinct assertions.

## Worker policy

1. Bind the exact module/package scope, build configuration, interfaces, and allowed effects.
2. Prefer repository conventions and standard-library solutions where they satisfy the contract.
3. Make goroutine lifetime, cancellation, cleanup, error identity, nil/zero-value behavior, and ownership visible.
4. Treat `go mod tidy`, `go generate`, dependency changes, format writes, and tool installation as effects.
5. Run focused checks during iteration. Preserve full-suite and matrix work for the assurance contract.
6. Return changed paths, commands, exact configurations, results, residuals, and discoveries.

## Validator policy

1. Bind one exact candidate and named assertions.
2. Reuse valid deterministic receipts rather than repeating mechanics from scratch.
3. Review only the selected compatibility, correctness, security, operations, or native-boundary concerns.
4. Distinguish `PASS`, `FAIL`, `BLOCKED`, `ERROR`, `INCONCLUSIVE`, `NOT_APPLICABLE`, `SKIPPED_BY_POLICY`, and `FLAKY`.
5. Do not repair, broaden scope, waive findings, or infer that a passing Go check establishes BBK completion.

## Gate principles

- final gates are check-only;
- candidate acceptance declares test-cache policy;
- a passing race run proves only exercised paths;
- workspace success does not prove `GOWORK=off` module release success;
- build-tag, target, CGO, and minimum-Go matrices are declared rather than guessed;
- required unavailable tools or configurations are `BLOCKED`;
- optional tools are advisory and are never installed silently.

## Return

Return the effective Go context, selected skills and reasons, planned gates, evidence identity, applicability gaps, unsupported configurations, and the smallest valid next action.

## Alpha.4 implementation structure and slicing

- When an `ImplementationStructureContract` is supplied, preserve its identity, revision, digest, fixed decisions, delegated freedom, scope, and review policy. Use `bbk-go structure`; do not rewrite the generic object.
- When an `ExecutionSlice` is supplied, use `bbk-go slice` to project a Go touchpoint, dependency closure, assertion evidence, candidate/validation boundary, and scaffolding disposition.
- Route `none` to ordinary profile behavior, `inline` to compact worker guidance, and `contract` to the focused structure authoring/review procedure.
- Select `go-implementation-structure-review` only for contract-level or independently material structure assertions. Do not preload it into routine workers.
- Compare fixed public/shared/package/state/lifecycle decisions, not exact private file trees.
- Add contract, slice, and projection digests to the effective profile lock.

