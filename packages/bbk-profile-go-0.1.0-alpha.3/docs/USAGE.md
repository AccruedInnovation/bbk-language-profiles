# Usage

## Ordinary resolution

Routine private work stays minimal:

```bash
bbk-go resolve --root . --role worker --task-profile implementation --assurance-tier routine --path internal/cache/cache.go
```

## Structure projection

```bash
bbk-go structure --root . --contract .bbk/contracts/implementation-structure.json \
  --role architect --task-profile implementation-structure --assurance-tier consequential
```

The output includes the generic input digest, static preflight digest, Go topology, type guidance, state/lifecycle ownership, fixed and delegated decisions, review selection, limitations, and output digest.

## Execution-slice projection

```bash
bbk-go slice --root . --slice .bbk/slices/consumer-path.json \
  --role planning_wayfinder --task-profile execution-slicing --assurance-tier material
```

A horizontal foundation slice requires a named feasibility or safety risk, an inspectable touchpoint of its own, and the next integrated slice it enables.

## Planned/actual review

```bash
bbk-go inventory --root . > actual-go-structure.json
bbk-go structure-review --root . \
  --contract .bbk/contracts/implementation-structure.json \
  --candidate .bbk/candidates/C-17/candidate.json \
  --actual-inventory actual-go-structure.json \
  --assurance-tier consequential
```

The static inventory can identify packages, files, exported declarations, and runtime-lifecycle signals. Fixed-decision conformance often needs explicit inventory evidence or a focused reviewer; absence of such evidence is not proof.

## Resolution with alpha.4 objects

```bash
bbk-go resolve --root . --role reviewer --assurance-tier consequential \
  --contract .bbk/contracts/implementation-structure.json \
  --slice .bbk/slices/first-consumer.json
```

The effective profile lock contains generic contract/slice digests and Go projection digests.
