---
name: go-security-supply-chain-review
description: Review Go trust boundaries, modules, dependencies, private-module policy, generation, untrusted input, filesystem, subprocess, network, secrets, vulnerabilities, and release provenance.
---

# Go Security and Supply-Chain Review

Review the exact candidate, module graph, build configuration, and assigned security assertions. Do not install tools or mutate dependencies.

## Trust boundaries

Identify:

- untrusted request, file, archive, template, path, database, message, and configuration inputs;
- network destinations, redirects, proxies, DNS, and credentials;
- subprocesses, arguments, environment, working directories, and inherited handles;
- filesystem roots, symlinks, temporary files, permissions, and archive extraction;
- authorization and tenant boundaries;
- secrets in logs, errors, profiles, traces, environment, binaries, and generated artifacts;
- `unsafe`, `cgo`, native libraries, plugins, and compiler directives.

## Module and workspace integrity

Review:

- `go.mod`, `go.sum`, `go.work`, `replace`, `exclude`, and `retract`;
- local and forked replacements that differ from consumer builds;
- minimal version selection and unexpected graph movement;
- vendor consistency and `vendor/modules.txt`;
- private-module configuration and information leakage to proxies or checksum services;
- tool and generator dependencies;
- licences and provenance.

A healthy `go.sum` verifies selected downloaded module content; it does not establish source trust, maintenance quality, licence suitability, or absence of malicious behavior.

## Generation and build-time effects

`go generate` may execute arbitrary repository commands. Review generator identity/version, inputs, output ownership, network and toolchain effects, reproducibility, and generated-file drift.

Review `//go:embed`, link flags, build tags, CGO compiler/linker input, and release scripts as build dependencies.

## Input and effect controls

Check:

- length, nesting, decompression, CPU, and memory bounds;
- path traversal, symlink/reparse behavior, absolute paths, duplicate archive entries, and TOCTOU;
- command injection and shell avoidance;
- URL and destination allowlists, redirects, proxy trust, and SSRF;
- template autoescaping and explicit unsafe content;
- SQL/query construction and authorization filtering;
- idempotency and replay for external mutations.

## Vulnerability evidence

Use repository-qualified vulnerability analysis such as `govulncheck` when applicable. Distinguish:

```text
known vulnerable module present
vulnerable symbol reachable
runtime/environment exposure
mitigated or unreachable
unknown or tool failure
```

Known-vulnerability tools are not a complete security review.

## CI and release provenance

Review pinned actions/tools, least-privilege credentials, protected release inputs, artifact digests, VCS state, module graph, Go/C toolchain identity, build flags, SBOM/licence inventory where required, and signing/attestation policy.

## Return

Return concrete attack or compromise scenarios, prerequisites, affected assets, evidence, severity, confidence, mitigation, regression test or gate, supply-chain disposition, and residual uncertainty. Keep tool failure distinct from candidate security failure.
