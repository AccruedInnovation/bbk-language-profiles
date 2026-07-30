# BBK language profiles

This repository contains the expanded, editable language-profile packages from
BBK `0.1.0-alpha.11.11`. Each directory beneath `packages/` remains independently
bound by its own `PACKAGE-MANIFEST.json`.

- **BBK CODESYS Structured Text Profile** — `codesys` `0.1.0-alpha.3`
- **BBK Go Profile** — `go` `0.1.0-alpha.3`
- **BBK Python Profile** — `python` `0.1.0-alpha.3`
- **BBK Rust Profile** — `rust` `0.1.0-alpha.3`
- **BBK TypeScript/JavaScript Profile** — `typescript-javascript` `0.1.0-alpha.3`

## Install with a sibling BBK checkout

From the BBK repository:

```powershell
python tools\setup.py --test-and-install `
  --scope user `
  --omp --codex `
  --language-profiles ..\bbk-language-profiles
```

The installer verifies `REPOSITORY-MANIFEST.json`, then independently verifies
every selected profile package before planning any destination write. A subset
can be selected with repeated `--profile-id` arguments.

The BBK release repository intentionally retains the small bundled profile ZIPs
so a single BBK checkout or release archive still supports the default
one-command installation. This repository is the editable source form.
