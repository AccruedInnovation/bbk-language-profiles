# BBK TypeScript/JavaScript Profile 0.1.0-alpha.3 release notes

## Summary

This immutable successor updates the alpha.2 profile for BBK `0.1.0-alpha.8`. It preserves the existing language procedures and adds read-only typed State–Decision–Effect and Review Assurance integration through `bbk.profile-capability.v1`.

## Added

- six typed profile operations: `state-effect`, `state-effect-inventory`, `state-effect-review`, `review-context`, `review-lens`, and `evidence-adapter`;
- exact alpha.8 request/result, context-manifest, and EvidenceReceipt v2 contracts;
- proportional `NONE`, `INLINE`, and `CONTRACT` State–Decision–Effect routing;
- profile-specific state/effect inventory and planned-versus-actual findings;
- focused logical-lens routing without mandatory comprehensive-review fanout;
- bounded, digest-stable review-context compilation with declared omissions and prior-finding visibility;
- native/legacy evidence adaptation that preserves source digests and never invents command, status, time, toolchain, environment, subject, or completeness facts;
- six additive OMP tools and commands backed by the same profile controller;
- alpha.8 fixtures, negative cases, compatibility checks, migration guidance, and reproducible release evidence.

## Compatibility

- requires BBK `0.1.0-alpha.8`;
- installs beside alpha.2; project owners deliberately re-resolve and update locks;
- all alpha.2 skill files remain byte-identical;
- existing entrypoints and direct skill use remain available;
- Review Assurance maturity: `supported`.

## Authority boundary

The profile adds procedures, projections, and evidence adapters only. It grants no tools or effects, cannot mutate the subject, cannot declare generic assertion pass/readiness/release, and cannot replace generic BBK or Blueprint authority.

## Qualification boundary

Package qualification and live toolchain/environment qualification remain separate. The release is package-qualified against the supplied BBK alpha.8 core; it does not claim every language toolchain, target, runtime, IDE, controller, deployment platform, browser, package manager, or external service has been live-qualified.

## Profile limitations

- The profile must not select or install a runtime, package manager, TypeScript version, or build tool.
- Static typing does not prove runtime data validity or host/browser behavior.
- Dual-package, edge, Electron, native-addon, React Native, and cross-runtime claims remain conditional or explicitly blocked when unqualified.
