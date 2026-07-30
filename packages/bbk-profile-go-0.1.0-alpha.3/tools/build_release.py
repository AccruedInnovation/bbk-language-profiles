#!/usr/bin/env python3
"""Build a deterministic bbk-profile-go zip and companion artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "PROFILE.json").read_text(encoding="utf-8"))
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
TOP = f"bbk-profile-go-{VERSION}"
FIXED_TIME = (2026, 7, 24, 0, 0, 0)
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def run(command: Sequence[str]) -> None:
    subprocess.run([str(item) for item in command], cwd=ROOT, check=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def package_files() -> Iterable[Path]:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in rel.parts) or path.suffix in EXCLUDED_SUFFIXES:
            continue
        if rel.as_posix() == "PACKAGE-MANIFEST.json":
            continue
        yield path


def is_executable(path: Path) -> bool:
    return bool(path.stat().st_mode & stat.S_IXUSR)


def build_manifest() -> dict[str, Any]:
    files = []
    for path in package_files():
        rel = path.relative_to(ROOT).as_posix()
        files.append({
            "path": rel,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "executable": is_executable(path),
        })
    root_schema = "bbk.profile-package-root.v1"
    payload = {"schema": root_schema, "name": PROFILE["name"], "version": VERSION, "files": files}
    gates = json.loads((ROOT / PROFILE["gates"]).read_text(encoding="utf-8"))
    triggers = json.loads((ROOT / PROFILE["selection"]["risk_trigger_map"]).read_text(encoding="utf-8"))
    fixtures = [path for path in (ROOT / "fixtures").rglob("*") if path.is_file() and not path.is_symlink()]
    return {
        "schema": "bbk.profile-package-manifest.v1",
        "root_schema": root_schema,
        "name": PROFILE["name"],
        "profile_id": PROFILE["id"],
        "version": VERSION,
        "maturity": PROFILE["maturity"],
        "created_at": "2026-07-24T00:00:00Z",
        "file_count": len(files),
        "files": files,
        "root_sha256": hashlib.sha256(canonical(payload)).hexdigest(),
        "profile_manifest_sha256": sha256_file(ROOT / "PROFILE.json"),
        "skill_count": len(PROFILE["skills"]),
        "gate_recipe_count": len(gates.get("recipes", [])),
        "trigger_count": len(triggers.get("triggers", [])),
        "fixture_file_count": len(fixtures),
        "authority_disclaimer": "This optional BBK profile adds procedure and gate recipes; it grants no tools, effects, completion, readiness, or release authority.",
    }


def write_manifest() -> dict[str, Any]:
    manifest = build_manifest()
    (ROOT / "PACKAGE-MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def zip_info(name: str, executable: bool) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_TIME)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (stat.S_IFREG | (0o755 if executable else 0o644)) << 16
    return info


def build_zip(output: Path, manifest: dict[str, Any]) -> None:
    all_files = [ROOT / item["path"] for item in manifest["files"]] + [ROOT / "PACKAGE-MANIFEST.json"]
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(all_files, key=lambda item: item.relative_to(ROOT).as_posix()):
            rel = path.relative_to(ROOT).as_posix()
            archive.writestr(
                zip_info(f"{TOP}/{rel}", is_executable(path)),
                path.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def qualification_checks() -> None:
    pyfiles = [str(path.relative_to(ROOT)) for path in package_files() if path.suffix == ".py"]
    run([sys.executable, "-m", "py_compile", *pyfiles])
    for path in [
        ROOT / "PROFILE.json",
        *sorted((ROOT / "schemas").glob("*.json")),
        *sorted((ROOT / "mappings").glob("*.json")),
        *sorted((ROOT / "gates").glob("*.json")),
        *sorted((ROOT / "sources").glob("*.json")),
    ]:
        json.loads(path.read_text(encoding="utf-8"))
    if shutil.which("node"):
        run(["node", "--check", "omp/extension/index.js"])
    if shutil.which("go"):
        run(["go", "-C", "fixtures/go-workspace", "test", "./api/...", "./cmd/..."])
        run(["go", "-C", "fixtures/go-workspace", "vet", "./api/...", "./cmd/..."])
    run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(ROOT.parent))
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write first so profile discovery and integration tests can verify the exact
    # package that will be archived. Qualification does not mutate manifested files.
    manifest = write_manifest()
    if not args.skip_tests:
        qualification_checks()
    manifest = write_manifest()
    run([sys.executable, "tools/verify_package.py", "--strict-mode"])

    archive = output_dir / f"{TOP}.zip"
    build_zip(archive, manifest)
    digest = sha256_file(archive)
    (output_dir / f"{TOP}.sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    shutil.copy2(ROOT / "PACKAGE-MANIFEST.json", output_dir / f"{TOP}-package-manifest.json")
    shutil.copy2(ROOT / "docs" / "RELEASE-NOTES.md", output_dir / f"{TOP}-release-notes.md")
    print(f"Built: {archive}")
    print(f"SHA-256: {digest}")
    print(f"Package root SHA-256: {manifest['root_sha256']}")
    print(f"Files: {manifest['file_count']}")
    print(f"Skills: {manifest['skill_count']}")
    print(f"Gate recipes: {manifest['gate_recipe_count']}")
    print(f"Triggers: {manifest['trigger_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
