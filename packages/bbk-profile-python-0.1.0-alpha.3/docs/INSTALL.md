# Installation

## Prerequisites

- Python 3.11 or later for the profile CLI and installer.
- BBK `0.1.0-alpha.8` or a compatible successor for profile orchestration.
- OMP only when installing the OMP extension.

The installer never installs project dependencies or Python toolchains.

## Verify the package

```bash
python3 tools/verify_package.py --strict-mode
```

## User scope

```bash
python3 tools/install.py install --scope user --omp
```

By default, user installation can install Codex, OMP, and Claude Code surfaces. Select one or more explicit harness flags to narrow installation.

## Project scope

```bash
python3 tools/install.py install --scope project --root /path/to/project --omp
```

## Status and removal

```bash
python3 tools/install.py status --scope user
python3 tools/install.py uninstall --scope user
```

Uninstall removes only files whose installed digest still matches. Modified files are preserved unless `--force` is explicitly supplied. User-home and project-root ownership boundaries are never removed.

## Upgrade from alpha.2 and side-by-side versions

The profile installs immutable versions under the profile data root and updates a small `current.json` selector. Alpha.1 evidence and locks remain valid against alpha.1. Installing alpha.3 does not delete the alpha.2 package directory.

Because both releases project the same skill names and OMP extension path, activate alpha.3 with an explicit replacement that preserves backups of the active alpha.2 projections:

```bash
python3 tools/install.py install --scope user --omp --force
```

Use the equivalent project-scoped command for a project installation. Review the installer preview or dry run first where local projections may have been edited. Projects must rerun profile resolution and deliberately update locks to alpha.3; a BBK core upgrade does not silently upgrade the effective profile.


Current profile package: `0.1.0-alpha.3`.


Version and contract-dialect semantics are documented in `docs/METADATA-CONTRACT.md`.
