---
name: tsjs-runtime-data-contract-review
description: Review runtime trust boundaries, parsing, validation, coercion, versioning, schemas, configuration, persistence, IPC, and external data before values become trusted TypeScript or JavaScript domain objects.
---

# TS/JS Runtime Data Contract Review

TypeScript annotations are erased. This review asks where runtime values become trusted and whether that transition is justified.

## Trigger boundaries

Apply to relevant values from:

- HTTP, RPC, GraphQL, WebSocket, webhooks, queues, and events;
- JSON, YAML, TOML, CSV, XML, binary protocols, files, archives, and form data;
- environment variables and configuration;
- database rows, cache entries, migrations, and persisted snapshots;
- CLI arguments and process input;
- browser storage, cookies, headers, URLs, and service workers;
- `postMessage`, workers, child processes, IPC, plugins, and host tools;
- third-party SDKs and generated clients;
- OMP tool, agent, or extension messages.

## Contract questions

For each material boundary identify:

```text
producer and consumer
wire or storage representation
version and compatibility policy
initial untrusted type
parser/validator/normalizer
trusted domain type
unknown-field behavior
absent/null/undefined behavior
defaulting and coercion
error and partial-success behavior
redaction and observability
migration/retry/replay behavior
```

## Review criteria

### Validation and parsing

- External values begin as `unknown`, bytes, or strings rather than an asserted domain type.
- Validation happens before business logic or persistence mutation.
- Parsing returns a trusted representation rather than a boolean followed by a second unchecked conversion.
- Coercion is explicit and does not silently turn malformed input into plausible data.
- Defaults distinguish absent input from explicit values.
- Numeric ranges, units, dates, encodings, identifiers, and precision are checked where meaningful.
- Recursive or large inputs have depth, size, and resource bounds.

### Schema and type ownership

Determine the canonical source:

```text
runtime schema generates types
types generate runtime schema
external protocol schema generates both
manually maintained contract with drift checks
```

Flag parallel mutable definitions without a deterministic consistency check.

### Compatibility

Assess independently:

- structural parse compatibility;
- semantic meaning;
- unknown/new field behavior;
- removed/renamed fields;
- enum evolution;
- default changes;
- ordering and duplicate semantics;
- version negotiation;
- persistent-data migration;
- mixed producer/consumer versions;
- rollback and replay.

### Error handling

- Invalid input fails with a stable classification.
- Error messages contain enough location/context to diagnose but do not leak secrets.
- Partial records or batched input have a declared all-or-nothing or partial-success policy.
- Retry does not duplicate committed effects.
- Invalid cached or persisted data has a repair or quarantine path.

## Testing

Select applicable evidence:

- valid/minimal/maximal examples;
- malformed and adversarial data;
- missing, null, undefined, unknown, duplicate, and extra fields;
- old/new version fixtures;
- round-trip only when round-trip is actually promised;
- differential tests against a previous parser or independent implementation;
- property or fuzz tests for parsers and decoders;
- persistence migration, downgrade, and rollback fixtures;
- actual host/plugin message fixtures.

Do not accept a compile-time type fixture as runtime-validation evidence.

## Output

For each boundary report the untrusted source, trust transition, runtime validator, canonical schema source, compatibility claim, failure behavior, tests, and exact gap. Distinguish:

```text
missing runtime validation
validation after side effects
schema/type drift
unsafe coercion/defaulting
compatibility defect
persistence/migration defect
resource-exhaustion risk
missing evidence
```

Return `PASS`, `FAIL`, `BLOCKED`, or `INCONCLUSIVE` only for assigned runtime-contract assertions.

## Implementation-structure projection

For alpha.4 contracts, identify one owner for each runtime schema/parser and its static type/declaration projection. Flag independently authored duplicate schemas, unvalidated trust-boundary assertions, moved validation after side effects, or runtime shape drift as material when they affect a fixed/shared contract. Private parser helper layout remains delegated.
