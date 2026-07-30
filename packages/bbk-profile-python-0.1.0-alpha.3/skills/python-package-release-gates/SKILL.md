---
name: python-package-release-gates
description: Design and review clean Python sdist, wheel, installed-artifact, entry-point, resource, metadata, compatibility, provenance, and rollback gates for libraries and applications.
---

# Python Package and Release Gates

Use for distribution, publication, installation, release, or deployment artifact claims.

## Subject chain

Bind the complete chain:

```text
exact source candidate
  → isolated declared-backend build
  → sdist
  → wheel
  → artifact inspection
  → clean installation
  → tests outside checkout
  → entry-point/resource verification
  → release provenance and disposition
```

Do not treat these subjects as interchangeable.

## Library package gates

As applicable:

1. validate `pyproject.toml` and declared backend requirements;
2. build sdist and wheel without undeclared source mutation;
3. inspect package names, versions, metadata, licences, README, dependencies, markers, extras, and `Requires-Python`;
4. inspect sdist/wheel contents, package data, stubs, `py.typed`, scripts, and entry points;
5. build a wheel from the sdist;
6. install the wheel into a clean environment;
7. import and test outside the checkout;
8. test selected supported Python/platform/extras configurations;
9. verify public runtime and typing compatibility where promised;
10. bind artifact digests and build environment.

## Application and service gates

Also inspect startup commands, configuration, resources, native libraries, image/package layout, version output, migrations, rollback, signals, shutdown, non-root/read-only behavior, and operational diagnostics.

## Reproducibility classification

State which claim applies:

- exact reproducible bytes;
- equivalent normalized artifact contents;
- semantically equivalent installed behavior;
- fresh isolated build receipt only.

Do not demand byte identity from inherently nondeterministic tooling without an explicit release requirement.

## Dependency policy

Libraries usually declare compatible ranges; applications usually bind a complete environment. Do not impose exact application-style pins on reusable libraries or loose library-style resolution on deployed applications without a declared policy.

## Result

Return exact source, sdist, wheel, installed environment, metadata, entry points, package files, test receipts, unsupported configurations, provenance, and residual limitations. A successful package build without installed tests is incomplete evidence.
