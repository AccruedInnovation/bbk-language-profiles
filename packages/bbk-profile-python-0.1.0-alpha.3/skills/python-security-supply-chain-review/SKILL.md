---
name: python-security-supply-chain-review
description: Review Python trust boundaries, dynamic execution, deserialization, subprocesses, paths, archives, network behavior, secrets, build backends, dependency sources, plugins, packages, and release provenance.
---

# Python Security and Supply-Chain Review

Use for trust-boundary, dependency, build, plugin, dynamic-code, subprocess, filesystem, archive, HTTP, credential, or release changes.

## Threat and authority frame

Record:

- assets and secrets;
- actors and trust boundaries;
- untrusted inputs and content;
- executable/build-time code paths;
- network and external effects;
- package indexes, registries, direct URLs, and VCS sources;
- exact candidate, environment, and assertions.

Avoid generic “zero trust” warnings without a concrete entry point and consequence.

## Dynamic execution and reconstruction

Inspect:

- `eval`, `exec`, `compile`;
- dynamic imports, plugin loading, template evaluation, and generated code;
- `pickle`, `shelve`, `dill`-style formats, unsafe YAML/object constructors, and custom reconstruction;
- runtime annotation evaluation;
- framework hooks that import or execute user-controlled paths.

Treat untrusted object reconstruction or dynamic execution as direct code-execution boundaries. Identify provenance, authentication, sandbox assumptions, and safer representations.

## Commands and subprocesses

Review:

- shell use and quoting;
- executable resolution and working directory;
- inherited environment and secrets;
- timeouts, process groups, signals, and cleanup;
- user-controlled arguments, files, and batch/shell semantics;
- captured output, encoding, limits, and logging.

## Files, paths, archives, and temporary resources

Inspect path traversal, symlinks/hard links, race conditions, normalization, permissions, archive extraction, decompression bombs, partial cleanup, temporary-file creation, file replacement, and user-controlled names. Archive filters reduce risk but do not establish general safety for hostile content.

## Network and web clients

Review timeouts, response-size limits, redirects, TLS verification, proxies, SSRF, URL parsing, credentials, retries/idempotency, cookies, debug modes, and secret-bearing logs.

## Dependencies and build system

Inspect:

- build backend and build requirements;
- dependency resolver and lock policy;
- unpinned or floating VCS/direct URLs;
- extra indexes and dependency confusion;
- hashes and provenance;
- editable or local-path dependencies;
- arbitrary code execution during builds;
- plugins and entry points loaded from dependencies;
- licences, advisories, abandoned dependencies, and transitive native code;
- source versus wheel trust and platform tags.

Repository policy determines accepted tools. Do not install an auditor, scanner, resolver, or build backend silently.

## Native boundaries

Trigger the dedicated native-extension review for C/C++, Cython, cffi, ctypes, PyO3/maturin, shared libraries, manual GIL/thread-state management, buffer protocol, or ABI claims.

## Evidence

As applicable, use dependency/source inventory, lock and artifact digests, static inspection, hostile fixtures, path/archive tests, subprocess tests, secret scanning, isolated builds, package-content inspection, and release provenance. Distinguish unavailable tool from a clean result.

Return concrete exploit or failure paths, affected assets, confidence, severity, evidence, containment, remediation, and regression tests. Do not broaden the review beyond assigned trust boundaries without routing a new charter.
