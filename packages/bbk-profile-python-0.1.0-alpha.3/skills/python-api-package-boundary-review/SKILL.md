---
name: python-api-package-boundary-review
description: Review a Python package, public runtime API, import surface, distribution metadata, entry points, resources, typing surface, and compatibility obligations against an exact candidate.
---

# Python API and Package Boundary Review

Use for public libraries, package layout changes, module moves, exports, entry points, plugins, distribution metadata, resource files, dependency markers, or compatibility-sensitive changes.

## Bind the subject

Record:

- exact candidate and source revision;
- package/distribution name and version source;
- source-tree, editable, wheel, or sdist-derived subject;
- supported Python/interpreter/platform range;
- selected extras and dependency groups;
- public API and compatibility claims;
- exact assigned assertions.

Do not mutate the candidate.

## Review surfaces

### Runtime and import API

- importable package and module paths;
- `__all__`, package re-exports, lazy exports, `__getattr__`, and `__dir__`;
- public classes, functions, constants, exceptions, decorators, descriptors, and protocols;
- call signatures, defaults, positional/keyword behavior, context-manager and iterator semantics;
- module moves, aliases, deprecation path, and import-time side effects;
- namespace packages and package-name collisions;
- behavior when imported outside the checkout root.

### Typing distribution surface

- `.pyi` files and runtime/stub agreement;
- `py.typed` inclusion;
- public `TypedDict`, `Protocol`, overload, generic, and annotation behavior;
- checker and Python-version conditional exports;
- runtime annotation consumers;
- changes that pass runtime tests but break static consumers.

Do not treat checker output as runtime validation.

### Distribution contents

Inspect `pyproject.toml`, build backend, dynamic metadata, package discovery, included/excluded packages, data files, licences, README, scripts, entry points, plugins, dependency markers, extras, and `Requires-Python`.

Compare:

```text
source tree
sdist contents
wheel contents
installed files
runtime imports and resources
```

Checkout-only tests do not prove distribution correctness.

### Entry points and plugins

- console and GUI script names;
- callable targets and argument behavior;
- exit codes, stdout/stderr, help, and version behavior;
- plugin group names, discovery, ordering, duplication, and failure isolation;
- optional dependency and missing-plugin behavior;
- direct and transitive import side effects.

### Compatibility dimensions

Assess separately:

```text
runtime source API
import path
exception behavior
typing/stub API
serialization and persisted data
CLI
configuration
entry-point/plugin
package metadata and dependency markers
wheel/interpreter/platform
```

A tool or source diff may support, but cannot replace, this multidimensional assessment.

## Validation expectations

As applicable:

- build sdist and wheel through the declared backend in isolation;
- inspect artifact contents and metadata;
- install the wheel into a clean environment;
- import from outside the repository;
- test public examples, entry points, resources, and selected extras;
- build a wheel from the sdist and compare the declared behavior;
- run downstream compile/import fixtures for public API and typing claims;
- verify deprecation and migration behavior.

## Findings

Return `PASS`, `FAIL`, `BLOCKED`, or `INCONCLUSIVE` for each assigned assertion. Include exact artifact digests, compatibility surfaces, evidence reused, evidence rerun, omissions, and the smallest valid repair or migration route. Do not infer release readiness from a successful local import.
## Structure-contract use

When a structure contract applies, map public runtime imports, typing exports, package metadata, entry points, plugin groups, wheel/sdist subjects, serialization forms, and consumer fixtures to its exact key contracts and fixed decisions. Do not require exact private module-tree equality. Public import or package-consumer drift is material only when it affects an explicit fixed or shared contract.
