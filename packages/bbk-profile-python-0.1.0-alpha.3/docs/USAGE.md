# Usage

## Ordinary resolution

```bash
bbk-python resolve \
  --root . \
  --role worker \
  --task-profile implementation \
  --assurance-tier routine \
  --path src/example.py
```

Ordinary work remains minimal. Structure specialists are not selected unless the generic applicability or explicit task warrants them.

## Structure projection

```bash
bbk-python structure \
  --root . \
  --contract .bbk/contracts/ISC-001.json \
  --role architect \
  --assurance-tier material
```

The result identifies Python package/module/type/ownership/test vocabulary, selected skills, planned gates, unsupported areas, and a deterministic output digest.

## Execution-slice projection

```bash
bbk-python slice \
  --root . \
  --slice .bbk/slices/ES-001.json \
  --contract .bbk/contracts/ISC-001.json \
  --role worker-designer
```

A slice projection identifies a real touchpoint, dependency closure, candidate and validation boundary, evidence subject, and scaffolding disposition. It does not execute the slice.

## Planned-versus-actual structure review

```bash
bbk-python structure-review \
  --root /path/to/candidate-checkout \
  --contract .bbk/contracts/ISC-001.json \
  --candidate .bbk/candidates/C-001/manifest.json
```

The CLI derives a bounded static inventory when no inventory is supplied. For state ownership, runtime validation, packaging, async cancellation, process behavior, or fixed prose decisions, supply an evidence-backed inventory:

```bash
bbk-python structure-review \
  --root /path/to/candidate-checkout \
  --contract contract.json \
  --candidate candidate.json \
  --actual-inventory python-actual-inventory.json
```

## Resolve with generic objects

```bash
bbk-python resolve \
  --root . \
  --role reviewer \
  --assurance-tier material \
  --structure-contract contract.json \
  --execution-slice slice.json
```

The effective profile lock includes the generic contract/slice digests and Python projection digests.

## OMP

```text
/bbk:python
/bbk:python:preflight
/bbk:python:gates material
/bbk:python:structure path/to/contract.json
/bbk:python:slice path/to/slice.json path/to/contract.json
/bbk:python:structure-review contract.json candidate.json inventory.json
```
