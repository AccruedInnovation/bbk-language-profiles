# Python compatibility policy

Compatibility is directional, scoped, environment-dependent, and evidence-linked. Evaluate at least the applicable surfaces:

```text
runtime source/API
import path and package exports
public exception behavior
typing and stubs
CLI and entry points
configuration
protocol and HTTP
serialization and persisted data
plugin contracts
dependency and optional-extra behavior
interpreter, ABI, platform, and wheel tags
deployment and migration
```

A successful import or type-check does not prove the other surfaces. Compatibility evidence must identify the exact old/new artifacts, interpreter, environment, extras, dependency resolution, and supported scope. Unknown is not compatible.
