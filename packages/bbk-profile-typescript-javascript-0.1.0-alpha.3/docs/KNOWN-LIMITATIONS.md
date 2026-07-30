# Known limitations

- Static/package qualification does not execute arbitrary project toolchains or lifecycle scripts.
- Automatic actual inventory proves paths and package metadata; semantic contract conformance needs explicit inventory, tool evidence or focused review.
- TypeScript AST, compiler API and bundler-specific shape extraction are intentionally not required at resolution time.
- Framework-specific component and routing semantics remain project-specific.
- Live compatibility with the exact installed BBK core, OMP build, provider configuration, and project toolchain requires qualification in the target installation.
- Browser/device, Bun, Deno, Workers, Electron, native addons, WASM and React Native remain conditional or unqualified as documented.
- The profile projects only its TS/JS portion of a mixed socio-technical slice.
