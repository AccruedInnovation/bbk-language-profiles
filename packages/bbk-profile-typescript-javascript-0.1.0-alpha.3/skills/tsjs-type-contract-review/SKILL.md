---
name: tsjs-type-contract-review
description: Review TypeScript and checked-JavaScript static contracts, declarations, inference, narrowing, escape hatches, strictness, and public type compatibility against an exact candidate and assertion set.
---

# TS/JS Type Contract Review

Review compile-time contracts only as far as the configured checker and consumer fixtures support them. Do not confuse type success with runtime validation or artifact loading.

## Bind the checker contract

Record:

- exact TypeScript CLI/compiler API/language-service identities where they differ;
- `tsconfig`/`jsconfig` inheritance and project-reference graph;
- affected package and consumer configs;
- `strict`, `allowJs`, `checkJs`, `noCheck`, `skipLibCheck`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `useUnknownInCatchVariables`, and related options;
- module, module resolution, target, lib, JSX, decorators, declaration, and composite settings;
- whether emit is separate from checking;
- public declaration generation and compatibility policy.

If semantic checking is not configured, return that limitation explicitly. Do not manufacture a type-safety pass from transpilation.

## Review areas

### Escape hatches

Inspect applicable uses of:

- explicit and implicit `any`;
- unsafe `unknown` narrowing;
- `as`, double assertions, non-null assertions;
- `@ts-ignore`, `@ts-expect-error`, `@ts-nocheck`;
- ambient declarations and module augmentation;
- broad index signatures;
- unchecked dynamic property access;
- `skipLibCheck` implications;
- generated declarations whose source contract is unclear.

An escape hatch is not automatically a defect. Evaluate its trust boundary, local rationale, public leakage, tests, and removal condition.

### Domain and state modeling

Check:

- discriminated unions and exhaustive handling;
- invalid state combinations;
- primitive identifiers with material confusion risk;
- optional, absent, `undefined`, and `null` semantics;
- state transitions enforced only by call ordering;
- overly broad booleans or partial objects;
- variance, covariance, and callback parameter assumptions where material;
- whether generics preserve or erase useful relationships.

### Public type surface

Review:

- exported functions, classes, values, types, interfaces, namespaces, and modules;
- declaration paths versus runtime paths;
- inferred public return types that expose implementation details;
- overload implementation compatibility;
- conditional and mapped type behavior;
- generic defaults and constraints;
- nominal/branding expectations;
- source compatibility for existing consumers;
- JavaScript/JSDoc consumer behavior where claimed.

### Narrowing and control flow

Check custom type predicates, assertion functions, discriminant logic, catch variables, truthiness narrowing, and impossible branches. A type predicate must be justified by runtime evidence, not merely silence checker errors.

## Evidence methods

Use only applicable methods:

- project semantic type check;
- targeted consumer compilation;
- expected-success and expected-failure type fixtures;
- declaration emit and comparison;
- API/declaration extraction where repository-qualified;
- JavaScript/JSDoc consumer fixture;
- supported TypeScript-version matrix;
- compile-only regression for a reported inference or overload defect.

A snapshot of `.d.ts` text is not sufficient when equivalent declarations may reorder or when consumer behavior is the real assertion. Prefer semantic consumer fixtures for important contracts.

## Strictness changes

Treat enabling strictness options as a migration:

1. identify affected packages and consumers;
2. separate real modeling defects from dependency/tooling noise;
3. estimate suppression or compatibility burden;
4. avoid unrelated mass edits;
5. pin the intended policy in repository configuration;
6. preserve a regression fixture for material discoveries.

Do not recommend “enable every strict flag” as a context-free refactor.

## Output

Return exact assertions and findings. Classify each as:

- checker configuration gap;
- public type compatibility defect;
- unsafe trust transition;
- domain/state modeling weakness;
- declaration/runtime divergence;
- consumer coverage gap;
- advisory style issue.

Include checker identity, configs, commands, affected consumers, compatibility dimensions, evidence, and residual gaps. Use `PASS`, `FAIL`, `BLOCKED`, or `INCONCLUSIVE` only for the assigned type-contract assertions.
