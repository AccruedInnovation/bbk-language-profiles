# Qualification

`bbk-profile-rust 0.1.0-alpha.3` is package-qualified against the exact supplied BBK `0.1.0-alpha.8` core and the `bbk.profile-capability.v1` protocol.

## Completed package qualification

- core profile inspection: valid profile, compatible BBK/Python requirements, strict package manifest, typed-v1 dispatch declarations;
- exact alpha.8 schemas copied byte-for-byte and validated;
- six operations dispatched through the alpha.8 core with valid request and result envelopes;
- State–Decision–Effect `NONE`, `INLINE`, and `CONTRACT` routing and profile-specific inventory/review findings;
- bounded review context, focused supported lens routing, unsupported generic lens handling, and prior-finding visibility;
- valid, incomplete, stale, wrong-subject, and redacted EvidenceReceipt v2 adaptation;
- request, package, source, input, subject, and authority negative cases;
- OMP mock registration and adjacent CLI invocation;
- inherited alpha.2 behavior and installer/package regression coverage;
- 32 tests executed: 32 passed; no tests skipped (10 alpha.8 dispatch tests plus 22 inherited/successor tests);
- all 280 skill files verified byte-identical to alpha.2;
- two independent byte-identical release builds and a byte-identical clean-extraction rebuild;
- ZIP duplicate/path-traversal/CRC/symlink/mode/order/timestamp/cache-leakage audit;
- user/project install, forced-upgrade backup, and uninstall preservation exercised by the inherited suite.

## Not claimed by package qualification

Package qualification does not establish live compatibility for every toolchain, runtime, target, package manager, operating system, IDE, controller, browser, deployment environment, extension, external service, or future OMP/BBK revision. Those claims require separate evidence bound to exact environment and dependency identities.

For live qualification, follow `LIVE-QUALIFICATION-PLAN.md` and preserve the resulting evidence as exact-subject `bbk.evidence-receipt.v2` records.
