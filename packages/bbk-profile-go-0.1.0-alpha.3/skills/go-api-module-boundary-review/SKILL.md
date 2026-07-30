---
name: go-api-module-boundary-review
description: Review Go exported APIs, package and module boundaries, method sets, errors, build configurations, wire formats, and downstream compatibility against exact assertions.
---

# Go API and Module Boundary Review

Review one exact candidate and assigned compatibility assertions. Do not mutate it.

## Bind the compatibility context

Identify:

- module path, semantic major version, `go` and `toolchain` directives;
- active `go.work`, local `replace`, vendor, build tags, targets, and CGO mode;
- public packages and intended downstream consumers;
- previous/released API or exact comparison baseline;
- wire, persistent, configuration, CLI, HTTP/RPC, and operational contracts in scope.

## Exported surface

Inspect exported:

- packages, types, aliases, constants, variables, functions, and methods;
- struct fields and embedding;
- interfaces and type sets;
- generic constraints and inferred behavior;
- constructors, zero-value contracts, option patterns, and lifecycle ordering;
- sentinel and concrete errors and `errors.Is`/`errors.As` behavior;
- examples and documentation that form caller expectations.

Check method-set changes caused by pointer/value receiver changes, embedding, generic instantiation, or moving methods. Remember that implicit interface satisfaction means a change can break consumers without an explicit implements declaration.

## Package and module boundaries

- Does each package own a coherent responsibility?
- Are `internal/` boundaries, package cycles, shared helpers, and generated packages intentional?
- Does a local `go.work` or `replace` hide standalone-module failure?
- Does a v2+ module use the correct major-version path and tag policy?
- Does the minimum Go version match dependencies and language/API use?
- Do build tags or platform files expose different public APIs?
- Are public interfaces defined where their ownership and evolution can be governed coherently?

## Compatibility dimensions

Assess each applicable dimension independently:

```text
source API
method-set and implicit-interface
module/import path
minimum Go and toolchain
build tag / target / CGO
error identity and behavior
wire/serialization
persistent data and migration
configuration
CLI
HTTP/RPC
operations
```

Do not reduce compatibility to a Boolean. Record compatible, conditional, incompatible, unknown, or not applicable with rationale.

## Go-specific hazards

- adding exported struct fields can break external unkeyed literals;
- changing value to pointer receivers or vice versa can alter method sets;
- adding methods to a public interface can break implementers;
- changing error wrapping can expose or hide identity;
- changing nil versus empty serialization can affect contracts;
- map order must not define stable output without normalization;
- changing `go` or `toolchain` directives changes consumer requirements;
- `replace` directives are not automatically part of a consumer release;
- generated APIs require source/generator and output consistency.

## Evidence

Use the cheapest sufficient set:

- exact exported-surface comparison;
- build/tag/target matrix for declared configurations;
- `GOWORK=off` clean module test;
- downstream compile fixtures;
- behavioral contract tests;
- wire/persistence golden fixtures and migrations;
- command, HTTP/RPC, or configuration compatibility tests.

A tool-generated API diff is supporting evidence, not the full compatibility decision.

## Return

Return `PASS`, `FAIL`, `BLOCKED`, or `INCONCLUSIVE` per assigned assertion; compatibility dimensions; exact evidence; consumer impact; migration or versioning requirement; coverage gaps; and the smallest valid disposition.

## Structure-contract integration

When assigned structure assertions, compare fixed module/import paths, exported declarations, consumer interfaces, method sets, error contracts, build-tag API variants, generated consumer artifacts, wire forms, and downstream module behavior. Private package/file placement is material only when the contract fixed it or it changes ownership or compatibility.

