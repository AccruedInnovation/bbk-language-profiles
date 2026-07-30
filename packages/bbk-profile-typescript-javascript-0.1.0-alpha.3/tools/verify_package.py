#!/usr/bin/env python3
"""Verify a bbk-profile-typescript-javascript package tree against PACKAGE-MANIFEST.json."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any, Sequence

EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def safe_relative(value: str) -> bool:
    path = Path(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and "\\" not in value


def actual_files(root: Path) -> set[str]:
    values: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            continue
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in rel.parts) or path.suffix in EXCLUDED_SUFFIXES:
            continue
        if rel.as_posix() == "PACKAGE-MANIFEST.json":
            continue
        values.add(rel.as_posix())
    return values


def verify(root: Path, *, strict_mode: bool = False) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = root / "PACKAGE-MANIFEST.json"
    errors: list[str] = []
    if not manifest_path.is_file():
        return {"schema": "bbk.profile-package-verification.v1", "status": "FAIL", "root": str(root), "errors": [f"missing {manifest_path}"]}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "bbk.profile-package-verification.v1", "status": "FAIL", "root": str(root), "errors": [f"invalid manifest: {exc}"]}
    if manifest.get("schema") != "bbk.profile-package-manifest.v1":
        errors.append(f"unsupported manifest schema: {manifest.get('schema')!r}")
    records = manifest.get("files", [])
    if not isinstance(records, list):
        records = []
        errors.append("files must be a list")
    expected: dict[str, dict[str, Any]] = {}
    for item in records:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            errors.append("invalid file record")
            continue
        rel = item["path"]
        if not safe_relative(rel):
            errors.append(f"unsafe path: {rel}")
            continue
        if rel in expected:
            errors.append(f"duplicate path: {rel}")
            continue
        expected[rel] = item
    actual = actual_files(root)
    symlinks = [path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_symlink()]
    if symlinks:
        errors.extend(f"symlink not allowed: {path}" for path in sorted(symlinks))
    for rel in sorted(set(expected) - actual):
        errors.append(f"missing: {rel}")
    for rel in sorted(actual - set(expected)):
        errors.append(f"unexpected: {rel}")
    for rel in sorted(actual & set(expected)):
        path = root / rel
        item = expected[rel]
        size = path.stat().st_size
        digest = sha256_file(path)
        executable = bool(path.stat().st_mode & stat.S_IXUSR)
        if size != item.get("bytes"):
            errors.append(f"size mismatch: {rel} expected={item.get('bytes')} actual={size}")
        if digest != item.get("sha256"):
            errors.append(f"digest mismatch: {rel} expected={item.get('sha256')} actual={digest}")
        if strict_mode and sys.platform != "win32" and executable != bool(item.get("executable")):
            errors.append(f"executable-bit mismatch: {rel} expected={item.get('executable')} actual={executable}")
    payload = {
        "schema": manifest.get("root_schema", "bbk.profile-package-root.v1"),
        "name": manifest.get("name"), "version": manifest.get("version"), "files": records,
    }
    root_digest = hashlib.sha256(canonical(payload)).hexdigest()
    if root_digest != manifest.get("root_sha256"):
        errors.append(f"root digest mismatch: expected={manifest.get('root_sha256')} actual={root_digest}")
    if manifest.get("file_count") != len(expected):
        errors.append(f"file_count mismatch: field={manifest.get('file_count')} records={len(expected)}")
    profile_path = root / "PROFILE.json"
    if profile_path.is_file():
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        if profile.get("id") != manifest.get("profile_id"):
            errors.append("profile id mismatch")
        if profile.get("version") != manifest.get("version"):
            errors.append("profile version mismatch")
    return {
        "schema": "bbk.profile-package-verification.v1", "status": "PASS" if not errors else "FAIL",
        "root": str(root), "profile_id": manifest.get("profile_id"), "version": manifest.get("version"),
        "root_sha256": root_digest, "file_count": len(expected), "errors": errors,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict-mode", action="store_true")
    args = parser.parse_args(argv)
    result = verify(Path(args.root), strict_mode=args.strict_mode)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"BBK TypeScript/JavaScript profile package verification: {result['status']}")
        print(f"Root: {result.get('root')}")
        print(f"Version: {result.get('version')}")
        print(f"Files: {result.get('file_count')}")
        print(f"Root SHA-256: {result.get('root_sha256')}")
        for error in result.get("errors", []):
            print(f"- {error}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
