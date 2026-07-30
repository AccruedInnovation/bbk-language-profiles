# Python performance policy

Performance recommendations require a declared workload and evidence. Measure wall time, CPU, allocation, memory retention, I/O, database/network round trips, import/startup cost, serialization, concurrency, and resource ceilings as applicable.

Do not prescribe `__slots__`, generators, async, multiprocessing, free-threading, native extensions, caching, a faster JSON library, or a different data representation without measuring the responsible bottleneck and accounting for semantic, operational, portability, and maintenance effects.

Benchmark evidence records interpreter, environment, dependency lock, workload, warmup, samples, variance, baseline, and resource conditions.
