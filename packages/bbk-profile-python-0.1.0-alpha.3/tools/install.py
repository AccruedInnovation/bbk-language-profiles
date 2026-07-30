#!/usr/bin/env python3
"""Cautious installer for bbk-profile-python across Codex, OMP, and Claude Code."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "PROFILE.json").read_text(encoding="utf-8"))
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
PROFILE_ID = str(PROFILE["id"])


class InstallError(RuntimeError):
    pass


def stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: Path, data: bytes, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.bbk-python-install-{os.getpid()}")
    temp.write_bytes(data)
    if mode is not None:
        os.chmod(temp, mode)
    os.replace(temp, path)


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def data_root() -> Path:
    if value := os.environ.get("BBK_INSTALL_ROOT"):
        return Path(value).expanduser().resolve()
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "BBK"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "BBK"
    base = os.environ.get("XDG_DATA_HOME")
    return (Path(base).expanduser() if base else Path.home() / ".local" / "share") / "bbk"


def bin_dir() -> Path:
    if value := os.environ.get("BBK_BIN_DIR"):
        return Path(value).expanduser().resolve()
    if os.name == "nt":
        return data_root() / "bin"
    return Path.home() / ".local" / "bin"


def source_files(root: Path) -> Iterable[Path]:
    excluded = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in excluded for part in rel.parts) or path.suffix in {".pyc", ".pyo"}:
            continue
        yield path


def backup_path(backup_root: Path, destination: Path) -> Path:
    """Map an absolute destination beneath the owned backup root.

    Joining a Path with an absolute component discards the prefix.  Preserve the
    destination hierarchy as relative path components and encode the filesystem
    anchor as an ordinary directory name so a forced replacement can never
    alias the live destination.
    """
    resolved = destination.expanduser().resolve(strict=False)
    parts = list(resolved.parts)
    anchor = parts[0] if resolved.is_absolute() and parts else "relative"
    safe_anchor = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in anchor).strip("_") or "root"
    relative_parts = parts[1:] if resolved.is_absolute() else parts
    return backup_root / safe_anchor / Path(*relative_parts)


def install_bytes(
    data: bytes,
    destination: Path,
    *,
    source: str,
    force: bool,
    dry_run: bool,
    backup_root: Path,
    records: list[dict[str, Any]],
    executable: bool = False,
) -> None:
    digest = hashlib.sha256(data).hexdigest()
    action = "create"
    backup: Path | None = None
    if destination.exists():
        if not destination.is_file():
            raise InstallError(f"refusing to replace non-file destination: {destination}")
        existing = sha256_file(destination)
        if existing == digest:
            records.append({"path": str(destination), "sha256": digest, "action": "unchanged", "source": source})
            return
        if not force:
            raise InstallError(f"destination differs: {destination}; rerun with --force to back it up and replace it")
        backup = backup_path(backup_root, destination)
        action = "replace"
        if not dry_run:
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)
    if not dry_run:
        atomic_write(destination, data, 0o755 if executable else 0o644)
    records.append({"path": str(destination), "sha256": digest, "action": action, "source": source, "backup": str(backup) if backup else None})


def install_file(source: Path, destination: Path, **kwargs: Any) -> None:
    install_bytes(source.read_bytes(), destination, source=str(source), executable=bool(source.stat().st_mode & 0o111), **kwargs)


def copy_tree(source: Path, destination: Path, **kwargs: Any) -> None:
    for path in source_files(source):
        install_file(path, destination / path.relative_to(source), **kwargs)


def profile_base(scope: str, project: Path | None) -> Path:
    if scope == "user":
        return data_root() / "profiles" / PROFILE_ID
    assert project is not None
    return project / ".bbk-kit" / "profiles" / PROFILE_ID


def install_package_copy(base: Path, **kwargs: Any) -> Path:
    version_root = base / VERSION
    copy_tree(ROOT, version_root, **kwargs)
    current = {"schema": "bbk.current-profile.v1", "id": PROFILE_ID, "version": VERSION, "path": str(version_root)}
    install_bytes(json_bytes(current), base / "current.json", source="generated:current-profile", **kwargs)
    return version_root


def launcher(package_root: Path) -> tuple[str, bytes]:
    script = package_root / "tools" / "bbk_python.py"
    if os.name == "nt":
        return "bbk-python.cmd", f'@echo off\r\nif defined BBK_PYTHON ("%BBK_PYTHON%" "{script}" %*) else (py -3 "{script}" %*)\r\n'.encode()
    return "bbk-python", f'#!/bin/sh\nexec "${{BBK_PYTHON:-python3}}" {json.dumps(str(script))} "$@"\n'.encode()


def manifest_path(scope: str, project: Path | None) -> Path:
    if scope == "user":
        return data_root() / "profile-install-manifests" / f"{PROFILE_ID}.json"
    assert project is not None
    return project / f".bbk-profile-{PROFILE_ID}-install.json"


def selected_harnesses(args: argparse.Namespace) -> tuple[bool, bool, bool]:
    codex, omp, claude = bool(args.codex), bool(args.omp), bool(args.claude)
    if not (codex or omp or claude):
        codex = omp = claude = True
    return codex, omp, claude


def install(args: argparse.Namespace) -> dict[str, Any]:
    codex, omp, claude = selected_harnesses(args)
    project = Path(args.root).expanduser().resolve() if args.root else (Path.cwd().resolve() if args.scope == "project" else None)
    if args.scope == "project" and project is None:
        raise InstallError("project scope requires --root or a current directory")
    base = profile_base(args.scope, project)
    backups = (data_root() if args.scope == "user" else project / ".bbk-kit") / "backups" / f"profile-{PROFILE_ID}" / stamp()  # type: ignore[operator]
    records: list[dict[str, Any]] = []
    common = {"force": args.force, "dry_run": args.dry_run, "backup_root": backups, "records": records}
    package_root = install_package_copy(base, **common)

    if args.scope == "user":
        agent_skills = Path.home() / ".agents" / "skills"
        claude_skills = Path.home() / ".claude" / "skills"
        omp_extension = Path.home() / ".omp" / "agent" / "extensions" / "bbk-profile-python"
        binaries = bin_dir()
    else:
        assert project is not None
        agent_skills = project / ".agents" / "skills"
        claude_skills = project / ".claude" / "skills"
        omp_extension = project / ".omp" / "extensions" / "bbk-profile-python"
        binaries = None

    if codex or omp:
        copy_tree(ROOT / "skills", agent_skills, **common)
    if claude:
        copy_tree(ROOT / "skills", claude_skills, **common)
    if omp:
        for name in ["index.js", "package.json", "README.md"]:
            install_file(ROOT / "omp" / "extension" / name, omp_extension / name, **common)
    if binaries is not None:
        name, content = launcher(package_root)
        install_bytes(content, binaries / name, source="generated:bbk-python-launcher", executable=True, **common)

    manifest = {
        "schema": "bbk.profile-install-manifest.v1", "profile_id": PROFILE_ID, "version": VERSION,
        "scope": args.scope, "project_root": str(project) if project else None,
        "package_root": str(package_root), "codex": codex, "omp": omp, "claude": claude,
        "dry_run": args.dry_run, "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "files": records, "backup_root": str(backups),
    }
    mpath = manifest_path(args.scope, project)
    if not args.dry_run:
        atomic_write(mpath, json_bytes(manifest), 0o600)
    manifest["manifest_path"] = str(mpath)
    return manifest


def status(args: argparse.Namespace) -> dict[str, Any]:
    project = Path(args.root).expanduser().resolve() if args.root else (Path.cwd().resolve() if args.scope == "project" else None)
    mpath = manifest_path(args.scope, project)
    result: dict[str, Any] = {
        "schema": "bbk.profile-install-status.v1", "profile_id": PROFILE_ID,
        "source_package": str(ROOT), "source_version": VERSION, "scope": args.scope,
        "manifest_path": str(mpath), "installed": mpath.exists(),
    }
    if not mpath.exists():
        return result
    try:
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result["manifest_error"] = str(exc)
        return result
    files = []
    for item in manifest.get("files", []):
        path = Path(item["path"])
        if not path.exists():
            state, current = "missing", None
        elif not path.is_file():
            state, current = "not-file", None
        else:
            current = sha256_file(path)
            state = "current" if current == item.get("sha256") else "modified"
        files.append({"path": str(path), "state": state, "expected": item.get("sha256"), "current": current})
    result.update({
        "installed_version": manifest.get("version"),
        "harnesses": {"codex": manifest.get("codex"), "omp": manifest.get("omp"), "claude": manifest.get("claude")},
        "files": files,
        "summary": {state: sum(1 for item in files if item["state"] == state) for state in {item["state"] for item in files}},
    })
    return result


def uninstall(args: argparse.Namespace) -> dict[str, Any]:
    project = Path(args.root).expanduser().resolve() if args.root else (Path.cwd().resolve() if args.scope == "project" else None)
    mpath = manifest_path(args.scope, project)
    if not mpath.exists():
        raise InstallError(f"no profile install manifest found: {mpath}")
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    removed: list[str] = []
    preserved: list[dict[str, Any]] = []
    for item in reversed(manifest.get("files", [])):
        path = Path(item["path"])
        if not path.exists():
            continue
        if not path.is_file():
            preserved.append({"path": str(path), "reason": "not a regular file"})
            continue
        current = sha256_file(path)
        if current != item.get("sha256") and not args.force:
            preserved.append({"path": str(path), "reason": "modified since install", "expected": item.get("sha256"), "current": current})
            continue
        if not args.dry_run:
            path.unlink()
        removed.append(str(path))
    if not args.dry_run:
        mpath.unlink(missing_ok=True)
        stop_dirs = {path.resolve() for path in (Path.home(), project, data_root(), data_root().parent) if path is not None}
        for raw in sorted({str(Path(path).parent) for path in removed}, key=len, reverse=True):
            directory = Path(raw).resolve()
            while directory.exists() and directory.is_dir():
                if directory in stop_dirs or directory == Path(directory.anchor):
                    break
                try:
                    directory.rmdir()
                except OSError:
                    break
                directory = directory.parent
    return {
        "schema": "bbk.profile-uninstall-result.v1", "profile_id": PROFILE_ID,
        "scope": args.scope, "dry_run": args.dry_run, "removed": removed,
        "preserved": preserved, "manifest_path": str(mpath),
    }


def human(value: dict[str, Any]) -> str:
    schema = value.get("schema")
    if schema == "bbk.profile-install-manifest.v1":
        actions: dict[str, int] = {}
        for item in value["files"]:
            actions[item["action"]] = actions.get(item["action"], 0) + 1
        return f"Python profile install {'dry run' if value['dry_run'] else 'complete'}\nScope: {value['scope']}\nHarnesses: Codex={value['codex']} OMP={value['omp']} Claude={value['claude']}\nFiles: {actions}\nManifest: {value['manifest_path']}"
    if schema == "bbk.profile-install-status.v1":
        return f"Python profile {value['source_version']}\nScope: {value['scope']}\nInstalled: {value['installed']}\nFiles: {value.get('summary', {})}\nManifest: {value['manifest_path']}"
    if schema == "bbk.profile-uninstall-result.v1":
        return f"Python profile uninstall {'dry run' if value['dry_run'] else 'complete'}\nRemoved: {len(value['removed'])}\nPreserved: {len(value['preserved'])}"
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ["install", "status", "uninstall"]:
        p = sub.add_parser(command)
        p.add_argument("--scope", choices=["user", "project"], default="user")
        p.add_argument("--root")
        if command == "install":
            p.add_argument("--codex", action="store_true")
            p.add_argument("--omp", action="store_true")
            p.add_argument("--claude", action="store_true")
            p.add_argument("--force", action="store_true")
            p.add_argument("--dry-run", action="store_true")
            p.set_defaults(func=install)
        elif command == "uninstall":
            p.add_argument("--force", action="store_true")
            p.add_argument("--dry-run", action="store_true")
            p.set_defaults(func=uninstall)
        else:
            p.set_defaults(func=status)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    normalized = list(sys.argv[1:] if argv is None else argv)
    if "--json" in normalized and normalized and normalized[0] != "--json":
        normalized.remove("--json")
        normalized.insert(0, "--json")
    args = build_parser().parse_args(normalized)
    try:
        value = args.func(args)
    except InstallError as exc:
        if args.json:
            print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"bbk-profile-python install: error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) if args.json else human(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
