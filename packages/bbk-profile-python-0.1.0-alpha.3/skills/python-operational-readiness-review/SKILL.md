---
name: python-operational-readiness-review
description: Review Python application, service, CLI, worker, migration, packaging, configuration, observability, deployment, startup, shutdown, recovery, capacity, and rollback readiness.
---

# Python Operational Readiness Review

Use for deployable applications, services, CLIs, workers, scheduled jobs, migrations, configuration changes, packaging, or operational claims.

## Bind the operating environment

Record:

- exact artifact and environment;
- Python/interpreter/platform/architecture;
- dependency and lock resolution;
- process model and worker count;
- entry points and startup command;
- external services, credentials, filesystem, and network dependencies;
- deployment, migration, rollback, and recovery contract;
- assigned operational assertions.

## Startup and configuration

Inspect:

- deterministic configuration sources and precedence;
- missing, invalid, stale, conflicting, and secret values;
- environment-variable parsing and normalization;
- effective configuration visibility without secret leakage;
- import-time startup work;
- dependency and migration readiness;
- startup timeout, health, and failure diagnostics;
- version and build identity.

## Runtime operation

Review:

- process/task/thread ownership;
- signal handling and graceful shutdown;
- request/job draining;
- subprocess and pool cleanup;
- connection pools and resource ceilings;
- retries, backpressure, queues, idempotency, and duplicate delivery;
- scheduled job overlap and leader election where applicable;
- temporary storage, permissions, disk exhaustion, and read-only filesystems;
- cache lifecycle and stale data;
- degraded operation and dependency outage behavior.

## Observability

Require fit-for-purpose:

- structured events and correlation;
- actionable logs without secrets;
- metrics for workload, saturation, failures, retries, queues, and latency;
- trace context across async/process boundaries where applicable;
- health versus readiness distinctions;
- operator-visible version, configuration provenance, and dependency state;
- diagnostic preservation after crash.

Do not demand every telemetry technology. Evaluate whether operators can detect, localize, and recover from the feared failures.

## Migrations and compatibility

Inspect:

- forward and rollback paths;
- mixed-version operation;
- expand/contract sequencing;
- realistic data volume and duration;
- lock/contention behavior;
- partial failure and restart;
- backup and restore;
- irreversible steps and authority;
- deployment order across producers/consumers.

## Packaging and deployment

Verify the exact installed artifact, entry points, resources, native libraries, wheel tags, image contents, non-root behavior, and uninstall/rollback where applicable. A source checkout is not deployment evidence.

## Capacity and performance

Use declared workloads and service objectives. Inspect query count, connection pools, event-loop blocking, process/thread sizing, memory retention, startup time, queue growth, and backpressure. Require measurement before optimization claims.

Return assertion-scoped findings, failure scenarios, observed evidence, unsupported configurations, rollback/recovery gaps, and the smallest safe operational next action.
