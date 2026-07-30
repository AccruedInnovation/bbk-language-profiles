---
name: tsjs-operational-release-review
description: Review TypeScript/JavaScript build, artifact, configuration, deployment, migration, source-map, observability, startup, shutdown, rollback, package, CLI, service, plugin, and host readiness.
---

# TS/JS Operational and Release Review

Review the exact artifact and environment intended for use. A source checkout passing tests is not release evidence.

## Bind the release subject

Identify:

- application, service, CLI, library, browser bundle, plugin, extension, worker, or package;
- exact source candidate and profile lock;
- runtime versions and operating systems;
- package manager and lockfile;
- build, declaration, bundle, minification and source-map configuration;
- package/container/archive subject;
- deployment and rollback mechanism;
- configuration and secret sources;
- observability and support expectations;
- migration and compatibility obligations.

## Build and artifact integrity

Check:

- clean/frozen installation;
- clean production build;
- separation of type checking and emit;
- generated artifact consistency;
- package/archive inclusion set;
- runtime assets and native/WASM files;
- reproducible or at least provenance-bound output;
- source maps, licences and notices;
- version reporting and build identity;
- no dependency on unpublished source paths, workspace hoisting, or developer-only aliases.

## Startup, shutdown and failure

For services, CLIs, workers and extensions review:

- missing and invalid configuration;
- startup ordering and partial initialization;
- dependency unavailable behavior;
- readiness versus liveness;
- signal and cancellation handling;
- graceful drain and timeout policy;
- child/worker/resource cleanup;
- exit codes and stdout/stderr;
- crash diagnostics and restart behavior;
- late async work after shutdown.

## Configuration

- Resolve configuration once at a boundary where practical.
- Distinguish absent, empty and invalid values.
- Record precedence among files, environment, flags, remote config and defaults.
- Prevent secrets from entering canonical output, logs, client bundles or source maps.
- Validate configuration before irreversible effects.
- Include a safe diagnostic view that redacts sensitive values.

## Deployment, migration and rollback

Review:

- compatible old/new versions and mixed-version windows;
- database or storage migration ordering;
- feature flags and staged rollout;
- cache/schema compatibility;
- deployment interruption and retry;
- rollback after partial migration;
- package or binary side-by-side behavior;
- stale worker, service worker or CDN cache behavior;
- release withdrawal or revocation.

## Observability

Require proportional evidence for:

- structured errors and correlation;
- startup and shutdown state;
- dependency and queue health;
- event-loop delay or saturation where material;
- memory/resource growth;
- retry and duplicate effects;
- user-visible failures;
- source-map availability and access control;
- version/build identity;
- privacy and redaction.

## Subject-specific gates

### Library/package

- pack dry run and archive inspection;
- clean consumer installation;
- declared runtime/module consumers;
- declaration resolution;
- licence/readme/metadata;
- publication provenance where claimed.

### CLI

- bin mapping, shebang and executable mode;
- clean install;
- help/version;
- exit codes;
- stdin/stdout/stderr;
- signals and temporary-file cleanup;
- behavior outside the source workspace.

### Service

- production build and startup;
- config validation;
- readiness/liveness;
- graceful shutdown;
- migration and rollback;
- dependency/fault scenarios;
- operational limits.

### Browser application/library

- production bundle and assets;
- supported browser load;
- CSP/source maps;
- cache/service-worker update;
- SSR/hydration where applicable;
- bundle and performance budgets.

### OMP/plugin/extension

- discovery by the exact host;
- command/tool/hook registration;
- representative invocation;
- restart/unload behavior;
- compatibility diagnostics;
- no leaked process or state.

## Output

Return release subject, environment, artifacts and digests, commands, compatibility matrix, operational findings, rollback status, unsupported configurations, and residual risk. Do not declare release authority; report whether the assigned operational assertions pass.
