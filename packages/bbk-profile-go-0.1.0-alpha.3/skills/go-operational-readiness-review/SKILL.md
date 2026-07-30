---
name: go-operational-readiness-review
description: Review a Go command or service for startup, configuration, shutdown, deployment, migration, observability, resource, rollback, and recovery readiness against exact operational assertions.
---

# Go Operational Readiness Review

Review the shipped process and environment, not merely package tests.

## Process lifecycle

Inspect:

- startup ordering, dependency checks, and partial-start cleanup;
- configuration resolution and validation;
- health, readiness, and liveness semantics;
- signal handling, cancellation, graceful shutdown, drain, and deadlines;
- goroutine, subprocess, listener, connection, and file cleanup;
- exit codes and crash diagnostics;
- restart behavior and duplicate effects.

A service should not report ready before dependencies and migrations are in the intended state. Shutdown should define what is drained, rejected, abandoned, or retried.

## HTTP/RPC operations

Review server and client timeout policies, request limits, streaming cancellation, connection reuse, redirects, proxy/header trust, TLS, backpressure, overload, and graceful shutdown.

## Configuration

Establish precedence among flags, files, environment, defaults, remote values, and runtime overrides. Make effective configuration inspectable without exposing secrets. Record behavior for missing, invalid, deprecated, and incompatible settings.

Include relevant `GODEBUG`, `GOEXPERIMENT`, build tags, target, CGO, and PGO configuration in environment identity.

## Persistence and migration

Review:

- preflight, backup, compatibility, and locking;
- forward and rollback strategy;
- mixed-version operation;
- partial migration and restart;
- transaction boundaries and external effects;
- data validation and observability;
- operator authority and recovery runbook.

## Observability

Require enough structured logs, metrics, traces, profiles, and correlation to answer:

- what operation failed;
- which dependency/configuration/version was active;
- what state may have changed;
- whether retry is safe;
- who owns recovery;
- whether the process is making progress.

Avoid secrets and unbounded high-cardinality fields.

## Resource and performance behavior

Review goroutine and queue bounds, connection pools, memory/GC limits, file descriptors, CPU, disk, network, rate limits, overload shedding, and container resource behavior. Performance claims require representative evidence.

## Deployment and rollback

Verify the actual artifact, target, tags, CGO mode, native dependencies, VCS/build metadata, PGO profile, configuration, and installation layout. Test startup, shutdown, version output, rollback compatibility, and clean removal.

## Evidence

Use clean builds, process smoke tests, signal/subprocess tests, migration/restart fixtures, representative workload, fault injection, and artifact inspection according to the assurance contract.

## Return

Return `PASS`, `FAIL`, `BLOCKED`, or `INCONCLUSIVE` by operational assertion; exact environment; failure and recovery scenarios; migration/rollback gaps; observability and resource gaps; evidence; and the smallest valid release disposition.
