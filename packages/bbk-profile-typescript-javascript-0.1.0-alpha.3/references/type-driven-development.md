# Type-driven development for TypeScript and JavaScript

“Type” includes more than TypeScript syntax:

- **identity** — domain, package, resource, route, message and host identities;
- **state** — valid states and transitions;
- **boundary** — exported types, JSDoc, runtime schemas, messages, declarations, package exports and consumer contracts;
- **ownership** — source-of-truth, mutation, timers, subscriptions, workers, streams, processes, caches and cancellation;
- **failure** — absence, rejection, timeout, cancellation, partial completion, stale data, degraded behavior and recovery;
- **evidence** — not-run, blocked, error, inconclusive, pass and fail.

Use discriminated unions for genuinely closed states and results. Use branded identities only when interchangeability would violate a material invariant. Use one runtime schema/parser at untrusted boundaries. Keep cancellation and cleanup explicit. Keep static and runtime/package/host evidence separate.

Add a type or abstraction only when it prevents a material invalid combination, localizes an invariant, clarifies ownership, stabilizes a boundary, improves change locality, creates a meaningful seam or hides consequential complexity.
