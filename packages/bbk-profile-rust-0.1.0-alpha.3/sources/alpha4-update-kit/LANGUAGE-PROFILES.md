# Language and domain profiles in alpha.4

Alpha.4 retains the alpha.3 host-neutral profile model and adds an optional `implementation_structure` capability.

A profile may declare:

```json
{
  "capabilities": {
    "implementation_structure": {
      "status": "supported",
      "artifact_kinds": ["module", "type", "test"],
      "contract_kinds": ["public-api", "state-owner"],
      "type_concepts": ["nominal-type", "state", "effect"],
      "touchpoint_kinds": ["cli", "api", "test"],
      "trigger_hints": ["public-api", "concurrency", "migration"]
    }
  },
  "entrypoints": {
    "structure": ["{python}", "tools/profile.py", "--json", "structure"],
    "slice": ["{python}", "tools/profile.py", "--json", "slice"],
    "structure_review": ["{python}", "tools/profile.py", "--json", "structure-review"]
  }
}
```

The profile may produce a namespaced projection under `profileProjections.<profile-id>`. It must not rewrite generic identity, authority, fixed decisions, work scope or assurance.

## Legacy alpha.3 profiles

An alpha.3 profile without this capability remains valid for ordinary preflight, resolution and gate planning. When structure inputs are supplied, alpha.4:

1. validates the generic contract and slices;
2. records their digests in the effective resolution and lock;
3. reports profile structure support as `legacy-unprojected`;
4. does not invent profile-specific claims.

Profile authors should release an independently versioned successor rather than editing an installed alpha.1 package in place.

## Required profile posture

Repository-declared toolchains, commands and conventions remain authoritative within their legitimate scope. A profile may add procedure, review criteria and gate recipes. It may not grant effects, expand work scope, reduce assurance or declare a pass.
