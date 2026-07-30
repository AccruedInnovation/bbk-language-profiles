# `mutest-rs` integration

BBK Rust uses `mutest-rs` as its mutation-testing recipe.

## Selection

Run it only when:

- the assurance contract explicitly requires mutation testing;
- high-value deterministic logic needs test-strength evidence; or
- review identifies a material test-strategy gap that mutation testing can discriminate.

## Preconditions

- exact project-qualified `mutest-rs` revision;
- compatible pinned nightly;
- passing baseline tests;
- bounded package/target/operator scope;
- declared timeout and resource ceiling;
- effect authority for any required toolchain or dependency access already established outside the profile.

## Command shape

```bash
cargo mutest run -p <package>
```

Repository wrappers and configuration take precedence.

## Evidence

Preserve baseline outcome, tool revision, nightly, selected targets, operator/configuration set, mutant inventory, killed/surviving mutants, timeouts, crashes, unsupported cases, logs, and explicit disposition. A survivor, equivalent mutant, timeout, tool crash, and infrastructure failure are distinct outcomes.

The profile makes no universal throughput claim. Local performance observations may inform project choice but do not replace qualification of the selected revision and codebase.
