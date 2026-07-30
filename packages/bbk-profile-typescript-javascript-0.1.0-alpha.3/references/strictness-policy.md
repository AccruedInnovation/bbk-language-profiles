# TypeScript and checked-JavaScript strictness policy

Strictness is a declared project contract and migration path, not a universal toggle.

## Language modes

- `typescript-strict` — semantic checking runs and `strict` is enabled for the affected package.
- `typescript-partially-strict` — TypeScript is checked but material strictness is intentionally disabled or inherited incompletely.
- `typescript-transpile-only` — TypeScript syntax is transformed or executed without authoritative semantic checking.
- `javascript-checked` — JavaScript is checked through `checkJs`, `@ts-check`, JSDoc or an equivalent configured checker.
- `javascript-unchecked` — no authoritative static type gate is identified.
- `mixed` — packages or paths use different modes.

## Ratchet rules

- Preserve repository policy unless the work explicitly changes it.
- New or touched code may adopt a stricter local contract when it does not create misleading mixed semantics.
- Enabling `strict`, `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`, or similar options across an existing public package is a compatibility and migration task.
- `skipLibCheck` may be a pragmatic dependency boundary but must not hide local declaration defects.
- `@ts-expect-error` is preferable to an unbounded ignore when a specific expected diagnostic is part of the contract; stale suppressions should fail where tooling supports it.
- `any`, assertions, non-null assertions and ambient declarations require contextual review rather than automatic prohibition.

A transpile-only project can still have excellent runtime validation and tests, but the profile must not describe it as compiler-verified.
