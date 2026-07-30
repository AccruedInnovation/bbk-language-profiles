# Runtime, module and artifact model

The effective TS/JS product is defined by several independently versioned tools and contracts:

```text
source language mode
  → semantic checker
  → transformer/emitter
  → bundler/minifier
  → declaration emitter
  → package/archive/container
  → runtime/host
  → actual consumer
```

Record each separately. A project may use different TypeScript versions for command-line checking, compiler APIs, language services and lint integrations.

## Module contract

Capture:

- package `type`;
- `.ts/.mts/.cts` and `.js/.mjs/.cjs` use;
- TypeScript `module` and `moduleResolution`;
- `verbatimModuleSyntax` and interop settings;
- `exports`, `imports`, `types`, `typesVersions`, `main`, `module`, `browser` and `bin`;
- conditions and subpaths;
- dynamic import and top-level await;
- path aliases and runtime equivalents;
- supported ESM/CommonJS/bundler consumers.

Do not add dual publication merely for compatibility optics. It creates two runtime identities and often two declaration surfaces that need independent evidence.

## Runtime-native TypeScript

A runtime executing TypeScript syntax may erase types without running the project's semantic checker or respecting its complete `tsconfig`. Treat runtime-native execution as an emit/runtime mechanism, not as proof of type correctness.
