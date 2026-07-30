---
name: python-typing-contract-review
description: Review a Python static typing and runtime annotation contract, including checker configuration, public stubs, py.typed, Any leakage, decorators, overloads, generics, version/platform branches, and annotation introspection.
---

# Python Typing Contract Review

Use when a project relies materially on static typing, publishes typing information, changes public annotations, adds decorators/generics/protocols, or consumes annotations at runtime.

## Bind the contract

Record:

- checker or checkers actually supported;
- exact checker versions and configuration;
- Python version and platform targets used by the checker;
- files and packages in scope;
- strictness, exclusions, ignores, plugins, and generated stubs;
- whether annotations are runtime-consumed;
- whether typing is a public compatibility surface.

## Static typing review

Inspect:

- implicit and explicit `Any` at material boundaries;
- untyped decorators and callables;
- incomplete third-party stubs;
- overload coverage and implementation agreement;
- `Protocol` and structural assumptions;
- generic bounds, variance, constraints, and defaults;
- `TypedDict` required/optional/read-only evolution;
- narrowing, pattern matching, `TypeGuard`, and `TypeIs` behavior;
- unreachable, redundant, and ignored diagnostics;
- platform/version-conditional definitions;
- generated code and checker plugins;
- public stub/runtime export agreement.

Do not recommend full typing merely as a percentage target. Prioritize stable public boundaries, high-value domain logic, dangerous dynamic seams, and code where typing materially improves change safety.

## Runtime annotation review

Annotations may be deferred, stringized, transformed, or evaluated by frameworks and introspection. Inspect:

- `typing.get_type_hints`, annotation-evaluation utilities, and custom schema/DI frameworks;
- forward references and import side effects;
- arbitrary code execution during annotation resolution;
- version-specific evaluation semantics;
- mutation of `__annotations__`;
- runtime validators that diverge from static types.

Keep these separate:

```text
checker acceptance
runtime value validation
runtime annotation introspection
serialization/schema generation
```

## Public compatibility

Assess changes to:

- parameter and return annotations;
- overloads and generics;
- public protocols and `TypedDict`;
- exported type aliases and enum/literal values;
- stub-only symbols;
- `py.typed` and distribution contents;
- supported checker and Python versions.

A runtime-compatible change can still break typed consumers.

## Validation

Use repository-configured checkers. A second checker is warranted only for a declared compatibility promise. Validate installed distributions or stubs when the public typing surface is packaged. Record checker identity, configuration digest, target version/platform, and ignored diagnostics.

Return exact assertion results, evidence, unsupported checker/configuration combinations, runtime-versus-static gaps, and the smallest compatible repair. Do not treat annotations as runtime enforcement.
## Structure-contract use

Distinguish static typing contracts from runtime validation and operational evidence. Review public annotations, stubs, `py.typed`, protocols, typed mappings, enums, dataclasses, exception/result forms, and runtime schemas only where the generic contract makes them shared, public, or fixed. Do not turn type-driven development into wrapper or protocol ceremony.
