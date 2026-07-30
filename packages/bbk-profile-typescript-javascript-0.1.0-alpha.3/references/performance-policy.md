# TypeScript/JavaScript performance policy

Do not prescribe optimization from syntax alone. Bind a workload, environment and measurable criterion.

Relevant dimensions include:

- algorithmic complexity and data volume;
- event-loop delay and long tasks;
- startup/cold-start and module loading;
- bundle, chunk and asset size;
- network waterfalls, caching and over-fetching;
- serialization/parsing and data copying;
- garbage-collection pressure and memory retention;
- streams and backpressure;
- worker/process overhead;
- type-check, build and test time;
- source-map and diagnostic cost.

A performance finding should include baseline, workload, samples, variance, environment, attribution and a regression threshold. Do not recommend memoization, alternate frameworks, workers, code splitting, pooling, caching or native addons without evidence that the change addresses the measured bottleneck and preserves correctness.
