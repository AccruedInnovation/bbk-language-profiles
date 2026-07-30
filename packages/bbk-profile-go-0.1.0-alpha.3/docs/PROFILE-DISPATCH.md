# Go typed profile dispatch

Version `0.1.0-alpha.3` implements `bbk.profile-capability.v1` for six read-only operations: `state-effect`, `state-effect-inventory`, `state-effect-review`, `review-context`, `review-lens`, and `evidence-adapter`.

The generic StateDecisionEffectDesign, ReviewManifest, AssuranceContract, candidate identity, evidence eligibility, finding lifecycle, aggregation, locks, and Blueprint authority remain outside this profile. A profile operation status reports execution of the profile procedure; it never establishes generic assertion success.

## Lens mapping

- `architecture-boundary` → `comprehensive-analysis-go`
- `interface-consumer-compatibility` → `go-api-module-boundary-review`
- `implementation-structure` → `go-implementation-structure-review`
- `state-concurrency-effect-recovery` → `go-correctness-concurrency-review`
- `security-privacy-supply-chain` → `go-security-supply-chain-review`
- `test-evidence` → `go-test-strategy-review`
- `operations-performance-resource` → `go-operational-readiness-review`
- `package-install-migration-release` → `go-package-release-gates`

## Path and authority rules

Input paths are relative to the request package. `BBK_PROFILE_SOURCE_ROOT` supplies the exact read-only subject root and is excluded from stable result identity. Qualified read-only tool permission never authorizes installation, mutation, network effects, publication, deployment, controller action, or secret access.
