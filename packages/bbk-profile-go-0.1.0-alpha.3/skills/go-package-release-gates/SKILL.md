---
name: go-package-release-gates
description: Define and review clean Go module or binary release gates, exact build identity, standalone consumer behavior, artifacts, startup diagnostics, rollback, and removal.
---

# Go Package and Release Gates

Distinguish public module releases from command/service artifacts.

## Public module release

Verify in a clean source copy:

- correct module path and v2+ major suffix;
- intended semantic version/tag relationship;
- `go` and `toolchain` policy;
- no unintended local `replace` or workspace dependency;
- `GOWORK=off` build and fresh tests;
- `go mod tidy` comparison and `go mod verify`;
- minimum supported Go version;
- declared tags/targets/CGO configurations;
- exported API and downstream consumer fixtures;
- docs/examples and generated artifacts;
- licences, vulnerabilities, and provenance as required.

## Binary or service release

Verify:

- clean build from exact source, module graph, Go/C toolchains, target, tags, CGO, experiments, flags, and PGO profile;
- expected commands and artifact set;
- startup, version/build-info output, missing/invalid configuration, signals, shutdown, and exit codes;
- native dependencies and portability assumptions;
- archive/install contents, permissions, checksums, rollback, and clean removal;
- migration and mixed-version behavior where applicable.

Use `go version -m` or equivalent artifact inspection to record embedded build/module information. Decide intentionally whether VCS stamping and `-trimpath` are required; they affect provenance, privacy, diagnostics, and reproducibility.

## Reproducibility

Do not require byte-identical binaries unless it is an explicit release assertion with controlled builders. Otherwise bind the fresh binary digest to exact source, module graph, toolchains, environment, flags, PGO, and candidate identity.

## Gate behavior

- final gates are check-only;
- generators and module tidy run in disposable copies and compare;
- missing required targets/tools are `BLOCKED`;
- one local workspace success does not prove standalone consumer success;
- signing, publication, registry upload, deployment, and remote writes require separate effect authority.

## Return

Return the release subject, exact environment, artifact manifest/digests, compatibility matrix, test and startup evidence, unsupported configurations, rollback/removal result, advisories, and release disposition. Do not equate this profile's result with official BBK or Blueprint release authority.
