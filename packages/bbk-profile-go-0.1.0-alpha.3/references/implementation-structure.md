# Go implementation structure and slicing

The generic `ImplementationStructureContract` and `ExecutionSlice` remain authoritative. The Go profile projects them into modules, packages, commands, exported declarations, request/result forms, errors, goroutine/channel/context ownership, generated artifacts, build configurations, module releases, tests, and runtime touchpoints.

Use `none` for routine private changes whose shape is already constrained. Use `inline` for a compact package/type/ownership note. Use `contract` for material public or shared interfaces, state/lifecycle ownership, concurrency/cancellation/recovery, persistence/migration, multi-module work, CGO/unsafe, release shape, or consequential uncertainty about where behavior belongs.

Conformance is semantic. Fixed decisions and consequential shape matter; exact private file trees do not. The profile never grants tools, effects, scope, approval, validation, or release authority.
