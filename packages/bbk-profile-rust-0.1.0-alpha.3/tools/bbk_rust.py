#!/usr/bin/env python3
"""Deterministic resolver and preflight CLI for bbk-profile-rust.

The profile adds procedure, routing, and gate recipes. It never grants tools,
network access, mutation authority, broader scope, or a verification pass.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Iterable, Sequence

import rust_structure

PROFILE_ROOT = Path(os.environ.get("BBK_PROFILE_ROOT", Path(__file__).resolve().parents[1])).resolve()
PROFILE = json.loads((PROFILE_ROOT / "PROFILE.json").read_text(encoding="utf-8"))
VERSION = (PROFILE_ROOT / "VERSION").read_text(encoding="utf-8").strip()
TIER_RANK = {"routine": 0, "material": 1, "consequential": 2, "critical": 3}
SECRET_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL", "PRIVATE_KEY")
MAX_CAPTURE = 256 * 1024


class RustProfileError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def pretty(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RustProfileError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RustProfileError(f"invalid JSON in {path}: {exc}") from exc


def read_toml(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RustProfileError(f"missing file: {path}") from exc
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise RustProfileError(f"invalid TOML in {path}: {exc}") from exc


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def find_cargo_root(start: Path) -> Path:
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    candidates: list[Path] = []
    for candidate in (current, *current.parents):
        manifest = candidate / "Cargo.toml"
        if manifest.is_file():
            candidates.append(candidate)
            try:
                data = read_toml(manifest)
            except RustProfileError:
                continue
            if "workspace" in data:
                return candidate
    if candidates:
        return candidates[0]
    raise RustProfileError(f"no Cargo.toml found from {current}")


def expand_workspace_members(root: Path, manifest: dict[str, Any]) -> list[Path]:
    workspace = manifest.get("workspace") if isinstance(manifest.get("workspace"), dict) else {}
    patterns = workspace.get("members", []) if isinstance(workspace, dict) else []
    excludes = workspace.get("exclude", []) if isinstance(workspace, dict) else []
    excluded: set[Path] = set()
    for pattern in excludes if isinstance(excludes, list) else []:
        if not isinstance(pattern, str):
            continue
        for raw in glob.glob(str(root / pattern), recursive=True):
            path = Path(raw)
            excluded.add((path if path.is_dir() else path.parent).resolve())
    members: set[Path] = set()
    if isinstance(manifest.get("package"), dict):
        members.add(root.resolve())
    for pattern in patterns if isinstance(patterns, list) else []:
        if not isinstance(pattern, str):
            continue
        for raw in glob.glob(str(root / pattern), recursive=True):
            path = Path(raw)
            if path.name == "Cargo.toml":
                path = path.parent
            if path.is_dir() and (path / "Cargo.toml").is_file() and path.resolve() not in excluded:
                members.add(path.resolve())
    if not members and (root / "Cargo.toml").is_file():
        members.add(root.resolve())
    return sorted(members, key=lambda item: relpath(item, root))


def target_summary(manifest: dict[str, Any], package_root: Path) -> dict[str, Any]:
    package = manifest.get("package") if isinstance(manifest.get("package"), dict) else {}
    lib = manifest.get("lib") if isinstance(manifest.get("lib"), dict) else None
    bins = manifest.get("bin") if isinstance(manifest.get("bin"), list) else []
    crate_types: list[str] = []
    proc_macro = False
    if lib:
        types = lib.get("crate-type", [])
        if isinstance(types, list):
            crate_types.extend(str(item) for item in types)
        proc_macro = bool(lib.get("proc-macro", False))
        if proc_macro and "proc-macro" not in crate_types:
            crate_types.append("proc-macro")
    if not lib and (package_root / "src" / "lib.rs").is_file():
        crate_types.append("lib")
    if bins or (package_root / "src" / "main.rs").is_file():
        crate_types.append("bin")
    return {
        "crate_types": sorted(set(crate_types)),
        "proc_macro": proc_macro,
        "bin_count": len(bins) if bins else int((package_root / "src" / "main.rs").is_file()),
        "example_count": len(manifest.get("example", [])) if isinstance(manifest.get("example"), list) else 0,
        "test_target_count": len(manifest.get("test", [])) if isinstance(manifest.get("test"), list) else 0,
        "bench_count": len(manifest.get("bench", [])) if isinstance(manifest.get("bench"), list) else 0,
        "build_script": bool(package.get("build") or (package_root / "build.rs").is_file()),
    }


def package_summary(root: Path, package_root: Path) -> dict[str, Any]:
    path = package_root / "Cargo.toml"
    manifest = read_toml(path)
    package = manifest.get("package") if isinstance(manifest.get("package"), dict) else {}
    features = manifest.get("features") if isinstance(manifest.get("features"), dict) else {}
    dependencies: list[dict[str, Any]] = []
    for section in ("dependencies", "dev-dependencies", "build-dependencies"):
        values = manifest.get(section)
        if not isinstance(values, dict):
            continue
        for name, spec in values.items():
            source = "registry-or-workspace"
            optional = False
            if isinstance(spec, dict):
                if "path" in spec:
                    source = "path"
                elif "git" in spec:
                    source = "git"
                elif spec.get("workspace") is True:
                    source = "workspace"
                optional = bool(spec.get("optional", False))
            dependencies.append({"name": str(name), "kind": section, "source": source, "optional": optional})
    summary = {
        "name": package.get("name") or package_root.name,
        "version": package.get("version"),
        "manifest": relpath(path, root),
        "root": relpath(package_root, root),
        "edition": str(package.get("edition")) if package.get("edition") is not None else None,
        "rust_version": str(package.get("rust-version")) if package.get("rust-version") is not None else None,
        "publish": package.get("publish", True),
        "default_features": list(features.get("default", [])) if isinstance(features.get("default"), list) else [],
        "feature_names": sorted(str(name) for name in features),
        "dependencies": sorted(dependencies, key=lambda item: (item["kind"], item["name"])),
        **target_summary(manifest, package_root),
    }
    return summary


def toolchain_summary(root: Path) -> dict[str, Any]:
    toml_path = root / "rust-toolchain.toml"
    plain_path = root / "rust-toolchain"
    result: dict[str, Any] = {"source": None, "channel": None, "components": [], "targets": [], "profile": None}
    if toml_path.is_file():
        data = read_toml(toml_path)
        toolchain = data.get("toolchain") if isinstance(data.get("toolchain"), dict) else {}
        result.update({
            "source": relpath(toml_path, root),
            "sha256": sha256_file(toml_path),
            "channel": toolchain.get("channel"),
            "components": sorted(str(item) for item in toolchain.get("components", []) if isinstance(item, str)),
            "targets": sorted(str(item) for item in toolchain.get("targets", []) if isinstance(item, str)),
            "profile": toolchain.get("profile"),
        })
    elif plain_path.is_file():
        text = plain_path.read_text(encoding="utf-8").strip()
        result.update({"source": relpath(plain_path, root), "sha256": sha256_file(plain_path), "channel": text})
    return result


def configuration_summary(root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for path in [root / ".cargo" / "config.toml", root / ".cargo" / "config"]:
        if path.is_file():
            files.append({"path": relpath(path, root), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    env_records: list[dict[str, Any]] = []
    fixed = {"RUSTFLAGS", "RUSTDOCFLAGS", "RUSTUP_TOOLCHAIN", "CARGO_BUILD_TARGET", "CARGO_TARGET_DIR", "CARGO_HOME", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER"}
    for key, value in sorted(os.environ.items()):
        if any(marker in key.upper() for marker in SECRET_MARKERS):
            continue
        if key in fixed or key.startswith("CARGO_PROFILE_") or key.startswith("CARGO_TARGET_"):
            env_records.append({"name": key, "value_sha256": sha256_bytes(value.encode("utf-8")), "bytes": len(value.encode("utf-8"))})
    return {"files": files, "environment": env_records}


def detect_repository_commands(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"files": [], "recipes": {}}
    candidates = [root / "Justfile", root / "justfile", root / "Makefile", root / "makefile"]
    patterns = {
        "format": [r"(?m)^(?:fmt|format|fmt-check|format-check)\s*[:=]"],
        "lint": [r"(?m)^(?:lint|clippy|check-lints)\s*[:=]"],
        "test": [r"(?m)^(?:test|tests|check-test)\s*[:=]"],
        "check": [r"(?m)^(?:check|ci|verify)\s*[:=]"],
        "package": [r"(?m)^(?:package|dist|release-check)\s*[:=]"],
        "mutest": [r"(?m)^(?:mutest|mutation|mutation-test)\s*[:=]"],
    }
    for path in candidates:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        kind = "just" if path.name.lower() == "justfile" else "make"
        result["files"].append({"path": relpath(path, root), "sha256": sha256_file(path), "kind": kind})
        for purpose, regexes in patterns.items():
            for regex in regexes:
                match = re.search(regex, text)
                if match:
                    target = match.group(0).split(":", 1)[0].split("=", 1)[0].strip()
                    executable = "just" if kind == "just" else "make"
                    result["recipes"].setdefault(purpose, [executable, target])
                    break
    return result


def scan_support_signals(root: Path, members: Sequence[Path]) -> dict[str, Any]:
    result = {"no_std": False, "wasm": False, "native_build": False, "proc_macro": False, "unsafe_files": 0}
    source_files: list[Path] = []
    for member in members:
        source_files.extend(sorted((member / "src").rglob("*.rs")) if (member / "src").is_dir() else [])
        if (member / "build.rs").is_file():
            result["native_build"] = True
    for path in source_files[:5000]:
        if path.stat().st_size > 1024 * 1024:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"#!\s*\[\s*no_std\s*\]", text):
            result["no_std"] = True
        if re.search(r"wasm_bindgen|web_sys|js_sys|target_arch\s*=\s*\"wasm32\"", text):
            result["wasm"] = True
        if re.search(r"\bunsafe\b", text):
            result["unsafe_files"] += 1
    return result


def run_command(argv: Sequence[str], cwd: Path, timeout: float = 30.0) -> dict[str, Any]:
    env = os.environ.copy()
    env["CARGO_NET_OFFLINE"] = "true"
    started = dt.datetime.now(dt.timezone.utc)
    try:
        completed = subprocess.run(
            [str(item) for item in argv], cwd=str(cwd), env=env, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
        stdout = completed.stdout[:MAX_CAPTURE]
        stderr = completed.stderr[:MAX_CAPTURE]
        return {
            "argv": list(argv), "returncode": completed.returncode,
            "stdout": stdout, "stderr": stderr,
            "truncated": len(completed.stdout) > MAX_CAPTURE or len(completed.stderr) > MAX_CAPTURE,
            "started_at": started.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
    except FileNotFoundError as exc:
        return {"argv": list(argv), "returncode": 127, "stdout": "", "stderr": str(exc), "truncated": False}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {"argv": list(argv), "returncode": 124, "stdout": stdout[:MAX_CAPTURE], "stderr": stderr[:MAX_CAPTURE], "truncated": True, "timed_out": True}


def compact_tool_result(value: dict[str, Any]) -> dict[str, Any]:
    stdout = value.get("stdout", "")
    stderr = value.get("stderr", "")
    return {
        "argv": value.get("argv"), "returncode": value.get("returncode"),
        "stdout": stdout, "stderr": stderr, "timed_out": bool(value.get("timed_out", False)),
        "truncated": bool(value.get("truncated", False)),
    }


def preflight(root_arg: Path, *, run_tools: bool = False) -> dict[str, Any]:
    root = find_cargo_root(root_arg)
    root_manifest_path = root / "Cargo.toml"
    root_manifest = read_toml(root_manifest_path)
    members = expand_workspace_members(root, root_manifest)
    packages = [package_summary(root, member) for member in members]
    workspace = root_manifest.get("workspace") if isinstance(root_manifest.get("workspace"), dict) else {}
    lock_path = root / "Cargo.lock"
    result: dict[str, Any] = {
        "schema": "bbk.rust-preflight.v1",
        "profile": {"id": PROFILE["id"], "version": PROFILE["version"], "maturity": PROFILE["maturity"]},
        "root": str(root),
        "cargo": {
            "manifest": relpath(root_manifest_path, root),
            "manifest_sha256": sha256_file(root_manifest_path),
            "lock": {"present": lock_path.is_file(), "path": relpath(lock_path, root) if lock_path.is_file() else None, "sha256": sha256_file(lock_path) if lock_path.is_file() else None},
        },
        "workspace": {
            "is_workspace": isinstance(root_manifest.get("workspace"), dict),
            "resolver": workspace.get("resolver") if isinstance(workspace, dict) else None,
            "members": [item["name"] for item in packages],
            "default_members": list(workspace.get("default-members", [])) if isinstance(workspace, dict) and isinstance(workspace.get("default-members"), list) else [],
            "packages": packages,
        },
        "toolchain": toolchain_summary(root),
        "configuration": configuration_summary(root),
        "repository_commands": detect_repository_commands(root),
        "support_signals": scan_support_signals(root, members),
        "tool_observations": {},
    }
    if run_tools:
        observations: dict[str, Any] = {}
        observations["rustc"] = compact_tool_result(run_command(["rustc", "-vV"], root))
        observations["cargo"] = compact_tool_result(run_command(["cargo", "-Vv"], root))
        observations["rustup"] = compact_tool_result(run_command(["rustup", "show", "active-toolchain"], root)) if shutil.which("rustup") else {"returncode": 127, "stderr": "rustup not found"}
        metadata_cmd = ["cargo", "metadata", "--format-version", "1", "--no-deps", "--offline"]
        if lock_path.is_file():
            metadata_cmd.append("--locked")
        metadata = compact_tool_result(run_command(metadata_cmd, root, timeout=60.0))
        if metadata.get("returncode") == 0:
            try:
                parsed = json.loads(metadata.get("stdout", "{}"))
                metadata["parsed"] = {
                    "workspace_root": parsed.get("workspace_root"),
                    "target_directory": parsed.get("target_directory"),
                    "workspace_members": parsed.get("workspace_members", []),
                    "packages": [{"name": p.get("name"), "version": p.get("version"), "id": p.get("id")} for p in parsed.get("packages", [])],
                }
                metadata.pop("stdout", None)
            except json.JSONDecodeError:
                pass
        observations["metadata"] = metadata
        result["tool_observations"] = observations
    digest_payload = dict(result)
    digest_payload.pop("digest", None)
    result["digest"] = sha256_bytes(canonical_bytes(digest_payload))
    return result


def normalize_role(value: str | None) -> str:
    role = (value or "worker").strip().lower().replace("-", "_")
    aliases = {
        "workerdesigner": "worker_designer",
        "verificationdesigner": "verification_designer",
        "architect": "reviewer",
    }
    return aliases.get(role, role)


def load_work_unit(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    value = read_json(path)
    if not isinstance(value, dict):
        raise RustProfileError("work unit must be a JSON object")
    return value


def listify(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, (str, int, float))]
    return []


def git_changed_paths(root: Path) -> list[str]:
    if not (root / ".git").exists() and not shutil.which("git"):
        return []
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z"], cwd=str(root), check=False,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    paths: list[str] = []
    chunks = completed.stdout.split(b"\0")
    for chunk in chunks:
        if not chunk:
            continue
        text = chunk.decode("utf-8", "replace")
        if len(text) < 4:
            continue
        path = text[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return sorted(set(paths))


def collect_scope_paths(root: Path, supplied: Sequence[str], work_unit: dict[str, Any]) -> tuple[list[str], str]:
    candidates: list[str] = list(supplied)
    for key in ("paths", "scope", "writable_paths", "changed_paths", "files", "affectedPaths"):
        candidates.extend(listify(work_unit.get(key)))
    source = "explicit"
    if not candidates:
        candidates = git_changed_paths(root)
        source = "git-status" if candidates else "none"
    normalized: list[str] = []
    for raw in candidates:
        path = Path(raw)
        if path.is_absolute():
            try:
                path = path.resolve().relative_to(root.resolve())
            except ValueError:
                continue
        text = path.as_posix().lstrip("./")
        if text and ".." not in Path(text).parts:
            normalized.append(text)
    return sorted(set(normalized)), source



def resolve_json_paths(root: Path, supplied: Sequence[str], work_unit: dict[str, Any], work_unit_key: str) -> list[Path]:
    values = list(supplied)
    values.extend(listify(work_unit.get(work_unit_key)))
    paths: list[Path] = []
    for raw in values:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        if not path.is_file():
            raise RustProfileError(f"missing alpha.4 planning object: {path}")
        paths.append(path)
    return sorted(set(paths), key=lambda item: str(item))

def path_glob_match(path: str, pattern: str) -> bool:
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern.removeprefix("**/"))


def expand_scan_files(root: Path, scope_paths: Sequence[str], scan: dict[str, Any]) -> list[Path]:
    max_files = int(scan.get("max_files", 5000))
    extensions = set(str(item) for item in scan.get("source_extensions", []))
    excludes = [str(item) for item in scan.get("exclude_globs", [])]
    files: list[Path] = []
    for raw in scope_paths:
        path = (root / raw).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            continue
        candidates: Iterable[Path]
        if path.is_dir():
            candidates = path.rglob("*")
        else:
            candidates = [path]
        for candidate in candidates:
            if len(files) >= max_files:
                break
            if not candidate.is_file():
                continue
            rel = relpath(candidate, root)
            if any(path_glob_match(rel, pattern) for pattern in excludes):
                continue
            if extensions and candidate.suffix not in extensions and candidate.name not in {"Cargo.toml", "Cargo.lock", "build.rs"}:
                continue
            files.append(candidate)
    return sorted(set(files), key=lambda item: relpath(item, root))[:max_files]


def detect_triggers(root: Path, scope_paths: Sequence[str], hints: Sequence[str], change_classes: Sequence[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mapping = read_json(PROFILE_ROOT / PROFILE["selection"]["risk_trigger_map"])
    scan_cfg = mapping.get("scan", {})
    files = expand_scan_files(root, scope_paths, scan_cfg)
    max_bytes = int(scan_cfg.get("max_file_bytes", 1024 * 1024))
    hint_set = {item.strip().lower() for item in hints if item.strip()}
    class_set = {item.strip().lower() for item in change_classes if item.strip()}
    observations: list[dict[str, Any]] = []
    for trigger in mapping.get("triggers", []):
        reasons: list[dict[str, Any]] = []
        trigger_hints = {str(item).lower() for item in trigger.get("hints", [])}
        trigger_classes = {str(item).lower() for item in trigger.get("change_classes", [])}
        matched_hints = sorted(hint_set & trigger_hints)
        matched_classes = sorted(class_set & trigger_classes)
        if matched_hints:
            reasons.append({"kind": "hint", "values": matched_hints})
        if matched_classes:
            reasons.append({"kind": "change-class", "values": matched_classes})
        for scope in scope_paths:
            matched = [pattern for pattern in trigger.get("file_globs", []) if path_glob_match(scope, str(pattern))]
            if matched:
                reasons.append({"kind": "path", "path": scope, "patterns": matched})
        regexes = [re.compile(str(value)) for value in trigger.get("content_regex", [])]
        if regexes:
            for path in files:
                if path.stat().st_size > max_bytes:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                matched = [regex.pattern for regex in regexes if regex.search(text)]
                if matched:
                    reasons.append({"kind": "content", "path": relpath(path, root), "patterns": matched[:8]})
        if reasons:
            observations.append({
                "id": trigger["id"], "reasons": reasons,
                "select": trigger.get("select", []), "gate_tags": trigger.get("gate_tags", []),
            })
    scan_summary = {
        "scope_paths": list(scope_paths), "scanned_files": [relpath(path, root) for path in files],
        "truncated": len(files) >= int(scan_cfg.get("max_files", 5000)),
    }
    return observations, scan_summary


def skill_catalog() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in PROFILE.get("skills", []):
        path = PROFILE_ROOT / item["path"]
        result[item["id"]] = {**item, "sha256": sha256_file(path), "bytes": path.stat().st_size}
    return result


def add_component(target: dict[str, dict[str, Any]], catalog: dict[str, dict[str, Any]], component_id: str, reason: str) -> None:
    if component_id not in catalog:
        raise RustProfileError(f"profile references unknown component: {component_id}")
    current = target.setdefault(component_id, {**catalog[component_id], "reasons": []})
    if reason not in current["reasons"]:
        current["reasons"].append(reason)


def select_components(role: str, task_profile: str, trigger_observations: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mapping = read_json(PROFILE_ROOT / PROFILE["selection"]["task_skill_map"])
    catalog = skill_catalog()
    selected: dict[str, dict[str, Any]] = {}
    recommended: dict[str, dict[str, Any]] = {}
    defaults = mapping.get("defaults", {}).get(role, mapping.get("defaults", {}).get("worker", []))
    for component_id in defaults:
        add_component(selected, catalog, component_id, f"default for role {role}")
    task = mapping.get("task_profiles", {}).get(task_profile, {})
    for component_id in task.get(role, []):
        add_component(selected, catalog, component_id, f"task profile {task_profile} for role {role}")
    review_kinds = {"focused-review", "survey-review"}
    broad = any(item.get("id") == "broad-architecture" for item in trigger_observations)
    for trigger in trigger_observations:
        for component_id in trigger.get("select", []):
            item = catalog.get(component_id)
            if not item:
                continue
            reason = f"trigger {trigger['id']}"
            if role in {"worker", "worker_designer"} and item["kind"] in review_kinds:
                add_component(recommended, catalog, component_id, reason)
            else:
                add_component(selected, catalog, component_id, reason)
    if broad and "comprehensive-analysis-rust" in selected:
        # A broad survey does not automatically fan out into every specialist. Explicit
        # non-broad triggers may still select their focused pack.
        for component_id in list(selected):
            if component_id == "comprehensive-analysis-rust":
                continue
            item = selected[component_id]
            reasons = item.get("reasons", [])
            if item.get("kind") == "focused-review" and reasons == ["trigger broad-architecture"]:
                selected.pop(component_id, None)
    return (
        [selected[key] for key in sorted(selected)],
        [recommended[key] for key in sorted(recommended)],
    )


def affected_packages(preflight_value: dict[str, Any], scope_paths: Sequence[str]) -> list[str]:
    packages = preflight_value.get("workspace", {}).get("packages", [])
    selected: list[tuple[int, str]] = []
    for package in packages:
        root = str(package.get("root") or "").rstrip("/")
        for path in scope_paths:
            if root in {"", "."} or path == root or path.startswith(root + "/"):
                selected.append((len(root), str(package.get("name"))))
                break
    if not selected and len(packages) == 1:
        return [str(packages[0].get("name"))]
    return sorted({name for _, name in selected if name})


def preferred_repo_command(preflight_value: dict[str, Any], gate_id: str) -> list[str] | None:
    recipes = preflight_value.get("repository_commands", {}).get("recipes", {})
    mapping = {
        "rustfmt-check": "format", "rust-focused-tests": "test", "rust-check-affected": "check",
        "rust-clippy-affected": "lint", "rust-package-clean": "package", "rust-mutest-rs": "mutest",
    }
    key = mapping.get(gate_id)
    value = recipes.get(key) if key else None
    return value if isinstance(value, list) else None


def compile_gate_plan(tier: str, trigger_observations: Sequence[dict[str, Any]], preflight_value: dict[str, Any], scope_paths: Sequence[str]) -> dict[str, Any]:
    gate_file = PROFILE_ROOT / PROFILE["gates"]
    definitions = read_json(gate_file)
    trigger_ids = {item["id"] for item in trigger_observations}
    tags = {tag for item in trigger_observations for tag in item.get("gate_tags", [])}
    hints = trigger_ids | tags | {tier}
    packages = affected_packages(preflight_value, scope_paths)
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for recipe in definitions.get("recipes", []):
        minimum = recipe.get("minimum_tier", "critical")
        if TIER_RANK.get(minimum, 99) > TIER_RANK[tier]:
            skipped.append({"id": recipe["id"], "reason": f"minimum tier is {minimum}"})
            continue
        cls = recipe.get("class")
        recipe_triggers = {str(item) for item in recipe.get("triggers", [])}
        applicable = False
        reasons: list[str] = []
        if cls in {"always-cheap", "required-if-configured"}:
            applicable = True
            reasons.append(f"{cls} at {tier} tier")
        if recipe_triggers & hints:
            applicable = True
            reasons.append("matched: " + ", ".join(sorted(recipe_triggers & hints)))
        if recipe["id"] == "rust-build-affected" and TIER_RANK[tier] >= TIER_RANK["material"]:
            applicable = True
            reasons.append("material-or-higher work requires a real build unless repository policy provides a stronger equivalent")
        if not applicable:
            skipped.append({"id": recipe["id"], "reason": "no applicable trigger"})
            continue
        preferred = preferred_repo_command(preflight_value, recipe["id"])
        selected.append({
            **recipe,
            "selection_reasons": reasons,
            "affected_packages": packages,
            "preferred_command": preferred or recipe.get("command"),
            "repository_override": preferred is not None,
            "execution": "planned-only",
        })
    payload = {
        "schema": "bbk.rust-gate-plan.v1", "tier": tier,
        "affected_packages": packages, "trigger_ids": sorted(trigger_ids),
        "policy": definitions.get("policy", {}), "selected": selected, "skipped": skipped,
        "source_sha256": sha256_file(gate_file),
    }
    payload["digest"] = sha256_bytes(canonical_bytes(payload))
    return payload


def profile_package_root_digest() -> str | None:
    path = PROFILE_ROOT / "PACKAGE-MANIFEST.json"
    if not path.is_file():
        return None
    value = read_json(path)
    digest = value.get("root_sha256")
    return str(digest) if isinstance(digest, str) else None


def make_lock(root: Path, preflight_value: dict[str, Any], selected: Sequence[dict[str, Any]], gate_plan: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    profile_record = {
        "id": PROFILE["id"], "package": PROFILE.get("package"), "version": PROFILE["version"],
        "maturity": PROFILE["maturity"],
        "profile_manifest_sha256": sha256_file(PROFILE_ROOT / "PROFILE.json"),
        "package_root_sha256": profile_package_root_digest(),
        "preflight_sha256": preflight_value["digest"],
        "gate_plan_sha256": gate_plan["digest"],
        "selected_components": [{"id": item["id"], "kind": item["kind"], "sha256": item["sha256"]} for item in selected],
        "inputs": inputs,
    }
    digest_payload = {"schema": "bbk.profile-lock-effective.v1", "project_root": str(root), "profiles": [profile_record]}
    effective = sha256_bytes(canonical_bytes(digest_payload))
    timestamp = os.environ.get("BBK_LOCK_TIMESTAMP") or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema": "bbk.profile-lock.v1", "generated_at": timestamp,
        "project_root": str(root), "profiles": [profile_record], "effective_sha256": effective,
    }


def resolve(args: argparse.Namespace) -> dict[str, Any]:
    root = find_cargo_root(Path(args.root or Path.cwd()))
    work_unit = load_work_unit(Path(args.work_unit).expanduser().resolve() if args.work_unit else None)
    task_profile = args.task_profile or str(work_unit.get("task_profile") or work_unit.get("taskProfile") or "implementation")
    tier = args.assurance_tier or str(work_unit.get("assurance_tier") or work_unit.get("assuranceTier") or work_unit.get("risk_tier") or "routine")
    if tier not in TIER_RANK:
        raise RustProfileError(f"unsupported assurance tier: {tier}")
    role = normalize_role(args.role or str(work_unit.get("role") or "worker"))
    hints = sorted(set(list(args.hint or []) + listify(work_unit.get("profile_hints")) + listify(work_unit.get("profileHints")) + listify(work_unit.get("hints"))))
    change_classes = sorted(set(list(args.change_class or []) + listify(work_unit.get("change_classes")) + listify(work_unit.get("changeClasses"))))
    scope_paths, scope_source = collect_scope_paths(root, args.path or [], work_unit)
    preflight_value = preflight(root, run_tools=bool(args.run_tools))
    observations, scan = detect_triggers(root, scope_paths, hints, change_classes)

    contract_paths = resolve_json_paths(root, args.structure_contract or [], work_unit, "implementationStructureContractRefs")
    slice_paths = resolve_json_paths(root, args.execution_slice or [], work_unit, "executionSliceRefs")
    structure_projections: list[dict[str, Any]] = []
    slice_projections: list[dict[str, Any]] = []
    for path in contract_paths:
        projection = rust_structure.structure_projection(
            root=root, contract_path=path, profile=PROFILE, preflight=preflight_value,
            role=role, task_profile=task_profile, assurance_tier=tier,
        )
        structure_projections.append(projection)
        disposition = projection.get("applicability", {}).get("disposition")
        if disposition not in {"NOT_APPLICABLE", "BLOCKED"}:
            observations.append({"id": "implementation-structure", "reasons": [{"kind": "planning-object", "path": str(path), "digest": projection["input"]["digest"]}], "select": ["rust-implementation-structure"], "gate_tags": ["implementation-structure", "structure-review"]})
        if disposition == "BLOCKED":
            raise RustProfileError("invalid ImplementationStructureContract: " + "; ".join(projection.get("blockers", [])))
    for path in slice_paths:
        projection = rust_structure.slice_projection(
            root=root, slice_path=path, profile=PROFILE, preflight=preflight_value,
            role=role, task_profile=task_profile, assurance_tier=tier,
        )
        slice_projections.append(projection)
        disposition = projection.get("applicability", {}).get("disposition")
        if disposition != "BLOCKED":
            observations.append({"id": "execution-slicing", "reasons": [{"kind": "planning-object", "path": str(path), "digest": projection["input"]["digest"]}], "select": ["rust-execution-slicing"], "gate_tags": ["execution-slicing", "slice-touchpoint"]})
        elif projection.get("blockers"):
            raise RustProfileError("invalid or blocked ExecutionSlice: " + "; ".join(projection.get("blockers", [])))

    # A focused structure reviewer is selected only for contract-level material review roles.
    if role in {"reviewer", "validator"} and any(item.get("applicability", {}).get("level") == "contract" for item in structure_projections):
        observations.append({"id": "structure-review", "reasons": [{"kind": "role", "value": role}], "select": ["rust-implementation-structure-review"], "gate_tags": ["structure-review"]})

    observations = sorted(observations, key=lambda item: (str(item.get("id")), json.dumps(item.get("reasons", []), sort_keys=True)))
    selected, recommended = select_components(role, task_profile, observations)
    gate_plan = compile_gate_plan(tier, observations, preflight_value, scope_paths)
    inputs = {
        "role": role, "task_profile": task_profile, "assurance_tier": tier,
        "hints": hints, "change_classes": change_classes, "scope_paths": scope_paths,
        "scope_source": scope_source, "run_tools": bool(args.run_tools),
        "work_unit_sha256": sha256_file(Path(args.work_unit).expanduser().resolve()) if args.work_unit else None,
        "implementation_structure_contracts": [
            {"id": item["input"]["id"], "revision": item["input"].get("revision"), "digest": item["input"]["digest"], "projection_digest": item["output_digest"], "applicability": item["applicability"]}
            for item in structure_projections
        ],
        "execution_slices": [
            {"id": item["input"]["id"], "digest": item["input"]["digest"], "projection_digest": item["output_digest"], "applicability": item["applicability"]}
            for item in slice_projections
        ],
    }
    lock = make_lock(root, preflight_value, selected, gate_plan, inputs)
    result: dict[str, Any] = {
        "schema": "bbk.rust-profile-resolution.v1",
        "profile": {"id": PROFILE["id"], "package": PROFILE.get("package"), "version": PROFILE["version"], "maturity": PROFILE["maturity"]},
        "structure_support": rust_structure.structure_support_status(PROFILE),
        "inputs": inputs,
        "observations": {"triggers": observations, "scan": scan, "preflight_digest": preflight_value["digest"]},
        "preflight": preflight_value,
        "structure_projections": structure_projections,
        "slice_projections": slice_projections,
        "selected_components": selected,
        "recommended_validator_packs": recommended,
        "gate_plan": gate_plan,
        "lock": lock,
        "effective_sha256": lock["effective_sha256"],
        "limitations": [
            "Profile selection does not grant tool, network, credential, filesystem, publication, or execution authority.",
            "Planned gates are not executed by resolution.",
            "Profile projections are views over generic BBK objects and are not authoritative state.",
            "Partial or unqualified support domains require separate project qualification.",
        ],
    }
    return result


def gate_plan_command(args: argparse.Namespace) -> dict[str, Any]:
    resolved = resolve(args)
    return resolved["gate_plan"]



def structure_command(args: argparse.Namespace) -> dict[str, Any]:
    root = find_cargo_root(Path(args.root or Path.cwd()))
    preflight_value = preflight(root, run_tools=False)
    return rust_structure.structure_projection(
        root=root, contract_path=Path(args.contract).expanduser().resolve(), profile=PROFILE,
        preflight=preflight_value, role=normalize_role(args.role),
        task_profile=args.task_profile or "implementation-structure",
        assurance_tier=args.assurance_tier or "material",
    )


def slice_command(args: argparse.Namespace) -> dict[str, Any]:
    root = find_cargo_root(Path(args.root or Path.cwd()))
    preflight_value = preflight(root, run_tools=False)
    return rust_structure.slice_projection(
        root=root, slice_path=Path(args.slice).expanduser().resolve(), profile=PROFILE,
        preflight=preflight_value, role=normalize_role(args.role),
        task_profile=args.task_profile or "execution-slicing",
        assurance_tier=args.assurance_tier or "material",
    )


def structure_review_command(args: argparse.Namespace) -> dict[str, Any]:
    root = find_cargo_root(Path(args.root or Path.cwd()))
    preflight_value = preflight(root, run_tools=False)
    return rust_structure.structure_review(
        root=root, contract_path=Path(args.contract).expanduser().resolve(),
        candidate_path=Path(args.candidate).expanduser().resolve(),
        actual_inventory_path=Path(args.actual_inventory).expanduser().resolve() if args.actual_inventory else None,
        profile=PROFILE, preflight=preflight_value, assurance_tier=args.assurance_tier or "material",
    )

def human(value: dict[str, Any]) -> str:
    schema = value.get("schema")
    if schema == "bbk.rust-preflight.v1":
        return f"Rust preflight: {value['root']}\nPackages: {len(value['workspace']['packages'])}\nToolchain: {value['toolchain'].get('channel') or 'repository/default'}\nDigest: {value['digest']}"
    if schema == "bbk.rust-profile-resolution.v1":
        items = ", ".join(item["id"] for item in value["selected_components"])
        return f"Rust profile resolution\nRole: {value['inputs']['role']}\nTier: {value['inputs']['assurance_tier']}\nComponents: {items}\nGates: {len(value['gate_plan']['selected'])}\nEffective digest: {value['effective_sha256']}"
    if schema == "bbk.rust-gate-plan.v1":
        return "\n".join([f"Rust gate plan ({value['tier']}):", *[f"- {item['id']}" for item in value["selected"]], f"Digest: {value['digest']}"])
    if schema in {"rust.implementation-structure-projection.v1", "rust.execution-slice-projection.v1", "rust.structure-review-result.v1"}:
        disposition = value.get("disposition") or value.get("applicability", {}).get("disposition")
        return f"{schema}\nDisposition: {disposition}\nDigest: {value.get('output_digest')}"
    return pretty(value).rstrip()


def add_resolution_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root")
    parser.add_argument("--work-unit")
    parser.add_argument("--task-profile")
    parser.add_argument("--assurance-tier", choices=list(TIER_RANK))
    parser.add_argument("--role")
    parser.add_argument("--change-class", action="append")
    parser.add_argument("--hint", action="append")
    parser.add_argument("--path", action="append")
    parser.add_argument("--structure-contract", action="append")
    parser.add_argument("--execution-slice", action="append")
    parser.add_argument("--run-tools", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bbk-rust", description=__doc__)
    parser.add_argument("--version", action="version", version=f"bbk-profile-rust {VERSION}")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preflight")
    p.add_argument("--root")
    p.add_argument("--run-tools", action="store_true")
    p.set_defaults(func=lambda args: preflight(Path(args.root or Path.cwd()), run_tools=args.run_tools))
    p = sub.add_parser("resolve")
    add_resolution_args(p)
    p.set_defaults(func=resolve)
    p = sub.add_parser("gate-plan")
    add_resolution_args(p)
    p.set_defaults(func=gate_plan_command)
    p = sub.add_parser("structure")
    p.add_argument("--root")
    p.add_argument("--contract", required=True)
    p.add_argument("--role", default="architect")
    p.add_argument("--task-profile", default="implementation-structure")
    p.add_argument("--assurance-tier", choices=list(TIER_RANK), default="material")
    p.set_defaults(func=structure_command)
    p = sub.add_parser("slice")
    p.add_argument("--root")
    p.add_argument("--slice", required=True)
    p.add_argument("--role", default="planning-wayfinder")
    p.add_argument("--task-profile", default="execution-slicing")
    p.add_argument("--assurance-tier", choices=list(TIER_RANK), default="material")
    p.set_defaults(func=slice_command)
    p = sub.add_parser("structure-review")
    p.add_argument("--root")
    p.add_argument("--contract", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--actual-inventory")
    p.add_argument("--assurance-tier", choices=list(TIER_RANK), default="material")
    p.set_defaults(func=structure_review_command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    normalized = list(sys.argv[1:] if argv is None else argv)
    if "--json" in normalized and normalized and normalized[0] != "--json":
        normalized.remove("--json")
        normalized.insert(0, "--json")
    args = build_parser().parse_args(normalized)
    try:
        value = args.func(args)
    except (RustProfileError, rust_structure.StructureInputError) as exc:
        if args.json:
            print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"bbk-rust: error: {exc}", file=sys.stderr)
        return 2
    print(pretty(value), end="") if args.json else print(human(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
