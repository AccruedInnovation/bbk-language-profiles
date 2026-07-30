# TypeScript/JavaScript typed profile dispatch

Version `0.1.0-alpha.3` implements `bbk.profile-capability.v1` for six read-only operations: `state-effect`, `state-effect-inventory`, `state-effect-review`, `review-context`, `review-lens`, and `evidence-adapter`.

The generic StateDecisionEffectDesign, ReviewManifest, AssuranceContract, candidate identity, evidence eligibility, finding lifecycle, aggregation, locks, and Blueprint authority remain outside this profile. A profile operation status reports execution of the profile procedure; it never establishes generic assertion success.

## Lens mapping

- `architecture-boundary` → `comprehensive-analysis-tsjs`
- `interface-consumer-compatibility` → `tsjs-api-module-package-review`, `tsjs-type-contract-review`, `tsjs-runtime-data-contract-review`
- `implementation-structure` → `tsjs-implementation-structure-review`
- `state-concurrency-effect-recovery` → `tsjs-async-resource-failure-review`
- `security-privacy-supply-chain` → `tsjs-security-supply-chain-review`
- `test-evidence` → `tsjs-test-strategy-review`
- `operations-performance-resource` → `tsjs-operational-release-review`
- `package-install-migration-release` → `tsjs-api-module-package-review`, `tsjs-operational-release-review`

## Path and authority rules

Input paths are relative to the request package. `BBK_PROFILE_SOURCE_ROOT` supplies the exact read-only subject root and is excluded from stable result identity. Qualified read-only tool permission never authorizes installation, mutation, network effects, publication, deployment, controller action, or secret access.
