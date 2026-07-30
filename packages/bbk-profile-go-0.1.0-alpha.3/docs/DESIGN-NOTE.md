# Go alpha.4 structure design note

## Meaningful type concepts

Go identity types, structs, typed constant sets, consumer interfaces, generic constraints, sentinel or typed errors, zero-value contracts, pointer/value semantics, runtime schemas, and explicit goroutine/channel/context lifecycle contracts.

## Inline versus contract triggers

`inline` is appropriate for a bounded private package change with one owner and no material public, state, concurrency, persistence, migration, release, or cross-module consequence. `contract` is selected for public/shared API or wire changes, package/source-of-truth ownership, goroutine/channel/cancellation/recovery, persistence/migration, multi-module topology, generated consumer shape, CGO/unsafe/ABI, release subjects, and hard-to-reverse realization decisions.

## Touchpoint vocabulary

Go command, package API, HTTP/RPC exchange, downstream consumer, package test, race run, synctest observation, fuzz reproducer, generated artifact, module release, binary/archive, protocol trace, and CGO/ABI fixture.

## Material planned/actual differences

Changes to fixed package or state ownership, exported/module/wire contracts, stable error handling, goroutine/channel/context lifecycle, effect/recovery boundaries, build-tag consumer shape, generated artifacts, migration, module release, or slice assertions are material. Private helpers, file movement, local iteration, and test utility placement inside delegated bounds are not.

## Evidence classes

Manifest/schema checks and static inventory are deterministic. Architecture and ownership quality are agent-reviewed. `go`, repository build/test/lint tools, race, fuzz, `govulncheck`, and native toolchains are tool-authoritative only for their exercised configuration. Downstream/module/package fixtures provide consumer evidence. Operational and human review remain necessary where runtime or organizational truth cannot be derived statically.

## Unsupported or unqualified areas

TinyGo, embedded, eBPF, mobile, specialized WASM, plugins, custom Go compiler forks, unusual shared-library modes, broad cross-platform runtime matrices, and every CGO sanitizer configuration remain partial or project-specific. Mixed subjects receive a bounded Go projection and explicit adjacent obligations.
