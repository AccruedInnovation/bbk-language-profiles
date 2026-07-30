# Installing bbk-profile-rust

## Requirements

- BBK core `0.1.0-alpha.4` or compatible successor;
- Python 3.11 or newer;
- optional Node.js only for local extension syntax checks;
- a Rust toolchain only when a project explicitly authorizes live Rust interrogation or gates.

The profile does not install Rust, Cargo components, nightlies, Cargo subcommands, or project dependencies.

## Verify the release

```bash
sha256sum -c bbk-profile-rust-0.1.0-alpha.2.sha256
unzip -q bbk-profile-rust-0.1.0-alpha.2.zip
cd bbk-profile-rust-0.1.0-alpha.2
python3 tools/verify_package.py --strict-mode
```

## User installation

```bash
python3 tools/install.py install --scope user --omp
```

Without explicit harness flags, the installer targets the supported Codex/OMP/Claude skill surfaces. Use `--dry-run` first when installing into an existing customized environment.

## Project installation

```bash
python3 tools/install.py install --scope project --root /path/to/repository --omp
```

Versions install side by side under the BBK profile root. `current.json` selects the current profile version without altering the prior alpha.1 package or its evidence.

## Status and removal

```bash
python3 tools/install.py status --scope user
python3 tools/install.py uninstall --scope user
```

Uninstall removes only files whose digests still match the install manifest. Locally modified files are preserved and reported.
