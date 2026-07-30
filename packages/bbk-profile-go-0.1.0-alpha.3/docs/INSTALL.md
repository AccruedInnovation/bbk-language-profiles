# BBK Go profile installation

## Requirements

- BBK core `0.1.0-alpha.4` or a compatible successor;
- Python 3.11 or newer for the resolver and installer;
- Go only when `--run-tools` or planned Go gates are actually executed;
- Node only to validate the optional OMP extension syntax.

No third-party Python package is required.

## Verify before installation

```bash
python3 tools/verify_package.py
python3 -m unittest discover -s tests -v
python3 tools/install.py install --scope user --dry-run
```

## User installation

```bash
python3 tools/install.py install --scope user
```

Individual harnesses:

```bash
python3 tools/install.py install --scope user --codex
python3 tools/install.py install --scope user --omp
python3 tools/install.py install --scope user --claude
```

The versioned profile package is installed below the BBK data root at `profiles/go/<version>/`. Skills are projected to the selected harness skill directories. The OMP extension is installed as `bbk-profile-go`, and a user launcher named `bbk-go` is created where applicable.

## Project installation

```bash
python3 tools/install.py install --scope project --root /path/to/repository --omp
```

Project profile location:

```text
.bbk-kit/profiles/go/<version>/
```

## Status and removal

```bash
python3 tools/install.py status --scope user
python3 tools/install.py uninstall --scope user --dry-run
python3 tools/install.py uninstall --scope user
```

Normal uninstall removes only files that still match the install manifest. Modified files and ownership roots are preserved.
