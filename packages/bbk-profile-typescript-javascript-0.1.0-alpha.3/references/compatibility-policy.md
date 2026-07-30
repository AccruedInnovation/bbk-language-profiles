# TypeScript/JavaScript compatibility policy

Compatibility is directional, scoped and evidence-linked. Do not collapse it into a single `breaking: yes/no` field.

Assess independently:

1. **Source type compatibility** — existing TypeScript or checked-JavaScript consumers still compile and infer intended types.
2. **Runtime API compatibility** — values, calls, events, errors and side effects retain their supported behavior.
3. **Module-resolution compatibility** — TypeScript, Node, bundlers and other claimed runtimes resolve supported entry points.
4. **Package-content compatibility** — the packed artifact includes required code, declarations, assets, licences and bins.
5. **Wire/schema compatibility** — serialized or network representations remain usable in the claimed direction.
6. **Persistence compatibility** — existing stored data, caches or migrations remain usable or have a qualified transition.
7. **Configuration/CLI compatibility** — flags, environment, config, exit codes and scripts retain declared behavior.
8. **Operational compatibility** — supported runtimes, browsers, deployment, resource and failure behavior remain valid.

Unknown is not compatible. Tool output such as declaration comparison or SemVer analysis is supporting evidence; actual consumer fixtures remain the strongest evidence for important public surfaces.

A package may deliberately support only ESM, only Node, or only a bounded TypeScript range. Unsupported consumers should fail clearly rather than accidentally load an incompatible path.
