# Support matrix

| Domain | Initial status | Notes |
|---|---|---|
| Node.js application/service | Primary | Type/runtime, async/resource, configuration, build and operational checks |
| Node.js CLI | Primary | Packed install, bin/shebang, exit, signal and cleanup behavior |
| ESM library/package | Primary | Exports, declarations, clean pack and consumer fixtures |
| Browser application/library | Primary | Production bundle, real-browser, security and accessibility concerns |
| Strict/checked TypeScript | Primary | Exact checker configuration and public type contracts |
| Checked JavaScript | Primary | `checkJs`, `@ts-check` and JSDoc are first-class; migration to `.ts` is not presumed |
| Mixed TS/JS workspace | Primary | Per-package language mode and package-boundary analysis |
| Monorepo/workspace | Primary | Static package graph, config inheritance and hoisting-risk preflight |
| OMP extension | Primary with exact-host fixture | Syntax alone is insufficient; live host behavior remains environment-qualified |
| Dual ESM/CommonJS | Conditional | Additional runtime, declaration and package-state compatibility surface |
| Bun or Deno production runtime | Conditional | Requires exact runtime and package/tooling qualification |
| Edge/Worker runtime | Conditional | Requires host API, module, resource and deployment qualification |
| SSR/hydration | Conditional | Requires server/client contract and real-browser evidence |
| Electron | Conditional | Main/renderer/preload boundaries and packaging need host-specific review |
| Native addon | Conditional | JS wrapper is covered; native implementation needs its own language/toolchain profile |
| WASM wrapper | Conditional | Host/memory/ABI and packaging boundaries require project evidence |
| React Native | Unqualified | Requires mobile/runtime-specific profile and devices |
| Hostile-code sandboxing | Unqualified | Runtime permission features are not assumed to be a security sandbox |
| Universal cross-runtime package | Unqualified | Each claimed runtime/condition requires explicit consumer evidence |

## Alpha.4 implementation-structure support

The profile reports `implementation_structure.status = supported` for the primary and conditional subjects above when the generic BBK contract is valid and the subject is materially TypeScript/JavaScript. The projection covers package/module topology, entry points and export maps, declaration and runtime-schema contracts, state/effect/async-resource ownership, generated artifacts, build outputs, test seams and consumer touchpoints.

Support remains bounded: adjacent native, infrastructure, hardware, organizational or operational subjects are returned as explicit adjacent obligations rather than being claimed by this language profile. Exact private file layout is delegated unless a generic fixed decision or public/shared contract makes it consequential.
