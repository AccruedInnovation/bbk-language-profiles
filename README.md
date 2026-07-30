# BBK Language Profiles

### Specialist language and domain capabilities for the Blueprint Bootstrap Kit

This repository contains the expanded, editable source form of the language and domain profiles used by **BBK—the Blueprint Bootstrap Kit**.

> [!IMPORTANT]
> These profiles are not a standalone agent framework. BBK discovers, selects, constrains, installs, and governs them.

BBK provides the shared planning, orchestration, implementation, validation, review, evidence, handoff, and recovery model. Profiles add the specialist procedures needed to apply that model within a particular language, toolchain, runtime, or engineering domain.

The companion core repository is [`AccruedInnovation/bbk`](https://github.com/AccruedInnovation/bbk).

---

## Included profiles

| Profile | ID | Current package version | Review Assurance |
| --- | --- | --- | --- |
| Go | `go` | `0.1.0-alpha.3` | Supported within declared toolchain and environment limits |
| Python | `python` | `0.1.0-alpha.3` | Supported within declared interpreter, environment, packaging, and runtime limits |
| Rust | `rust` | `0.1.0-alpha.3` | Supported within declared toolchain and target limits |
| TypeScript / JavaScript | `typescript-javascript` | `0.1.0-alpha.3` | Supported within declared runtime, browser, package, and host limits |

`REPOSITORY-MANIFEST.json` and each package’s `PROFILE.json` are authoritative for the current inventory, identity, compatibility, capabilities, and package digests.

---

## What a profile provides

A BBK profile may add:

- language- or domain-specific planning and implementation procedures;
- type, interface, state, concurrency, effect, resource-lifetime, packaging, and migration guidance;
- compiler, formatter, linter, test, mutation-test, static-analysis, simulator, or CI procedures;
- review-context selectors and claim-specific review lenses;
- evidence-collection and normalization adapters;
- focused skills for particular toolchain operations;
- host-specific extensions or launchers;
- typed capability metadata used by BBK profile routing.

Profiles **do not**:

- replace BBK’s canonical role system;
- broaden an agent’s authority or mutation scope;
- waive assurance requirements or declare project acceptance;
- install, select, license, or qualify an external toolchain by implication;
- turn missing mandatory evidence into a pass.

They specialize how an already-authorized BBK role performs and verifies work.

---

## Compatibility model

Three version concepts are intentionally distinct:

1. **Profile package version** — the version of the specialist package, currently `0.1.0-alpha.3`.
2. **Minimum compatible BBK version** — currently BBK `0.1.0-alpha.8` or a compatible successor, as declared by each `PROFILE.json`.
3. **Contract dialect lineage** — several structure and execution projections implement the contract dialect introduced in BBK alpha.4. That does **not** mean the profile only supports BBK alpha.4 or that alpha.4 is the current core version.

The profile metadata and runtime compatibility checks use these meanings explicitly. Do not infer compatibility from directory names or prose alone.

---

## Use with BBK

The normal source-repository arrangement is:

```text
workspace/
├── bbk/
└── bbk-language-profiles/
```

From the `bbk` repository, verify BBK and install all profiles from this expanded repository:

```bash
python tools/setup.py --test-and-install --scope user --omp --codex --language-profiles ../bbk-language-profiles
```

Install only selected profiles:

```bash
python tools/setup.py --test-and-install --scope user --omp --codex --language-profiles ../bbk-language-profiles --profile-id rust --profile-id python
```

Preview the complete verification and installation plan without writing destination files:

```bash
python tools/setup.py --test-and-install --scope user --omp --codex --language-profiles ../bbk-language-profiles --dry-run
```

BBK first verifies `REPOSITORY-MANIFEST.json`, then independently verifies every selected package’s `PACKAGE-MANIFEST.json`, compatibility declaration, identity, destination plan, and collision boundary before any installation write begins.

BBK release archives also contain qualified ZIP snapshots of the current profiles so a standalone BBK checkout remains self-contained. This repository is the editable source form and should be used for profile development, review, and contribution.

---

## How BBK uses profiles

At installation time, BBK records the exact installed profile IDs, versions, routers, capabilities, package bindings, and launch fallbacks. At runtime, profile-aware roles:

1. inspect the installed-profile registry;
2. select the smallest applicable profile set;
3. load the profile router first;
4. load only the focused procedures required for the current task and assurance claims;
5. propagate profile identity, assumptions, required gates, and unavailable-capability dispositions to child agents;
6. treat profile output as additional procedure and evidence—not as expanded authority or an automatic pass.

The profile repository does not redefine BBK’s canonical direct-child topology or role constitution.

---

## Repository layout

```text
bbk-language-profiles/
├── packages/
│   ├── bbk-profile-go-<version>/
│   ├── bbk-profile-python-<version>/
│   ├── bbk-profile-rust-<version>/
│   └── bbk-profile-typescript-javascript-<version>/
├── REPOSITORY-MANIFEST.json
├── SHA256SUMS.txt
├── README.md
└── LICENSE
```

Each profile package is independently versioned and contains its own:

```text
PROFILE.json
PACKAGE-MANIFEST.json
VERSION
README.md
CHANGELOG.md
docs/
skills/
references/
mappings/
schemas/
gates/
tools/
tests/
```

The exact contents vary by language and declared capability.

---

## Verify an individual profile

From a profile package directory:

```bash
python tools/verify_package.py --strict-mode
python -m unittest discover -s tests -v
```

These checks establish package integrity and the profile’s deterministic contracts. They do not qualify a live compiler, IDE, simulator, runtime, browser, external service, physical target, or target project.

Use the profile’s own `README.md`, `docs/USAGE.md`, `docs/SUPPORT-MATRIX.md`, `docs/KNOWN-LIMITATIONS.md`, and `docs/QUALIFICATION.md` for language-specific requirements and boundaries.

---

## Contributing

Profile changes should remain bounded to language- or domain-specific capability. In particular:

- keep `PROFILE.json` accurate and treat it as the canonical profile declaration;
- keep current metadata consistent across `VERSION`, `PROFILE.json`, the package README, installation docs, OMP metadata, and manifests;
- distinguish package version, BBK compatibility floor, and contract-dialect lineage;
- do not redefine BBK’s canonical roles, authority boundaries, constitution, or direct-child topology;
- keep router skills small and load focused skills only when required;
- preserve explicit UTF-8 handling, deterministic package verification, and reproducible builds;
- exclude interpreter caches and generated local state from packages and manifests;
- update focused tests when procedures, schemas, adapters, compatibility checks, or tooling change;
- distinguish package qualification from live compiler, IDE, simulator, runtime, provider, or target-project qualification;
- regenerate package and repository manifests and checksums with the repository tooling rather than editing them by hand.

Changes to BBK’s core method, role system, host adapters, project records, installer, or orchestration model belong in the companion BBK repository.

---

## Status

BBK and these profiles are pre-1.0. Compatibility and capability limits are declared explicitly. Use a BBK release that satisfies the selected profile’s `requires.bbk_minimum` contract, and treat missing mandatory toolchain evidence as `BLOCKED` rather than inferred success.

---

## License

See [`LICENSE`](LICENSE).
