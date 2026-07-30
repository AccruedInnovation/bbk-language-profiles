# BBK Language Profiles

### Specialist language and domain capabilities for the Blueprint Bootstrap Kit

This repository contains the editable source form of the language and domain profiles used by **BBK—the Blueprint Bootstrap Kit**.

> [!IMPORTANT]
> These profiles are not intended to be used as a standalone agent framework. They are discovered, selected, constrained, installed, and governed by BBK.

BBK provides the shared planning, orchestration, implementation, validation, review, evidence, and recovery model. Profiles add the specialist procedures needed to apply that model within a particular language, toolchain, runtime, or engineering domain.

## Included profiles

The current repository contains profiles for:

- **Go**
- **Python**
- **Rust**
- **TypeScript / JavaScript**

Each profile declares its identity, version, BBK compatibility, capabilities, router skill, focused skills, host integrations, and package inventory through its own `PROFILE.json` and `PACKAGE-MANIFEST.json`.

## What a profile provides

A BBK profile may add:

- language- or domain-specific planning and implementation procedures;
- compiler, formatter, linter, test, mutation-test, static-analysis, or CI guidance;
- validation and evidence-collection adapters;
- focused skills for particular toolchain operations;
- host-specific extensions or launchers;
- compatibility and capability metadata used by BBK profile routing.

Profiles **do not** replace BBK’s canonical role system, broaden an agent’s authority, waive assurance requirements, or make an unavailable external toolchain available. They specialize how an authorized BBK role performs and verifies work.

## Use with BBK

The normal source-repository arrangement is:

```text
workspace/
├── bbk/
└── bbk-language-profiles/
```

From the `bbk` repository, verify BBK and install all profiles from this expanded repository:

```bash
python tools/setup.py --test-and-install \
  --scope user \
  --omp --codex \
  --language-profiles ../bbk-language-profiles
```

Install only selected profiles:

```bash
python tools/setup.py --test-and-install \
  --scope user \
  --omp --codex \
  --language-profiles ../bbk-language-profiles \
  --profile-id rust \
  --profile-id python
```

BBK verifies the repository inventory and independently verifies every selected profile package before beginning installation writes.

Release archives of BBK may contain bundled snapshots of these profiles for self-contained installation. This repository is the editable source form and should be used when developing or reviewing profile changes.

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

The repository manifest binds the expected profile set and package-root digests. Each profile package also carries its own independent manifest.

## Contributing

Profile changes should remain bounded to language- or domain-specific capability. In particular:

- keep `PROFILE.json` accurate and treat it as the profile’s canonical declaration;
- do not redefine BBK’s canonical roles, authority boundaries, or direct-child topology;
- keep router skills small and load focused skills only when required;
- preserve deterministic package verification and reproducible builds;
- update tests and qualification evidence alongside procedure or tooling changes;
- distinguish package qualification from live compiler, IDE, simulator, runtime, or target-project qualification;
- regenerate manifests and checksums with the repository tooling rather than editing them by hand.

Changes to BBK’s core method, host adapters, project records, installer, or orchestration model belong in the companion BBK repository.

## Status

BBK and these profiles are pre-1.0. Profile compatibility is versioned explicitly; use a BBK release that satisfies the requirements declared by the selected profile.

## License

See [`LICENSE`](LICENSE).
