#!/usr/bin/env python3
"""Deterministic resolver and static preflight for bbk-profile-typescript-javascript.

The profile adds procedure, review criteria, and planned gate recipes. It never
installs tools, executes project gates, grants effects, expands scope, lowers
assurance, or declares a verification pass.
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
from pathlib import Path
from typing import Any, Iterable, Sequence

from tsjs_structure import (
    StructureError,
    read_json as read_structure_json,
    slice_projection,
    structure_projection,
    structure_review,
)

PROFILE_ROOT = Path(os.environ.get("BBK_PROFILE_ROOT", Path(__file__).resolve().parents[1])).resolve()
PROFILE = json.loads((PROFILE_ROOT / "PROFILE.json").read_text(encoding="utf-8"))
VERSION = (PROFILE_ROOT / "VERSION").read_text(encoding="utf-8").strip()
TIER_RANK = {"routine": 0, "material": 1, "consequential": 2, "critical": 3}
MAX_CAPTURE = 256 * 1024
MAX_SCAN_FILES = 256
MAX_SCAN_BYTES = 256 * 1024
SOURCE_EXTENSIONS = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}
TS_EXTENSIONS = {".ts", ".tsx", ".mts", ".cts"}
JS_EXTENSIONS = {".js", ".jsx", ".mjs", ".cjs"}
EXCLUDED_DIRS = {
    ".git", ".jj", ".bbk", ".bbk-kit", ".bbk-worktrees", "node_modules", "dist", "build", "out",
    ".next", ".nuxt", ".svelte-kit", ".turbo", ".nx", "coverage", ".cache", ".vite", ".parcel-cache",
    "vendor", "tmp", "temp", "__pycache__",
}
RELEVANT_ENV = {
    "NODE_ENV", "NODE_OPTIONS", "NODE_PATH", "CI", "COREPACK_HOME", "NPM_CONFIG_USERCONFIG",
    "NPM_CONFIG_REGISTRY", "PNPM_HOME", "YARN_ENABLE_IMMUTABLE_INSTALLS", "BUN_INSTALL", "DENO_DIR",
    "TS_NODE_PROJECT", "TSX_TSCONFIG_PATH", "VITEST_POOL_ID", "PLAYWRIGHT_BROWSERS_PATH",
}
SECRET_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL", "PRIVATE_KEY", "AUTH")


class TsjsProfileError(RuntimeError):
    """Expected user-facing profile error."""


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
        raise TsjsProfileError(f"missing file: {path}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TsjsProfileError(f"invalid JSON in {path}: {exc}") from exc


def strip_json_comments(text: str) -> str:
    output: list[str] = []
    index = 0
    in_string = False
    quote = ""
    escaped = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                in_string = False
            index += 1
            continue
        if char in {'"', "'"}:
            in_string = True
            quote = char
            output.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(text) and not (text[index] == "*" and text[index + 1] == "/"):
                if text[index] in "\r\n":
                    output.append(text[index])
                index += 1
            index += 2
            continue
        output.append(char)
        index += 1
    return "".join(output)


def read_jsonc(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise TsjsProfileError(f"missing file: {path}") from exc
    except UnicodeDecodeError as exc:
        raise TsjsProfileError(f"invalid UTF-8 in {path}: {exc}") from exc
    stripped = strip_json_comments(text)
    stripped = re.sub(r",(?=\s*[}\]])", "", stripped)
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise TsjsProfileError(f"invalid JSON/JSONC in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TsjsProfileError(f"expected an object in {path}")
    return value


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def safe_read_prefix(path: Path, limit: int = MAX_SCAN_BYTES) -> str:
    try:
        data = path.read_bytes()[:limit]
        return data.decode("utf-8", "replace")
    except OSError:
        return ""


def run_read_only(argv: Sequence[str], cwd: Path, timeout: int = 20) -> dict[str, Any]:
    command = [str(item) for item in argv]
    try:
        completed = subprocess.run(
            command, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
        stdout = completed.stdout[:MAX_CAPTURE]
        stderr = completed.stderr[:MAX_CAPTURE]
        return {
            "argv": command, "returncode": completed.returncode, "stdout": stdout.strip(),
            "stderr": stderr.strip(), "truncated": len(completed.stdout) > MAX_CAPTURE or len(completed.stderr) > MAX_CAPTURE,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"argv": command, "returncode": 124 if isinstance(exc, subprocess.TimeoutExpired) else 127, "stdout": "", "stderr": str(exc), "truncated": False}


def package_json(path: Path) -> dict[str, Any]:
    value = read_json(path)
    if not isinstance(value, dict):
        raise TsjsProfileError(f"package.json must contain an object: {path}")
    return value


def package_workspaces(value: dict[str, Any]) -> list[str]:
    raw = value.get("workspaces")
    if isinstance(raw, list):
        return [str(item) for item in raw if isinstance(item, str)]
    if isinstance(raw, dict) and isinstance(raw.get("packages"), list):
        return [str(item) for item in raw["packages"] if isinstance(item, str)]
    return []


def pnpm_workspace_patterns(path: Path) -> list[str]:
    if not path.is_file():
        return []
    values: list[str] = []
    in_packages = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not raw.startswith((" ", "\t")):
            in_packages = line == "packages:"
            continue
        if in_packages and line.startswith("-"):
            value = line[1:].strip().strip('"\'')
            if value:
                values.append(value)
    return values


def workspace_markers(root: Path, pkg: dict[str, Any] | None = None) -> list[str]:
    markers: list[str] = []
    pkg = pkg or {}
    if package_workspaces(pkg):
        markers.append("package.json#workspaces")
    for name in ["pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json", "rush.json", "moon.yml", "moon.yaml"]:
        if (root / name).is_file():
            markers.append(name)
    return markers


def find_project_root(start: Path) -> Path:
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    nearest: Path | None = None
    for candidate in (current, *current.parents):
        has_project = any((candidate / name).is_file() for name in ["package.json", "tsconfig.json", "jsconfig.json", "deno.json", "deno.jsonc"])
        if not has_project:
            continue
        if nearest is None:
            nearest = candidate
        pkg: dict[str, Any] = {}
        if (candidate / "package.json").is_file():
            try:
                pkg = package_json(candidate / "package.json")
            except TsjsProfileError:
                pass
        if workspace_markers(candidate, pkg):
            return candidate
    if nearest is not None:
        return nearest
    raise TsjsProfileError(f"no package.json, tsconfig.json, jsconfig.json, or deno.json found from {current}")


def expand_workspace_members(root: Path, root_pkg: dict[str, Any]) -> list[Path]:
    patterns = package_workspaces(root_pkg) + pnpm_workspace_patterns(root / "pnpm-workspace.yaml")
    excludes = [item[1:] for item in patterns if item.startswith("!")]
    includes = [item for item in patterns if not item.startswith("!")]
    members: set[Path] = set()
    if (root / "package.json").is_file():
        members.add(root.resolve())
    for pattern in includes:
        for raw in glob.glob(str(root / pattern), recursive=True):
            path = Path(raw)
            if path.name == "package.json":
                path = path.parent
            if not path.is_dir() or not (path / "package.json").is_file():
                continue
            rel = relpath(path, root)
            if any(fnmatch.fnmatch(rel, excluded) or fnmatch.fnmatch(rel + "/", excluded) for excluded in excludes):
                continue
            members.add(path.resolve())
    if not members and (root / "package.json").is_file():
        members.add(root.resolve())
    return sorted(members, key=lambda item: relpath(item, root))


def resolve_local_extends(path: Path, value: str) -> Path | None:
    if not value.startswith((".", "/")):
        return None
    candidate = (path.parent / value).resolve()
    choices = [candidate]
    if candidate.suffix == "":
        choices.extend([candidate.with_suffix(".json"), candidate / "tsconfig.json"])
    for item in choices:
        if item.is_file():
            return item
    return None


def merge_dict(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def load_tsconfig(path: Path, seen: set[Path] | None = None) -> tuple[dict[str, Any], list[Path], list[str]]:
    seen = set(seen or set())
    resolved = path.resolve()
    if resolved in seen:
        return {}, [], [f"tsconfig extends cycle at {path}"]
    seen.add(resolved)
    value = read_jsonc(path)
    chain: list[Path] = []
    warnings: list[str] = []
    base: dict[str, Any] = {}
    extends = value.get("extends")
    if isinstance(extends, str):
        parent = resolve_local_extends(path, extends)
        if parent:
            base, chain, warnings = load_tsconfig(parent, seen)
        else:
            warnings.append(f"external or unresolved tsconfig extends: {extends}")
    merged = merge_dict(base, value)
    chain.append(path.resolve())
    return merged, chain, warnings


def iter_source_files(root: Path, nested_package_roots: set[Path] | None = None) -> Iterable[Path]:
    nested = {item.resolve() for item in (nested_package_roots or set()) if item.resolve() != root.resolve()}
    count = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        directory = Path(dirpath).resolve()
        dirnames[:] = sorted([
            name for name in dirnames
            if name not in EXCLUDED_DIRS and (directory / name).resolve() not in nested
        ])
        for name in sorted(filenames):
            path = directory / name
            if path.suffix.lower() in SOURCE_EXTENSIONS or name.endswith((".d.ts", ".d.mts", ".d.cts")):
                yield path
                count += 1
                if count >= 10000:
                    return


def source_summary(package_root: Path, nested: set[Path]) -> dict[str, Any]:
    counts = {"ts": 0, "tsx": 0, "mts": 0, "cts": 0, "js": 0, "jsx": 0, "mjs": 0, "cjs": 0, "declarations": 0, "ts_check_files": 0}
    dom_signals = 0
    omp_signals = 0
    for path in iter_source_files(package_root, nested):
        name = path.name.lower()
        if name.endswith((".d.ts", ".d.mts", ".d.cts")):
            counts["declarations"] += 1
        else:
            key = path.suffix.lower().lstrip(".")
            if key in counts:
                counts[key] += 1
        prefix = safe_read_prefix(path, 8192)
        if path.suffix.lower() in JS_EXTENSIONS and re.search(r"^\s*//\s*@ts-check\b", prefix, re.MULTILINE):
            counts["ts_check_files"] += 1
        if re.search(r"\b(document|window|navigator)\.", prefix):
            dom_signals += 1
        if re.search(r"\b(registerTool|registerCommand|sendMessage)\s*\(", prefix):
            omp_signals += 1
    counts["dom_signal_files"] = dom_signals
    counts["omp_signal_files"] = omp_signals
    return counts


def config_summary(package_root: Path, root: Path) -> dict[str, Any]:
    candidates = [package_root / "tsconfig.json", package_root / "jsconfig.json"]
    primary = next((path for path in candidates if path.is_file()), None)
    configs = sorted({*package_root.glob("tsconfig*.json"), *package_root.glob("jsconfig*.json")})
    merged: dict[str, Any] = {}
    chain: list[Path] = []
    warnings: list[str] = []
    if primary:
        try:
            merged, chain, warnings = load_tsconfig(primary)
        except TsjsProfileError as exc:
            warnings.append(str(exc))
    options = merged.get("compilerOptions") if isinstance(merged.get("compilerOptions"), dict) else {}
    tracked = [
        "strict", "noCheck", "allowJs", "checkJs", "skipLibCheck", "noImplicitAny", "strictNullChecks",
        "noUncheckedIndexedAccess", "exactOptionalPropertyTypes", "useUnknownInCatchVariables", "noImplicitOverride",
        "verbatimModuleSyntax", "isolatedModules", "isolatedDeclarations", "module", "moduleResolution", "target", "lib",
        "jsx", "experimentalDecorators", "emitDecoratorMetadata", "declaration", "declarationMap", "emitDeclarationOnly",
        "noEmit", "composite", "incremental", "baseUrl", "paths", "outDir", "rootDir", "sourceMap", "inlineSourceMap",
    ]
    return {
        "primary": relpath(primary, root) if primary else None,
        "files": [{"path": relpath(path, root), "sha256": sha256_file(path)} for path in configs if path.is_file()],
        "extends_chain": [relpath(path, root) for path in chain],
        "compiler_options": {key: options.get(key) for key in tracked if key in options},
        "project_references": merged.get("references", []) if isinstance(merged.get("references"), list) else [],
        "warnings": warnings,
    }


def dependency_names(pkg: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for section in ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies", "bundledDependencies"]:
        value = pkg.get(section)
        if isinstance(value, dict):
            result[section] = sorted(str(name) for name in value)
        elif isinstance(value, list):
            result[section] = sorted(str(name) for name in value)
        else:
            result[section] = []
    return result


def dependency_specs(pkg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for section in ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]:
        value = pkg.get(section)
        if not isinstance(value, dict):
            continue
        for name, spec in value.items():
            result[str(name)] = {"section": section, "spec": spec}
    return result


def all_dependency_names(dependencies: dict[str, list[str]]) -> set[str]:
    return {name for values in dependencies.values() for name in values}


def detect_tooling(deps: set[str], scripts: dict[str, str]) -> dict[str, list[str]]:
    joined = "\n".join(scripts.values()).lower()
    groups = {
        "typecheckers": ["typescript"],
        "transpilers": ["typescript", "@swc/core", "@babel/core", "esbuild", "tsx", "ts-node"],
        "bundlers": ["vite", "rollup", "webpack", "esbuild", "tsup", "parcel", "@parcel/core", "rspack", "@rspack/core"],
        "declaration_tools": ["typescript", "@microsoft/api-extractor", "rollup-plugin-dts", "vite-plugin-dts"],
        "linters": ["eslint", "@typescript-eslint/parser", "biome", "@biomejs/biome", "oxlint"],
        "formatters": ["prettier", "biome", "@biomejs/biome", "dprint"],
        "test_runners": ["vitest", "jest", "mocha", "ava", "tap", "tsx", "@playwright/test", "cypress"],
        "browser_frameworks": ["react", "preact", "vue", "svelte", "@angular/core", "solid-js", "lit", "next", "nuxt", "astro", "@remix-run/react"],
        "schema_tools": ["zod", "ajv", "valibot", "io-ts", "runtypes", "typebox", "@sinclair/typebox", "joi", "yup"],
        "native_tools": ["node-gyp", "node-pre-gyp", "prebuild", "prebuildify", "@napi-rs/cli", "napi-rs"],
    }
    result: dict[str, list[str]] = {}
    for key, candidates in groups.items():
        selected = [name for name in candidates if name in deps or name.lower() in joined]
        if key == "test_runners" and re.search(r"\bnode\s+--test\b", joined):
            selected.append("node:test")
        result[key] = sorted(set(selected))
    return result


def script_map(pkg: dict[str, Any]) -> dict[str, str]:
    raw = pkg.get("scripts")
    return {str(key): str(value) for key, value in raw.items()} if isinstance(raw, dict) else {}


def package_manager_summary(root: Path, root_pkg: dict[str, Any]) -> dict[str, Any]:
    lock_names = ["package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb", "deno.lock"]
    locks = [{"path": name, "sha256": sha256_file(root / name)} for name in lock_names if (root / name).is_file()]
    declared = root_pkg.get("packageManager") if isinstance(root_pkg.get("packageManager"), str) else None
    name = None
    version = None
    if declared:
        match = re.match(r"^([^@]+)@(.+)$", declared)
        if match:
            name, version = match.group(1), match.group(2)
        else:
            name = declared
    if not name:
        if any(item["path"] in {"package-lock.json", "npm-shrinkwrap.json"} for item in locks):
            name = "npm"
        elif any(item["path"] == "pnpm-lock.yaml" for item in locks):
            name = "pnpm"
        elif any(item["path"] == "yarn.lock" for item in locks):
            name = "yarn"
        elif any(item["path"] in {"bun.lock", "bun.lockb"} for item in locks):
            name = "bun"
        elif any(item["path"] == "deno.lock" for item in locks):
            name = "deno"
    return {
        "declared": declared, "name": name, "version": version, "lockfiles": locks,
        "multiple_lockfiles": len(locks) > 1,
    }


def language_mode(source: dict[str, Any], config: dict[str, Any], scripts: dict[str, str], deps: set[str]) -> dict[str, Any]:
    options = config.get("compiler_options", {})
    ts_count = sum(int(source.get(key, 0)) for key in ["ts", "tsx", "mts", "cts", "declarations"])
    js_count = sum(int(source.get(key, 0)) for key in ["js", "jsx", "mjs", "cjs"])
    script_text = "\n".join(scripts.values()).lower()
    has_semantic_script = bool(re.search(r"\btsc\b", script_text)) and "--nocheck" not in script_text.replace("-", "")
    typescript_present = "typescript" in deps or bool(config.get("primary"))
    checked_js = options.get("checkJs") is True or int(source.get("ts_check_files", 0)) > 0
    no_check = options.get("noCheck") is True
    modes: list[str] = []
    if ts_count:
        if no_check or (not typescript_present and not has_semantic_script):
            modes.append("typescript-transpile-only")
        elif options.get("strict") is True:
            modes.append("typescript-strict")
        else:
            modes.append("typescript-partially-strict")
    if js_count:
        modes.append("javascript-checked" if checked_js else "javascript-unchecked")
    if not modes:
        primary = "unknown"
    elif len(set(modes)) > 1:
        primary = "mixed"
    else:
        primary = modes[0]
    return {
        "primary": primary, "modes_present": sorted(set(modes)), "typescript_files": ts_count, "javascript_files": js_count,
        "semantic_check_signal": has_semantic_script or (typescript_present and not no_check),
        "strict": options.get("strict"), "allow_js": options.get("allowJs"), "check_js": options.get("checkJs"),
        "no_check": options.get("noCheck"), "skip_lib_check": options.get("skipLibCheck"),
        "no_unchecked_indexed_access": options.get("noUncheckedIndexedAccess"),
        "exact_optional_property_types": options.get("exactOptionalPropertyTypes"),
    }


def module_contract(pkg: dict[str, Any], config: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    options = config.get("compiler_options", {})
    package_type = pkg.get("type") if isinstance(pkg.get("type"), str) else None
    has_mts = int(source.get("mts", 0)) > 0
    has_cts = int(source.get("cts", 0)) > 0
    exports = pkg.get("exports")
    conditions: set[str] = set()
    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if isinstance(key, str) and not key.startswith("."):
                    conditions.add(key)
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
    collect(exports)
    if has_mts and has_cts or "import" in conditions and "require" in conditions:
        declared = "dual"
    elif package_type == "module" or has_mts or "import" in conditions:
        declared = "esm"
    elif package_type == "commonjs" or has_cts or "require" in conditions:
        declared = "commonjs"
    else:
        declared = "unspecified"
    return {
        "declared": declared, "package_type": package_type,
        "typescript_module": options.get("module"), "typescript_module_resolution": options.get("moduleResolution"),
        "verbatim_module_syntax": options.get("verbatimModuleSyntax"),
        "exports_present": exports is not None, "imports_present": pkg.get("imports") is not None,
        "conditions": sorted(conditions), "main": pkg.get("main"), "module": pkg.get("module"),
        "browser": pkg.get("browser"), "types": pkg.get("types") or pkg.get("typings"),
        "types_versions": bool(pkg.get("typesVersions")), "bin": pkg.get("bin"), "side_effects": pkg.get("sideEffects"),
    }


def runtime_targets(root: Path, pkg: dict[str, Any], deps: set[str], tooling: dict[str, list[str]], source: dict[str, Any]) -> list[dict[str, Any]]:
    targets: dict[str, list[str]] = {}
    def add(name: str, reason: str) -> None:
        targets.setdefault(name, []).append(reason)
    engines = pkg.get("engines") if isinstance(pkg.get("engines"), dict) else {}
    if engines.get("node") or pkg.get("bin") or any(name in deps for name in ["@types/node", "express", "fastify", "koa", "commander", "yargs"]):
        add("node", "Node engine, CLI, types or server dependency")
    if pkg.get("browser") is not None or pkg.get("browserslist") is not None or tooling.get("browser_frameworks") or int(source.get("dom_signal_files", 0)):
        add("browser", "browser field/list, framework or DOM usage")
    if (root / "bun.lock").is_file() or (root / "bun.lockb").is_file() or (root / "bunfig.toml").is_file() or engines.get("bun"):
        add("bun", "Bun lock/config/engine")
    if any((root / name).is_file() for name in ["deno.json", "deno.jsonc", "deno.lock"]):
        add("deno", "Deno configuration or lockfile")
    if any((root / name).is_file() for name in ["wrangler.toml", "wrangler.json", "wrangler.jsonc"]):
        add("worker", "Worker deployment configuration")
    if "electron" in deps:
        add("electron", "Electron dependency")
    if "react-native" in deps:
        add("react-native", "React Native dependency")
    if tooling.get("native_tools"):
        add("native-addon", "native addon build tooling")
    if int(source.get("omp_signal_files", 0)) or "oh-my-pi" in str(pkg.get("keywords", "")).lower():
        add("omp", "OMP extension API signal")
    if not targets:
        add("unspecified", "No authoritative runtime target detected")
    return [{"id": name, "reasons": reasons} for name, reasons in sorted(targets.items())]


def package_kinds(pkg: dict[str, Any], runtime: list[dict[str, Any]], module: dict[str, Any]) -> list[str]:
    result: set[str] = set()
    if pkg.get("bin"):
        result.add("cli")
    if pkg.get("exports") is not None or pkg.get("types") or pkg.get("typings") or (not pkg.get("private", False) and (pkg.get("main") or pkg.get("module"))):
        result.add("library")
    runtime_ids = {item["id"] for item in runtime}
    if "browser" in runtime_ids:
        result.add("browser-application-or-library")
    if "node" in runtime_ids and "library" not in result and "cli" not in result:
        result.add("node-application-or-service")
    if "omp" in runtime_ids:
        result.add("omp-extension")
    if module.get("declared") == "dual":
        result.add("dual-package")
    return sorted(result or {"unspecified"})


def package_summary(root: Path, package_root: Path, all_members: set[Path]) -> dict[str, Any]:
    pkg_path = package_root / "package.json"
    pkg = package_json(pkg_path) if pkg_path.is_file() else {}
    scripts = script_map(pkg)
    dependencies = dependency_names(pkg)
    deps = all_dependency_names(dependencies)
    nested = {item for item in all_members if item.resolve() != package_root.resolve() and package_root.resolve() in item.resolve().parents}
    source = source_summary(package_root, nested)
    config = config_summary(package_root, root)
    tooling = detect_tooling(deps, scripts)
    language = language_mode(source, config, scripts, deps)
    module = module_contract(pkg, config, source)
    runtime = runtime_targets(root, pkg, deps, tooling, source)
    lifecycle = sorted(name for name in scripts if name in {"preinstall", "install", "postinstall", "prepare", "prepublish", "prepublishOnly", "publish", "postpublish"})
    return {
        "name": pkg.get("name") or package_root.name,
        "version": pkg.get("version"), "private": bool(pkg.get("private", False)),
        "root": relpath(package_root, root), "manifest": relpath(pkg_path, root) if pkg_path.is_file() else None,
        "manifest_sha256": sha256_file(pkg_path) if pkg_path.is_file() else None,
        "package_manager_declared": pkg.get("packageManager"), "engines": pkg.get("engines", {}),
        "scripts": scripts, "lifecycle_scripts": lifecycle, "dependencies": dependencies, "dependency_specs": dependency_specs(pkg),
        "source": source, "config": config, "language": language, "module": module, "runtime_targets": runtime,
        "package_kinds": package_kinds(pkg, runtime, module), "tooling": tooling,
        "public_package": not bool(pkg.get("private", False)) and (pkg.get("exports") is not None or pkg.get("main") or pkg.get("module") or pkg.get("types") or pkg.get("typings")),
        "generated_signals": sorted(name for name in scripts if any(token in name.lower() for token in ["generate", "codegen", "schema", "client"])),
    }


def repository_config_files(root: Path) -> list[dict[str, Any]]:
    names = [
        "package.json", "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "pnpm-workspace.yaml", "yarn.lock",
        "bun.lock", "bun.lockb", "bunfig.toml", "deno.json", "deno.jsonc", "deno.lock", ".npmrc", ".yarnrc", ".yarnrc.yml",
        "turbo.json", "nx.json", "lerna.json", "rush.json", "biome.json", "biome.jsonc", "eslint.config.js", "eslint.config.mjs",
        "eslint.config.cjs", "prettier.config.js", "vite.config.ts", "vite.config.js", "webpack.config.js", "rollup.config.js",
        "tsup.config.ts", "vitest.config.ts", "jest.config.js", "playwright.config.ts", "wrangler.toml",
    ]
    values = []
    for name in names:
        path = root / name
        if path.is_file():
            values.append({"path": name, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    return values


def environment_summary() -> dict[str, Any]:
    """Record only an allowlisted environment fingerprint without secret material.

    Secret-looking variables outside the allowlist are deliberately not enumerated:
    variable names can themselves disclose provider or infrastructure details.  An
    allowlisted value whose name is secret-like records presence only and is never
    hashed, because a digest of a low-entropy credential is still sensitive.
    """
    values: dict[str, Any] = {}
    for key in sorted(RELEVANT_ENV):
        if key not in os.environ:
            continue
        redacted = any(marker in key.upper() for marker in SECRET_MARKERS)
        entry: dict[str, Any] = {"present": True, "redacted": redacted}
        if not redacted:
            entry["sha256"] = sha256_bytes(os.environ[key].encode("utf-8"))
        values[key] = entry
    return values


def repository_commands(manager: dict[str, Any], packages: list[dict[str, Any]]) -> dict[str, Any]:
    name = manager.get("name")
    values: dict[str, Any] = {"package_manager": name, "packages": {}}
    for package in packages:
        values["packages"][package["name"]] = {
            "root": package["root"], "scripts": package["scripts"],
        }
    return values


def tool_versions(root: Path) -> dict[str, Any]:
    commands = {
        "node": ["node", "--version"], "npm": ["npm", "--version"], "pnpm": ["pnpm", "--version"],
        "yarn": ["yarn", "--version"], "bun": ["bun", "--version"], "deno": ["deno", "--version"],
        "tsc": ["tsc", "--version"], "eslint": ["eslint", "--version"], "biome": ["biome", "--version"],
    }
    result: dict[str, Any] = {}
    for name, command in commands.items():
        resolved = shutil.which(command[0])
        if not resolved:
            result[name] = {"available": False}
            continue
        value = run_read_only(command, root)
        result[name] = {"available": True, "resolved": resolved, **value}
    return result


def preflight(start: Path, *, run_tools: bool = False) -> dict[str, Any]:
    root = find_project_root(start)
    root_pkg = package_json(root / "package.json") if (root / "package.json").is_file() else {}
    members = expand_workspace_members(root, root_pkg)
    member_set = {item.resolve() for item in members}
    packages = [package_summary(root, item, member_set) for item in members]
    manager = package_manager_summary(root, root_pkg)
    modes = sorted({package["language"]["primary"] for package in packages})
    if len(modes) > 1 and "unknown" in modes:
        modes.remove("unknown")
    runtime_ids = sorted({target["id"] for package in packages for target in package["runtime_targets"]})
    if len(runtime_ids) > 1 and "unspecified" in runtime_ids:
        runtime_ids.remove("unspecified")
    warnings: list[str] = []
    if manager["multiple_lockfiles"]:
        warnings.append("multiple lockfiles detected; package-manager authority must be explicit")
    for package in packages:
        warnings.extend(f"{package['name']}: {item}" for item in package["config"].get("warnings", []))
        if package["language"]["primary"] == "typescript-transpile-only":
            warnings.append(f"{package['name']}: TypeScript appears to be transpile-only; do not claim semantic type-check evidence")
        if package["module"]["declared"] == "dual":
            warnings.append(f"{package['name']}: dual ESM/CommonJS support requires separate consumer evidence")
    payload: dict[str, Any] = {
        "schema": "bbk.tsjs-preflight.v1", "profile_version": VERSION, "root": str(root),
        "workspace": {
            "markers": workspace_markers(root, root_pkg), "patterns": package_workspaces(root_pkg) + pnpm_workspace_patterns(root / "pnpm-workspace.yaml"),
            "members": [package["name"] for package in packages], "member_roots": [package["root"] for package in packages],
        },
        "package_manager": manager,
        "toolchain": {
            "declared_typescript_specs": sorted({str(package.get("dependency_specs", {}).get("typescript", {}).get("spec")) for package in packages if package.get("dependency_specs", {}).get("typescript", {}).get("spec") is not None}),
            "detected_tooling": sorted({tool for package in packages for values in package["tooling"].values() for tool in values}),
            "executed_versions": tool_versions(root) if run_tools else {},
            "run_tools": run_tools,
        },
        "language": {"project_modes": modes, "checked_packages": [p["name"] for p in packages if p["language"]["primary"] in {"typescript-strict", "typescript-partially-strict", "javascript-checked", "mixed"}], "packages": {p["name"]: p["language"] for p in packages}},
        "runtime": {"targets": runtime_ids, "packages": {p["name"]: p["runtime_targets"] for p in packages}},
        "packages": packages,
        "repository_commands": repository_commands(manager, packages),
        "configuration_files": repository_config_files(root),
        "environment": environment_summary(),
        "warnings": sorted(set(warnings)),
    }
    digest_payload = {key: value for key, value in payload.items() if key != "digest"}
    payload["digest"] = sha256_bytes(canonical_bytes(digest_payload))
    return payload


def load_work_unit(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    value = read_json(path)
    if not isinstance(value, dict):
        raise TsjsProfileError("work unit must be a JSON object")
    return value


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def normalize_role(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    aliases = {
        "verification-designer": "verification-designer", "worker-designer": "worker-designer",
        "architect": "architect", "reviewer": "reviewer", "validator": "validator", "worker": "worker",
        "prototyper": "worker", "implementation-worker": "worker",
    }
    return aliases.get(normalized, normalized)


def git_changed_paths(root: Path) -> list[str]:
    if shutil.which("git") is None:
        return []
    result = run_read_only(["git", "status", "--porcelain=v1", "--untracked-files=all"], root)
    if result["returncode"] != 0:
        return []
    paths: list[str] = []
    for line in result["stdout"].splitlines():
        raw = line[3:] if len(line) > 3 else line
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        if raw:
            paths.append(raw.strip('"'))
    return sorted(set(paths))


def collect_scope_paths(root: Path, explicit: Sequence[str], work_unit: dict[str, Any]) -> tuple[list[str], str]:
    raw = list(explicit)
    source = "explicit"
    if not raw:
        for key in ["paths", "scope", "writable_paths", "readable_paths", "files"]:
            raw.extend(listify(work_unit.get(key)))
        source = "work-unit" if raw else "git-status"
    if not raw:
        raw = git_changed_paths(root)
    if not raw:
        source = "project"
    values: list[str] = []
    for item in raw:
        path = Path(item).expanduser()
        if path.is_absolute():
            values.append(relpath(path, root))
        else:
            values.append(path.as_posix().lstrip("./"))
    return sorted(set(value for value in values if value)), source


def glob_matches(path: str, pattern: str) -> bool:
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch("/" + path, pattern)


def scan_scope(root: Path, paths: Sequence[str]) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    scanned = 0
    for raw in paths:
        candidate = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            continue
        expanded: Iterable[Path]
        if candidate.is_dir():
            expanded = (path for path in candidate.rglob("*") if path.is_file())
        elif candidate.is_file():
            expanded = [candidate]
        else:
            expanded = []
        for path in expanded:
            if scanned >= MAX_SCAN_FILES:
                break
            rel = relpath(path, root)
            if any(part in EXCLUDED_DIRS for part in Path(rel).parts):
                continue
            if path.stat().st_size > MAX_SCAN_BYTES:
                files.append({"path": rel, "bytes": path.stat().st_size, "scanned": False, "reason": "file too large"})
                scanned += 1
                continue
            text = safe_read_prefix(path)
            files.append({"path": rel, "bytes": path.stat().st_size, "scanned": True, "text": text})
            scanned += 1
        if scanned >= MAX_SCAN_FILES:
            break
    return {"file_count": len(files), "truncated": scanned >= MAX_SCAN_FILES, "files": files}


def preflight_trigger_signals(value: dict[str, Any]) -> dict[str, list[str]]:
    signals: dict[str, list[str]] = {}
    def add(trigger: str, reason: str) -> None:
        signals.setdefault(trigger, []).append(reason)
    for package in value.get("packages", []):
        name = package["name"]
        mode = package["language"]["primary"]
        if mode in {"typescript-strict", "typescript-partially-strict", "javascript-checked", "mixed"}:
            add("type-contract", f"{name} uses checked language mode {mode}")
        if package.get("public_package"):
            add("api-module-package", f"{name} exposes a public package surface")
        if package["module"].get("declared") == "dual":
            add("api-module-package", f"{name} declares dual module behavior")
        runtime_ids = {item["id"] for item in package.get("runtime_targets", [])}
        if "browser" in runtime_ids:
            add("browser-ui", f"{name} targets a browser")
        if "omp" in runtime_ids:
            add("host-extension", f"{name} appears to be an OMP extension")
        if package.get("lifecycle_scripts") or package["tooling"].get("native_tools"):
            add("security-supply-chain", f"{name} has lifecycle scripts or native tooling")
        if package.get("generated_signals"):
            add("operational-release", f"{name} has generation scripts")
    return signals


def detect_triggers(root: Path, scope_paths: Sequence[str], hints: Sequence[str], change_classes: Sequence[str], preflight_value: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    definitions = read_json(PROFILE_ROOT / PROFILE["selection"]["risk_trigger_map"])
    scan = scan_scope(root, scope_paths)
    hint_set = {item.lower() for item in hints}
    change_set = {item.lower() for item in change_classes}
    static_signals = preflight_trigger_signals(preflight_value)
    observations: list[dict[str, Any]] = []
    for trigger in definitions.get("triggers", []):
        reasons: list[str] = []
        trigger_hints = {str(item).lower() for item in trigger.get("hints", [])}
        trigger_changes = {str(item).lower() for item in trigger.get("change_classes", [])}
        matched_hints = sorted(hint_set & trigger_hints)
        matched_changes = sorted(change_set & trigger_changes)
        if matched_hints:
            reasons.append("hints: " + ", ".join(matched_hints))
        if matched_changes:
            reasons.append("change classes: " + ", ".join(matched_changes))
        path_matches: set[str] = set()
        content_matches: set[str] = set()
        for file in scan["files"]:
            path = file["path"]
            if any(glob_matches(path, pattern) for pattern in trigger.get("file_globs", [])):
                path_matches.add(path)
            if file.get("scanned"):
                for pattern in trigger.get("content_regex", []):
                    try:
                        if re.search(pattern, file.get("text", ""), re.IGNORECASE | re.MULTILINE):
                            content_matches.add(path)
                            break
                    except re.error as exc:
                        raise TsjsProfileError(f"invalid trigger regex {pattern!r}: {exc}") from exc
        if path_matches:
            reasons.append("paths: " + ", ".join(sorted(path_matches)[:8]))
        if content_matches:
            reasons.append("content: " + ", ".join(sorted(content_matches)[:8]))
        if trigger["id"] in static_signals and (not scope_paths or matched_hints or matched_changes or path_matches or content_matches):
            reasons.extend(static_signals[trigger["id"]])
        if reasons:
            observations.append({
                "id": trigger["id"], "reasons": sorted(set(reasons)),
                "select": trigger.get("select", []), "gate_tags": trigger.get("gate_tags", []),
            })
    return sorted(observations, key=lambda item: item["id"]), {
        "scope_paths": list(scope_paths), "file_count": scan["file_count"], "truncated": scan["truncated"],
        "files": [{key: value for key, value in item.items() if key != "text"} for item in scan["files"]],
    }


def component_catalog() -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in PROFILE["skills"]}


def component_record(component_id: str, reasons: Sequence[str]) -> dict[str, Any]:
    catalog = component_catalog()
    if component_id not in catalog:
        raise TsjsProfileError(f"unknown profile component: {component_id}")
    item = catalog[component_id]
    path = PROFILE_ROOT / item["path"]
    if not path.is_file():
        raise TsjsProfileError(f"missing profile component: {path}")
    return {
        "id": component_id, "kind": item["kind"], "path": item["path"], "sha256": sha256_file(path),
        "selection_reasons": sorted(set(str(reason) for reason in reasons)),
    }


def role_is_worker(role: str) -> bool:
    return role in {"worker"}


def select_components(role: str, task_profile: str, observations: Sequence[dict[str, Any]], tier: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    task_map = read_json(PROFILE_ROOT / PROFILE["selection"]["task_skill_map"])
    task = task_map.get("tasks", {}).get(task_profile)
    if not isinstance(task, dict):
        task = task_map.get("tasks", {}).get("implementation", {})
    observed_ids = {item["id"] for item in observations}
    if "broad-architecture" in observed_ids and not role_is_worker(role):
        return [
            component_record("bbk-tsjs", ["profile router"]),
            component_record("comprehensive-analysis-tsjs", ["explicit broad architecture survey"]),
        ], []
    base_key = "worker" if role_is_worker(role) else "review"
    selected_ids = list(task.get(base_key, ["bbk-tsjs"]))
    reasons: dict[str, list[str]] = {item: [f"task profile {task_profile} for role {role}"] for item in selected_ids}
    triggered_focus: list[str] = []
    for observation in observations:
        for component_id in observation.get("select", []):
            kind = component_catalog().get(component_id, {}).get("kind")
            if role_is_worker(role) and kind in {"focused-review", "survey-review"}:
                triggered_focus.append(component_id)
                continue
            selected_ids.append(component_id)
            reasons.setdefault(component_id, []).append(f"trigger {observation['id']}: " + "; ".join(observation["reasons"]))
    selected_ids = list(dict.fromkeys(selected_ids))
    # Browser review is never selected without a browser trigger.
    if "browser-ui" not in observed_ids and "tsjs-browser-ui-review" in selected_ids:
        selected_ids.remove("tsjs-browser-ui-review")
    selected = [component_record(item, reasons.get(item, ["profile selection"])) for item in selected_ids]
    recommended_ids = [] if TIER_RANK[tier] == TIER_RANK["routine"] else list(task.get("validator_recommendations", [])) + triggered_focus
    recommended: list[dict[str, Any]] = []
    for item in dict.fromkeys(recommended_ids):
        if item == "tsjs-browser-ui-review" and "browser-ui" not in observed_ids:
            continue
        if item in component_catalog():
            recommended.append(component_record(item, ["recommended for a later assertion-scoped reviewer or validator"]))
    return selected, recommended


def affected_packages(preflight_value: dict[str, Any], scope_paths: Sequence[str]) -> list[str]:
    if not scope_paths:
        return [package["name"] for package in preflight_value.get("packages", [])]
    matched: list[tuple[int, str]] = []
    for package in preflight_value.get("packages", []):
        root = package.get("root") or "."
        prefix = "" if root == "." else root.rstrip("/") + "/"
        if any(path == root or path.startswith(prefix) for path in scope_paths):
            matched.append((len(prefix), package["name"]))
    if matched:
        max_len = max(length for length, _ in matched)
        values = sorted({name for length, name in matched if length == max_len or max_len == 0})
        return values
    return [package["name"] for package in preflight_value.get("packages", [])]


def manager_script_command(manager: str | None, script: str, package_root: str = ".", package_name: str | None = None) -> list[str] | None:
    if manager == "npm":
        return ["npm", "run", script, *( ["--workspace", package_root] if package_root not in {"", "."} else [] )]
    if manager == "pnpm":
        return ["pnpm", *( ["--dir", package_root] if package_root not in {"", "."} else [] ), "run", script]
    if manager == "yarn":
        return ["yarn", *( ["workspace", package_name or package_root] if package_root not in {"", "."} else [] ), script]
    if manager == "bun":
        return ["bun", "run", script]
    if manager == "deno":
        return ["deno", "task", script]
    return None


def preferred_script(preflight_value: dict[str, Any], affected: Sequence[str], candidates: Sequence[str]) -> tuple[list[str] | None, dict[str, Any] | None]:
    manager = preflight_value.get("package_manager", {}).get("name")
    package_map = {package["name"]: package for package in preflight_value.get("packages", [])}
    ordered = list(affected) + [name for name in package_map if name not in affected]
    for name in ordered:
        package = package_map.get(name)
        if not package:
            continue
        scripts = package.get("scripts", {})
        for candidate in candidates:
            if candidate in scripts:
                command = manager_script_command(manager, candidate, package.get("root", "."), name)
                return command, {"package": name, "script": candidate, "body": scripts[candidate]}
    return None, None


def frozen_install_command(manager: str | None) -> list[str] | None:
    return {
        "npm": ["npm", "ci"],
        "pnpm": ["pnpm", "install", "--frozen-lockfile"],
        "yarn": ["yarn", "install", "--immutable"],
        "bun": ["bun", "install", "--frozen-lockfile"],
    }.get(manager)


def pack_dry_run_command(manager: str | None) -> list[str] | None:
    if manager == "npm":
        return ["npm", "pack", "--dry-run", "--json"]
    return None


def fallback_command(recipe: dict[str, Any], preflight_value: dict[str, Any], affected: Sequence[str]) -> list[str] | None:
    kind = recipe.get("command_kind")
    manager = preflight_value.get("package_manager", {}).get("name")
    if kind == "frozen-install":
        return frozen_install_command(manager)
    if kind == "pack-dry-run":
        return pack_dry_run_command(manager)
    raw = recipe.get("fallback_command")
    if not isinstance(raw, list):
        return None
    package_map = {package["name"]: package for package in preflight_value.get("packages", [])}
    package = package_map.get(affected[0]) if affected else None
    tsconfig = package.get("config", {}).get("primary") if package else None
    local_tsc = str(Path(package.get("root", ".")) / "node_modules" / ".bin" / ("tsc.cmd" if os.name == "nt" else "tsc")) if package else "node_modules/.bin/tsc"
    result: list[str] = []
    for item in raw:
        value = str(item).replace("{local-typescript}", local_tsc).replace("{tsconfig}", tsconfig or "tsconfig.json")
        result.append(value)
    return result


def compile_gate_plan(tier: str, observations: Sequence[dict[str, Any]], preflight_value: dict[str, Any], scope_paths: Sequence[str]) -> dict[str, Any]:
    gate_file = PROFILE_ROOT / PROFILE["gates"]
    definitions = read_json(gate_file)
    trigger_ids = {item["id"] for item in observations}
    gate_tags = {tag for item in observations for tag in item.get("gate_tags", [])}
    hints = trigger_ids | gate_tags
    if TIER_RANK[tier] >= TIER_RANK["material"]:
        hints.add("material")
    affected = affected_packages(preflight_value, scope_paths)
    checked = bool(preflight_value.get("language", {}).get("checked_packages"))
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for recipe in definitions.get("recipes", []):
        minimum = str(recipe.get("minimum_tier", "routine"))
        if TIER_RANK[tier] < TIER_RANK.get(minimum, 0):
            skipped.append({"id": recipe["id"], "reason": f"requires {minimum} tier"})
            continue
        command, script = preferred_script(preflight_value, affected, recipe.get("script_candidates", []))
        if command is None:
            command = fallback_command(recipe, preflight_value, affected)
        cls = recipe.get("class")
        recipe_triggers = {str(item) for item in recipe.get("triggers", [])}
        matched = sorted(recipe_triggers & hints)
        applicable = False
        reasons: list[str] = []
        if cls == "required-if-configured" and command is not None:
            applicable = True
            reasons.append("repository or qualified fallback command is configured")
        elif cls == "required-when-language-checked" and checked:
            applicable = True
            reasons.append("affected project contains checked TypeScript or JavaScript")
        elif matched:
            applicable = True
            reasons.append("matched: " + ", ".join(matched))
        if recipe["id"] == "tsjs-build-affected" and TIER_RANK[tier] >= TIER_RANK["material"]:
            if command is not None:
                applicable = True
                reasons.append("material-or-higher work requires the real configured build where a build exists")
        if recipe["id"] == "tsjs-typecheck-affected" and checked:
            applicable = True
        if not applicable:
            skipped.append({"id": recipe["id"], "reason": "no applicable trigger or configured command"})
            continue
        required = cls not in {"recommended", "manual-experimental"} or bool(matched)
        command_kind = recipe.get("command_kind")
        if command is not None:
            availability = "AVAILABLE"
        elif command_kind in {"profile-entrypoint", "inspection"}:
            # These gates are executed by BBK/profile orchestration against exact
            # contract, slice, candidate, and inventory inputs. Resolution plans
            # them without fabricating a project command or declaring a pass.
            availability = "PLANNED"
        else:
            availability = "BLOCKED" if required else "ADVISORY"
        selected.append({
            **recipe,
            "selection_reasons": reasons,
            "affected_packages": affected,
            "preferred_command": command,
            "repository_script": script,
            "repository_override": script is not None,
            "availability": availability,
            "execution": "planned-only",
        })
    payload = {
        "schema": "bbk.tsjs-gate-plan.v1", "tier": tier, "affected_packages": affected,
        "trigger_ids": sorted(trigger_ids), "gate_tags": sorted(gate_tags), "policy": definitions.get("policy", {}),
        "selected": selected, "skipped": skipped, "source_sha256": sha256_file(gate_file),
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


def make_lock(
    root: Path,
    preflight_value: dict[str, Any],
    selected: Sequence[dict[str, Any]],
    gate_plan: dict[str, Any],
    inputs: dict[str, Any],
    structure_support: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile_record = {
        "id": PROFILE["id"], "package": PROFILE.get("package"), "version": PROFILE["version"], "maturity": PROFILE["maturity"],
        "profile_manifest_sha256": sha256_file(PROFILE_ROOT / "PROFILE.json"),
        "package_root_sha256": profile_package_root_digest(),
        "preflight_sha256": preflight_value["digest"], "gate_plan_sha256": gate_plan["digest"],
        "selected_components": [{"id": item["id"], "kind": item["kind"], "sha256": item["sha256"]} for item in selected],
        "inputs": inputs,
    }
    if structure_support:
        profile_record["implementation_structure"] = {
            "support_status": PROFILE.get("capabilities", {}).get("implementation_structure", {}).get("status", "unsupported"),
            "contract_digest": structure_support.get("contract_digest"),
            "contract_projection_digest": structure_support.get("contract_projection_digest"),
            "slice_digest": structure_support.get("slice_digest"),
            "slice_projection_digest": structure_support.get("slice_projection_digest"),
        }
    digest_payload = {"schema": "bbk.profile-lock-effective.v1", "project_root": str(root), "profiles": [profile_record]}
    effective = sha256_bytes(canonical_bytes(digest_payload))
    timestamp = os.environ.get("BBK_LOCK_TIMESTAMP") or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {"schema": "bbk.profile-lock.v1", "generated_at": timestamp, "project_root": str(root), "profiles": [profile_record], "effective_sha256": effective}


def resolve(args: argparse.Namespace) -> dict[str, Any]:
    root = find_project_root(Path(args.root or Path.cwd()))
    work_unit = load_work_unit(Path(args.work_unit).expanduser().resolve() if args.work_unit else None)
    inferred_task_profile = "implementation"
    if args.structure_contract:
        inferred_task_profile = "implementation-structure"
    elif args.execution_slice:
        inferred_task_profile = "execution-slicing"
    task_profile = args.task_profile or str(work_unit.get("task_profile") or inferred_task_profile)
    tier = args.assurance_tier or str(work_unit.get("assurance_tier") or work_unit.get("risk_tier") or "routine")
    if tier not in TIER_RANK:
        raise TsjsProfileError(f"unsupported assurance tier: {tier}")
    role = normalize_role(args.role or str(work_unit.get("role") or "worker"))
    hints = list(args.hint or []) + listify(work_unit.get("profile_hints")) + listify(work_unit.get("hints"))
    if args.structure_contract:
        hints.append("implementation-structure")
    if args.execution_slice:
        hints.append("execution-slicing")
    hints = sorted(set(hints))
    change_classes = sorted(set(list(args.change_class or []) + listify(work_unit.get("change_classes"))))
    scope_paths, scope_source = collect_scope_paths(root, args.path or [], work_unit)
    preflight_value = preflight(root, run_tools=bool(args.run_tools))
    observations, scan = detect_triggers(root, scope_paths, hints, change_classes, preflight_value)
    selected, recommended = select_components(role, task_profile, observations, tier)
    gate_plan = compile_gate_plan(tier, observations, preflight_value, scope_paths)
    structure_support: dict[str, Any] = {
        "support_status": PROFILE.get("capabilities", {}).get("implementation_structure", {}).get("status", "unsupported"),
        "contract": None,
        "slice": None,
    }
    if args.structure_contract:
        contract_path = Path(args.structure_contract).expanduser().resolve()
        contract = read_structure_json(contract_path)
        contract_projection = structure_projection(
            root, contract, profile=PROFILE, role=role, task_profile=task_profile,
            assurance_tier=tier, preflight=preflight_value,
        )
        structure_support.update({
            "contract": contract_projection,
            "contract_digest": contract_projection["input"]["digest"],
            "contract_projection_digest": contract_projection["output_digest"],
        })
    if args.execution_slice:
        slice_path = Path(args.execution_slice).expanduser().resolve()
        slice_value = read_structure_json(slice_path)
        projected_slice = slice_projection(
            root, slice_value, profile=PROFILE, role=role, task_profile=task_profile,
            assurance_tier=tier, preflight=preflight_value,
        )
        structure_support.update({
            "slice": projected_slice,
            "slice_digest": projected_slice["input"]["digest"],
            "slice_projection_digest": projected_slice["output_digest"],
        })
    inputs = {
        "role": role, "task_profile": task_profile, "assurance_tier": tier, "hints": hints,
        "change_classes": change_classes, "scope_paths": scope_paths, "scope_source": scope_source,
        "run_tools": bool(args.run_tools),
        "work_unit_sha256": sha256_file(Path(args.work_unit).expanduser().resolve()) if args.work_unit else None,
        "structure_contract_sha256": sha256_file(Path(args.structure_contract).expanduser().resolve()) if args.structure_contract else None,
        "execution_slice_sha256": sha256_file(Path(args.execution_slice).expanduser().resolve()) if args.execution_slice else None,
    }
    lock = make_lock(root, preflight_value, selected, gate_plan, inputs, structure_support)
    return {
        "schema": "bbk.tsjs-profile-resolution.v1",
        "profile": {"id": PROFILE["id"], "package": PROFILE.get("package"), "version": PROFILE["version"], "maturity": PROFILE["maturity"]},
        "inputs": inputs,
        "observations": {"triggers": observations, "scan": scan, "preflight_digest": preflight_value["digest"]},
        "preflight": preflight_value,
        "selected_components": selected,
        "recommended_validator_packs": recommended,
        "gate_plan": gate_plan,
        "implementation_structure": structure_support,
        "lock": lock,
        "effective_sha256": lock["effective_sha256"],
        "limitations": [
            "Profile selection grants no tool, network, credential, installation, filesystem, publication, deployment, or semantic authority.",
            "Planned gates are not executed by resolution.",
            "Type checking, transformation, bundling, declaration emit, artifact execution, and packed-consumer behavior remain separate evidence classes.",
            "Conditional and unqualified runtimes require project-specific evidence.",
        ],
    }


def gate_plan_command(args: argparse.Namespace) -> dict[str, Any]:
    return resolve(args)["gate_plan"]


def structure_command(args: argparse.Namespace) -> dict[str, Any]:
    root = find_project_root(Path(args.root or Path.cwd()))
    contract = read_structure_json(Path(args.contract).expanduser().resolve())
    preflight_value = preflight(root, run_tools=bool(args.run_tools))
    return structure_projection(
        root, contract, profile=PROFILE, role=normalize_role(args.role or "architect"),
        task_profile=args.task_profile or "implementation-structure",
        assurance_tier=args.assurance_tier or str((contract.get("review") or {}).get("assuranceTier") or "material"),
        preflight=preflight_value,
    )


def slice_command(args: argparse.Namespace) -> dict[str, Any]:
    root = find_project_root(Path(args.root or Path.cwd()))
    value = read_structure_json(Path(args.slice).expanduser().resolve())
    preflight_value = preflight(root, run_tools=bool(args.run_tools))
    return slice_projection(
        root, value, profile=PROFILE, role=normalize_role(args.role or "planning-wayfinder"),
        task_profile=args.task_profile or "execution-slicing",
        assurance_tier=args.assurance_tier or "material", preflight=preflight_value,
    )


def structure_review_command(args: argparse.Namespace) -> dict[str, Any]:
    root = find_project_root(Path(args.root or Path.cwd()))
    contract = read_structure_json(Path(args.contract).expanduser().resolve())
    candidate = read_structure_json(Path(args.candidate).expanduser().resolve())
    actual_inventory = read_structure_json(Path(args.actual_inventory).expanduser().resolve()) if args.actual_inventory else None
    preflight_value = preflight(root, run_tools=bool(args.run_tools))
    return structure_review(
        root, contract, candidate, profile=PROFILE,
        assurance_tier=args.assurance_tier or str((contract.get("review") or {}).get("assuranceTier") or "material"),
        preflight=preflight_value, actual_inventory=actual_inventory,
    )


def human(value: dict[str, Any]) -> str:
    schema = value.get("schema")
    if schema == "bbk.tsjs-preflight.v1":
        return (
            f"TS/JS preflight: {value['root']}\n"
            f"Packages: {len(value['packages'])}\n"
            f"Language modes: {', '.join(value['language']['project_modes']) or 'unknown'}\n"
            f"Runtimes: {', '.join(value['runtime']['targets'])}\n"
            f"Digest: {value['digest']}"
        )
    if schema == "bbk.tsjs-profile-resolution.v1":
        components = ", ".join(item["id"] for item in value["selected_components"])
        return (
            f"TS/JS profile resolution\nRole: {value['inputs']['role']}\nTier: {value['inputs']['assurance_tier']}\n"
            f"Components: {components}\nGates: {len(value['gate_plan']['selected'])}\nEffective digest: {value['effective_sha256']}"
        )
    if schema == "bbk.tsjs-gate-plan.v1":
        return "\n".join([f"TS/JS gate plan ({value['tier']}):", *[f"- {item['id']} [{item['availability']}]" for item in value["selected"]], f"Digest: {value['digest']}"])
    if schema == "bbk.tsjs-implementation-structure-projection.v1":
        return f"TS/JS structure projection: {value['applicability']['disposition']}\nContract: {value['input']['id']}@{value['input']['revision']}\nArtifacts: {len(value['projection']['artifact_topology'])}\nDigest: {value['output_digest']}"
    if schema == "bbk.tsjs-execution-slice-projection.v1":
        return f"TS/JS execution-slice projection: {value['applicability']['disposition']}\nSlice: {value['input']['id']}\nTouchpoint: {value['projection']['touchpoint'].get('kind')}\nDigest: {value['output_digest']}"
    if schema == "bbk.tsjs-structure-review-result.v1":
        return f"TS/JS structure review: {value['disposition']}\nContract: {value['input']['id']}@{value['input']['revision']}\nFindings: {len(value['findings'])}\nDigest: {value['output_digest']}"
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
    parser.add_argument("--run-tools", action="store_true")
    parser.add_argument("--structure-contract")
    parser.add_argument("--execution-slice")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bbk-tsjs", description=__doc__)
    parser.add_argument("--version", action="version", version=f"bbk-profile-typescript-javascript {VERSION}")
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
    p.add_argument("--role")
    p.add_argument("--task-profile", default="implementation-structure")
    p.add_argument("--assurance-tier", choices=list(TIER_RANK))
    p.add_argument("--run-tools", action="store_true")
    p.set_defaults(func=structure_command)
    p = sub.add_parser("slice")
    p.add_argument("--root")
    p.add_argument("--slice", required=True)
    p.add_argument("--role")
    p.add_argument("--task-profile", default="execution-slicing")
    p.add_argument("--assurance-tier", choices=list(TIER_RANK), default="material")
    p.add_argument("--run-tools", action="store_true")
    p.set_defaults(func=slice_command)
    p = sub.add_parser("structure-review")
    p.add_argument("--root")
    p.add_argument("--contract", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--actual-inventory")
    p.add_argument("--assurance-tier", choices=list(TIER_RANK))
    p.add_argument("--run-tools", action="store_true")
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
    except (TsjsProfileError, StructureError) as exc:
        if args.json:
            print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"bbk-tsjs: error: {exc}", file=sys.stderr)
        return 2
    print(pretty(value), end="") if args.json else print(human(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
