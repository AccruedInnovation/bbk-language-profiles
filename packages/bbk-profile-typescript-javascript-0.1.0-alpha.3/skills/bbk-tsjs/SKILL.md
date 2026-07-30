---
name: bbk-tsjs
description: Route TypeScript and JavaScript work through the BBK TS/JS profile. Use for repository/toolchain preflight, language-mode detection, runtime and package boundaries, proportional skill selection, gate planning, and structured worker or validator handoff.
---

# BBK TypeScript/JavaScript

Use this skill as the compact entry point. Do not load every focused review pack by default.

## Bind the effective project before reasoning

1. Locate the actual package or workspace root.
2. Identify the runtime targets: Node.js, browser, Bun, Deno, Worker, Electron, OMP, or another declared host.
3. Identify the language mode per affected package:
   - `typescript-strict`;
   - `typescript-partially-strict`;
   - `typescript-transpile-only`;
   - `javascript-checked`;
   - `javascript-unchecked`;
   - `mixed`.
4. Distinguish the tools that perform:
   - semantic type checking;
   - transformation or emit;
   - bundling;
   - declaration generation;
   - linting;
   - testing;
   - package installation and publication.
5. Record the package manager, lockfile, workspace graph, module contract, package exports, supported consumers, and repository-owned commands.
6. Prefer repository configuration and commands over generic recipes. Never install or upgrade a tool, dependency, runtime, package manager, or lockfile silently.

Use `bbk-tsjs preflight` or the `bbk_tsjs_preflight` OMP tool when available.

## Core assurance rules

- TypeScript annotations describe compiler assumptions; they do not validate runtime values.
- Type checking, transpilation, bundling, declaration emit, artifact execution, and packed-consumer behavior are separate evidence classes.
- A source workspace pass does not prove the published or deployed artifact works.
- ESM, CommonJS, conditional exports, TypeScript resolution, runtime resolution, and bundler resolution may disagree.
- Async JavaScript still has races, cancellation gaps, resource leaks, partial completion, and ordering failures.
- Dependency installation may execute lifecycle scripts or native builds and therefore remains an effectful operation.
- A Node permission policy is complementary evidence, not a hostile-code sandbox.
- Required unavailable checks are `BLOCKED`; optional unavailable checks are advisory.
- Run deterministic checks before model review. Prove each material assertion once by the cheapest sufficient method.

## Route focused work

Use only the packs justified by the exact assertion or change:

- static type quality, declarations, escape hatches, inference → `tsjs-type-contract-review`;
- external values, schemas, configuration, persistence, IPC → `tsjs-runtime-data-contract-review`;
- exports, ESM/CommonJS, package contents, declaration and consumer compatibility → `tsjs-api-module-package-review`;
- promises, cancellation, timers, streams, workers, retries, shutdown → `tsjs-async-resource-failure-review`;
- type tests, runtime tests, browser tests, property/fuzz/fault testing → `tsjs-test-strategy-review`;
- dependencies, install scripts, registries, injection, secrets, native addons → `tsjs-security-supply-chain-review`;
- build, deployment, source maps, configuration, rollback, package and host loading → `tsjs-operational-release-review`;
- DOM, accessibility, hydration, XSS/CSP, browser compatibility → `tsjs-browser-ui-review`;
- broad inherited-codebase or modernization survey → `comprehensive-analysis-tsjs`.

A broad survey identifies hotspots. It does not automatically authorize all focused reviews.

## Worker and validator separation

A worker normally receives:

- `bbk-tsjs`;
- `tsjs-development-practices`;
- exact repository conventions;
- exact work-unit scope;
- applicable deterministic gates;
- the ordinary BBK worker handoff.

A validator receives one exact candidate, exact assertions, applicable deterministic receipts, and only the focused pack or packs needed for those assertions. Do not give a worker the later validator charter merely so it can optimize for the wording.

## Return contract

Report:

- effective root, packages, runtime and language modes;
- task and assurance inputs;
- selected skills and why each applies;
- planned gates and the subject each proves;
- unsupported or unqualified configurations;
- required effects or unavailable tools;
- exact profile-lock digest when available.

This profile adds procedure and evidence expectations only. It grants no filesystem, network, credential, installation, publication, deployment, semantic, acceptance, or release authority.

## Alpha.4 implementation structure and slicing

When a generic `ImplementationStructureContract` or `ExecutionSlice` is present:

- keep the generic object authoritative;
- use `bbk-tsjs structure`, `slice`, or `structure-review` for deterministic projection;
- map artifact topology into packages, modules, entry points, export maps, declarations, runtime schemas, browser/server outputs, generated artifacts, tests, plugins, and host extensions;
- map key contracts into static types/JSDoc, runtime parsers, public declarations, package consumers, events/messages, state owners, async resources, and effect owners;
- preserve fixed decisions and delegated freedom separately;
- select `tsjs-implementation-structure-review` only for applicable planning/review roles or planned-versus-actual assertions;
- do not require a standalone structure contract for routine private work.

Profile projections and Markdown guidance are views, not BBK state. Static notation never substitutes for runtime, consumer, browser, host, human, or operational evidence.
