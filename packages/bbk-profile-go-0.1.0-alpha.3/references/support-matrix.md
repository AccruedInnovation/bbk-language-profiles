# Go support matrix

## Primary support

- ordinary modules and workspaces;
- libraries, commands, HTTP/RPC services, and concurrent applications;
- generated-code repositories;
- module and binary release planning;
- standard-library and repository-defined testing and analysis.

## Conditional support

The following require explicit triggers, tools, targets, and project evidence:

- public module compatibility and semantic import versioning;
- `unsafe`, `cgo`, assembly, callbacks, and compiler/runtime directives;
- platform-specific behavior and cross-compilation;
- PGO;
- database and persistent-data migrations;
- HTMX/Alpine server-driven UI conventions;
- race, fuzz, coverage, mutation, sanitizer, and vulnerability evidence.

## Partial or unqualified

- Go plugins;
- mobile;
- TinyGo and embedded systems;
- eBPF;
- specialized WASM environments;
- custom compiler forks;
- unusual shared-library build modes.

## Version policy

The repository's `go` and `toolchain` directives and exact effective patch release are authoritative. Version-dependent techniques are selected only when supported. For example, `testing/synctest` requires a sufficiently recent standard library; sanitizer and race support varies by target and CGO/toolchain configuration.
