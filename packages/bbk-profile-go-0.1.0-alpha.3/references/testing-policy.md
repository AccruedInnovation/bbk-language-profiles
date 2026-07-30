# Go testing policy

Choose the cheapest method that proves the assertion. Techniques are complementary:

- focused package and external-package tests;
- integration, subprocess, HTTP server, database, and platform tests;
- race-enabled execution for exercised concurrency paths;
- `testing/synctest` for controlled time and contained goroutine behavior when supported;
- native fuzzing and persistent crash corpora;
- property, state-machine, differential, and metamorphic tests;
- deterministic failpoints and restart/recovery tests;
- coverage for gap discovery;
- mutation testing for high-value assertion strength;
- benchmarks and profiles for performance claims.

Candidate acceptance declares cache policy. `-count=1` or an equivalent repository command is normally used when fresh execution is part of the claim. Retries preserve every attempt and may produce `FLAKY`; they never erase an earlier failure.
