# Installing the BBK TypeScript/JavaScript profile

## Prerequisites

- BBK core `0.1.0-alpha.8` or a compatible successor;
- Python 3.11 or later;
- Codex, OMP and/or Claude Code only for the harnesses you select;
- Node.js only for OMP-extension qualification, not for static profile resolution.

The installer does not install Node, TypeScript, package managers, project dependencies or browsers.

## User scope

Install all supported harness surfaces:

```bash
python3 tools/install.py install --scope user
```

Select only OMP:

```bash
python3 tools/install.py install --scope user --omp
```

User targets include:

```text
BBK data root/profiles/typescript-javascript/<version>/
~/.agents/skills/<profile skill>/
~/.claude/skills/<profile skill>/
~/.omp/agent/extensions/bbk-profile-typescript-javascript/
~/.local/bin/bbk-tsjs
```

## Project scope

```bash
python3 tools/install.py install --scope project --root /path/to/project --omp
```

Project targets include:

```text
<project>/.bbk-kit/profiles/typescript-javascript/<version>/
<project>/.agents/skills/<profile skill>/
<project>/.claude/skills/<profile skill>/
<project>/.omp/extensions/bbk-profile-typescript-javascript/
```

## Safety behavior

- divergent files are not overwritten without `--force`;
- forced replacements are backed up;
- installed files are content-addressed in an install manifest;
- uninstall preserves locally modified files unless forced;
- user home and project root are cleanup boundaries and are never removed;
- versions install side by side and `current.json` selects the active profile copy.

## Verify discovery

```bash
bbk profile list
bbk profile inspect --id typescript-javascript
bbk-tsjs --version
```

## Status and removal

```bash
python3 tools/install.py status --scope user
python3 tools/install.py uninstall --scope user
```


Current profile package: `0.1.0-alpha.3`.


Version and contract-dialect semantics are documented in `docs/METADATA-CONTRACT.md`.
