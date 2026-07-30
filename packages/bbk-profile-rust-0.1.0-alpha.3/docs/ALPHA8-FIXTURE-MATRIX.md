# Alpha.8 profile-dispatch fixture matrix

Profile: `rust`  
Successor: `0.1.0-alpha.3`  
Required BBK: `0.1.0-alpha.8`

| Fixture family | Positive case | Negative/fault case | Primary evidence |
|---|---|---|---|
| Contract and dispatch | All six operations accept an exact request package and return `bbk.profile-capability-result.v1` | Wrong profile/version/package root/manifest/input/request digest; unknown operation | `tests/test_alpha8_dispatch.py`; request/result schemas |
| Proportionality | `NONE`, `INLINE`, and `CONTRACT` route only the required profile procedures | Missing or contradictory applicability data blocks or reports bounded findings | `design-none.json`, `design-inline.json`, `design-contract.json` |
| State–Decision–Effect inventory | Canonical owner, decisions, effect executor, and failure mechanisms are inventoried | Ambient/shadow state, hidden dependencies, and missing mechanisms are surfaced | `inventory-match.json`, `inventory-divergent.json` |
| Planned-versus-actual review | Matching inventory produces no fabricated generic assurance claim | Divergence produces typed profile findings and unknowns | `state-effect-review` fixture requests/results |
| Review context | Request-relative bounded context, exact digests, omissions, and HIDDEN/TARGETED prior-finding visibility | Missing subject/context inputs produce partial or blocked context rather than guessed coverage | `review-context` fixtures and schema |
| Review lens | Every declared language/domain lens maps to tested procedures | Unsupported/generic-only lens returns bounded unsupported/blocked status | `review-lens-map.json`; lens fixtures |
| Evidence adapter | Exact-subject native evidence is normalized without inventing fields | Legacy, incomplete, stale, wrong-subject, redacted, or unavailable evidence stays partial/blocked/ineligible | `native-evidence.json`, `legacy-evidence.txt`; EvidenceReceipt v2 schema |
| Determinism and path stability | Equivalent requests in relocated roots return the same stable semantic result identity | Source-root locator is excluded from stable identity; input bytes remain digest-bound | deterministic-path tests |
| OMP-adjacent registration | Six additive tools and commands invoke the same controller | Missing request or invalid controller output fails visibly | generated OMP extension checks and mock invocation |
| Compatibility and packaging | Original alpha.2 tests, successor tests, installer round trip, strict manifest, reproducible build, and clean-extraction rebuild pass | Traversal, symlink, mode, CRC, stale-manifest, and incompatible-core cases fail closed | release qualification evidence archive |

This matrix is a package qualification plan and evidence index. It does not claim native compiler, runtime, controller, IDE, cloud, or external service qualification.
