# Live OMP and toolchain qualification plan

Package qualification and live environment qualification are deliberately separate. Review Assurance dispatch is `supported`; any native compiler/runtime/tool evidence remains separately environment-qualified.

## Preconditions

- Pin the exact BBK `0.1.0-alpha.8` package, this profile ZIP and digest, OMP build/patch identity, operating system, language or domain toolchain, repository revision, lockfiles, and credentials/effect policy.
- Install or activate no tool merely because this profile names it. Missing optional tools remain unavailable; required tools produce a bounded blocked result.
- Use a disposable or explicitly authorized workspace and preserve the exact subject digest and request package.

## Qualification sequence

1. Verify the profile package manifest and SHA-256, then resolve it through BBK Alpha.8.
2. Load the OMP extension and verify all legacy plus six typed tools/commands register without collision.
3. Invoke each typed operation through both the direct controller and OMP surface using the same request files; compare stable result digests and payloads.
4. Run the repository-authoritative format, compile/typecheck/static-analysis, test, model/trace, package, and consumer checks applicable to the assigned lens.
5. Adapt native outputs to EvidenceReceipt v2 while preserving command, exit status, subject, time, toolchain, environment, freshness, completeness, redaction, and limitations exactly.
6. Exercise cancellation, timeout, duplicate/retry, stale input, wrong subject, partial evidence, unavailable tool, and interrupted execution cases.
7. Re-run on a clean extraction and, where claimed, on each supported operating system/toolchain combination.
8. Record a separate live qualification report bound to the exact environment and evidence archive. Do not modify this immutable package in place.

## Acceptance

- Package/protocol qualification may pass while a native environment remains unqualified.
- A live capability is supported only for the exact qualified environment closure.
- No profile result grants mutation, deployment, publication, controller, licence, secret, network, completion, readiness, or release authority.

## Declared limitations

- The profile must not install or select a Rust toolchain.
- Types and compilation do not prove runtime input validity, persistence, cancellation, recovery, or operational behavior.
- Unsafe, concurrency, performance, package, and supply-chain methods remain trigger-based rather than universal.
