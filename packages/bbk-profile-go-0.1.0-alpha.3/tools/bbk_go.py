#!/usr/bin/env python3
"""Deterministic resolver and preflight CLI for bbk-profile-go.

The profile adds procedure, routing, and gate recipes. It never grants tools,
network access, mutation authority, broader scope, or a verification pass.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence

PROFILE_ROOT = Path(os.environ.get("BBK_PROFILE_ROOT", Path(__file__).resolve().parents[1])).resolve()
PROFILE = json.loads((PROFILE_ROOT / "PROFILE.json").read_text(encoding="utf-8"))
VERSION = (PROFILE_ROOT / "VERSION").read_text(encoding="utf-8").strip()
TIER_RANK = {"routine": 0, "material": 1, "consequential": 2, "critical": 3}
SECRET_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL", "PRIVATE_KEY", "AUTH")
MAX_CAPTURE = 256 * 1024
EXCLUDED_DIRS = {".git", ".jj", ".bbk", ".bbk-kit", ".bbk-worktrees", "vendor", "node_modules", "dist", "build"}


class GoProfileError(RuntimeError):
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
        raise GoProfileError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GoProfileError(f"invalid JSON in {path}: {exc}") from exc


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def strip_go_comment(line: str) -> str:
    # go.mod/go.work paths and versions do not use // as meaningful data. Preserve
    # quoted strings conservatively by only treating // after whitespace as comment.
    match = re.search(r"\s//", line)
    return line[: match.start()].rstrip() if match else line.rstrip()


def parse_go_directives(path: Path) -> dict[str, Any]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise GoProfileError(f"unable to read {path}: {exc}") from exc
    values: dict[str, Any] = {
        "module": None,
        "go": None,
        "toolchain": None,
        "godebug": [],
        "use": [],
        "require": [],
        "replace": [],
        "exclude": [],
        "retract": [],
        "tool": [],
        "unknown": [],
    }
    block: str | None = None
    recognized = set(values)
    for number, raw in enumerate(lines, start=1):
        line = strip_go_comment(raw).strip()
        if not line or line.startswith("//"):
            continue
        if line == ")":
            block = None
            continue
        if line.endswith("("):
            directive = line[:-1].strip().split()[0]
            block = directive
            if directive not in recognized:
                values["unknown"].append({"line": number, "text": line})
            continue
        parts = line.split(None, 1)
        directive = block or parts[0]
        body = line if block else (parts[1].strip() if len(parts) > 1 else "")
        if directive in {"module", "go", "toolchain"}:
            if values[directive] is None:
                values[directive] = body
            else:
                values["unknown"].append({"line": number, "text": line, "reason": f"duplicate {directive}"})
        elif directive in {"godebug", "use", "require", "replace", "exclude", "retract", "tool"}:
            values[directive].append(body)
        elif directive not in {"module", "go", "toolchain"}:
            values["unknown"].append({"line": number, "text": line})
    return values


def ancestors(start: Path) -> list[Path]:
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    return [current, *current.parents]


def resolve_env_gowork(start: Path) -> Path | None:
    raw = os.environ.get("GOWORK", "").strip()
    if not raw or raw.lower() in {"auto", "off"}:
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (start / path).resolve()
    return path if path.is_file() else None


def find_go_root(start: Path) -> tuple[Path, Path | None, Path | None]:
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    env_work = resolve_env_gowork(current)
    if env_work is not None:
        return env_work.parent, env_work, None
    work: Path | None = None
    module: Path | None = None
    for candidate in ancestors(current):
        if work is None and (candidate / "go.work").is_file():
            work = candidate / "go.work"
        if module is None and (candidate / "go.mod").is_file():
            module = candidate / "go.mod"
    if os.environ.get("GOWORK", "").strip().lower() == "off":
        work = None
    if work is not None:
        return work.parent, work, module
    if module is not None:
        return module.parent, None, module
    raise GoProfileError(f"no go.work or go.mod found from {current}")


def resolve_workspace_modules(root: Path, work_path: Path | None, nearest_mod: Path | None) -> list[Path]:
    modules: list[Path] = []
    if work_path is not None:
        work = parse_go_directives(work_path)
        for raw in work.get("use", []):
            value = raw.strip().strip('"')
            if not value:
                continue
            candidate = (work_path.parent / value).resolve()
            if candidate.name == "go.mod":
                candidate = candidate.parent
            if (candidate / "go.mod").is_file():
                modules.append(candidate)
    elif nearest_mod is not None:
        modules.append(nearest_mod.parent.resolve())
    if not modules:
        # Invalid or unusual workspace: preserve a bounded inventory without claiming
        # these are active main modules.
        for path in sorted(root.rglob("go.mod")):
            if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
                continue
            modules.append(path.parent.resolve())
    unique: list[Path] = []
    seen: set[str] = set()
    for module in modules:
        key = os.path.normcase(str(module))
        if key not in seen:
            seen.add(key)
            unique.append(module)
    return unique


def iter_source_files(module_root: Path, max_files: int = 10000) -> Iterable[Path]:
    count = 0
    for dirpath, dirnames, filenames in os.walk(module_root, topdown=True, followlinks=False):
        directory = Path(dirpath)
        dirnames[:] = sorted(name for name in dirnames if name not in EXCLUDED_DIRS and not name.startswith("."))
        if "testdata" in directory.parts:
            continue
        for name in sorted(filenames):
            if Path(name).suffix.lower() not in {".go", ".s", ".c", ".h"}:
                continue
            yield directory / name
            count += 1
            if count >= max_files:
                return


def package_name(text: str) -> str | None:
    match = re.search(r"(?m)^\s*package\s+([A-Za-z_][A-Za-z0-9_]*)\b", text)
    return match.group(1) if match else None


def module_summary(project_root: Path, module_root: Path) -> dict[str, Any]:
    mod_path = module_root / "go.mod"
    directives = parse_go_directives(mod_path)
    module_path = directives.get("module") or module_root.name
    sum_path = module_root / "go.sum"
    packages: dict[str, dict[str, Any]] = {}
    signals = {
        "unsafe": False,
        "cgo": False,
        "assembly": False,
        "go_directives": [],
        "generation": False,
        "generated_files": 0,
        "embed": False,
        "concurrency": False,
        "http": False,
        "database": False,
        "htmx": False,
        "pgo": (module_root / "default.pgo").is_file(),
    }
    build_tags: set[str] = set()
    for path in iter_source_files(module_root):
        rel_module = path.relative_to(module_root).as_posix()
        rel_dir = path.parent.relative_to(module_root).as_posix()
        if path.suffix.lower() == ".s":
            signals["assembly"] = True
        text = ""
        if path.stat().st_size <= 1024 * 1024:
            text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".go":
            pkg = package_name(text) or "<unknown>"
            record = packages.setdefault(rel_dir, {
                "directory": rel_dir,
                "package": pkg,
                "import_path": str(module_path).rstrip("/") + ("/" + rel_dir if rel_dir not in {"", "."} else ""),
                "go_files": 0,
                "test_files": 0,
                "main": False,
                "internal": "/internal/" in f"/{rel_dir}/" or rel_dir.startswith("internal/"),
            })
            record["go_files"] += 1
            if path.name.endswith("_test.go"):
                record["test_files"] += 1
            if pkg == "main":
                record["main"] = True
            if re.search(r'(?m)^\s*import\s+(?:\([^)]*)?\s*"unsafe"', text) or '"unsafe"' in text:
                signals["unsafe"] = True
            if re.search(r'(?m)^\s*import\s+(?:\([^)]*)?\s*"C"', text) or '"C"' in text:
                signals["cgo"] = True
            if "//go:generate" in text:
                signals["generation"] = True
            if re.search(r"(?m)^// Code generated .* DO NOT EDIT\.?$", text):
                signals["generated_files"] += 1
            if "//go:embed" in text or '"embed"' in text:
                signals["embed"] = True
            if re.search(r"\bgo\s+[A-Za-z_(]|\bchan\b|context\.|sync\.|atomic\.", text):
                signals["concurrency"] = True
            if '"net/http"' in text or "http.Server" in text:
                signals["http"] = True
            if '"database/sql"' in text:
                signals["database"] = True
            if re.search(r"hx-(get|post|put|patch|delete|swap|target)|x-data|Alpine\.", text):
                signals["htmx"] = True
            for directive in re.findall(r"(?m)^//go:([A-Za-z0-9_]+)", text):
                signals["go_directives"].append(directive)
            for tag_line in re.findall(r"(?m)^//go:build\s+(.+)$", text):
                build_tags.add(tag_line.strip())
    package_list = sorted(packages.values(), key=lambda item: item["directory"])
    command_packages = [item["import_path"] for item in package_list if item["main"]]
    return {
        "module_path": module_path,
        "root": relpath(module_root, project_root),
        "go_mod": {"path": relpath(mod_path, project_root), "sha256": sha256_file(mod_path), "directives": directives},
        "go_sum": {"present": sum_path.is_file(), "path": relpath(sum_path, project_root) if sum_path.is_file() else None, "sha256": sha256_file(sum_path) if sum_path.is_file() else None},
        "vendor": {"present": (module_root / "vendor" / "modules.txt").is_file(), "sha256": sha256_file(module_root / "vendor" / "modules.txt") if (module_root / "vendor" / "modules.txt").is_file() else None},
        "default_pgo": {"present": (module_root / "default.pgo").is_file(), "sha256": sha256_file(module_root / "default.pgo") if (module_root / "default.pgo").is_file() else None},
        "packages": package_list,
        "command_packages": command_packages,
        "build_tags": sorted(build_tags),
        "support_signals": {**signals, "go_directives": sorted(set(signals["go_directives"]))},
    }


def configuration_summary(root: Path) -> dict[str, Any]:
    fixed = {
        "GOTOOLCHAIN", "GOWORK", "GOMOD", "GOENV", "GOFLAGS", "GOEXPERIMENT", "GOOS", "GOARCH", "GOAMD64", "GOARM", "GOARM64", "GOMIPS", "GOMIPS64", "GOWASM",
        "CGO_ENABLED", "CC", "CXX", "CGO_CFLAGS", "CGO_CPPFLAGS", "CGO_CXXFLAGS", "CGO_FFLAGS", "CGO_LDFLAGS",
        "GOPROXY", "GOSUMDB", "GOPRIVATE", "GONOPROXY", "GONOSUMDB", "GOVCS", "GOAUTH", "GODEBUG",
    }
    records: list[dict[str, Any]] = []
    for key, value in sorted(os.environ.items()):
        if key not in fixed:
            continue
        records.append({
            "name": key,
            "value_sha256": sha256_bytes(value.encode("utf-8")),
            "bytes": len(value.encode("utf-8")),
            "redacted": any(marker in key.upper() for marker in SECRET_MARKERS) or key in {"GOPRIVATE", "GONOPROXY", "GONOSUMDB", "GOAUTH"},
        })
    return {"environment": records}


def detect_repository_commands(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"files": [], "recipes": {}}
    candidates = [root / "Justfile", root / "justfile", root / "Makefile", root / "makefile", root / "Taskfile.yml", root / "Taskfile.yaml"]
    patterns = {
        "format": [r"(?m)^(?:fmt|format|fmt-check|format-check)\s*[:=]"],
        "lint": [r"(?m)^(?:lint|vet|staticcheck|check-lints)\s*[:=]"],
        "test": [r"(?m)^(?:test|tests|unit-test)\s*[:=]"],
        "check": [r"(?m)^(?:check|ci|verify)\s*[:=]"],
        "generate": [r"(?m)^(?:generate|gen|generated-check)\s*[:=]"],
        "race": [r"(?m)^(?:race|test-race)\s*[:=]"],
        "fuzz": [r"(?m)^(?:fuzz|test-fuzz)\s*[:=]"],
        "coverage": [r"(?m)^(?:coverage|cover)\s*[:=]"],
        "vuln": [r"(?m)^(?:vuln|vulncheck|security)\s*[:=]"],
        "package": [r"(?m)^(?:package|module-release|dist)\s*[:=]"],
        "release": [r"(?m)^(?:release|release-check)\s*[:=]"],
        "matrix": [r"(?m)^(?:matrix|test-matrix|platform-matrix)\s*[:=]"],
        "mutation": [r"(?m)^(?:mutation|mutate|mutation-test)\s*[:=]"],
    }
    for path in candidates:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name.lower().startswith("taskfile"):
            kind = "task"
            executable = "task"
        elif path.name.lower() == "justfile":
            kind = "just"
            executable = "just"
        else:
            kind = "make"
            executable = "make"
        result["files"].append({"path": relpath(path, root), "sha256": sha256_file(path), "kind": kind})
        for purpose, regexes in patterns.items():
            for regex in regexes:
                match = re.search(regex, text)
                if match:
                    target = match.group(0).split(":", 1)[0].split("=", 1)[0].strip()
                    result["recipes"].setdefault(purpose, [executable, target])
                    break
    return result


def run_command(argv: Sequence[str], cwd: Path, timeout: float = 30.0) -> dict[str, Any]:
    env = os.environ.copy()
    env.update({"GOTOOLCHAIN": "local", "GOPROXY": "off", "GOSUMDB": "off"})
    started = dt.datetime.now(dt.timezone.utc)
    try:
        completed = subprocess.run(
            [str(item) for item in argv], cwd=str(cwd), env=env, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
        return {
            "argv": list(argv), "returncode": completed.returncode,
            "stdout": completed.stdout[:MAX_CAPTURE], "stderr": completed.stderr[:MAX_CAPTURE],
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
    return {
        "argv": value.get("argv"), "returncode": value.get("returncode"),
        "stdout": value.get("stdout", ""), "stderr": value.get("stderr", ""),
        "timed_out": bool(value.get("timed_out", False)), "truncated": bool(value.get("truncated", False)),
    }


def aggregate_support(modules: Sequence[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "unsafe": False, "cgo": False, "assembly": False, "generation": False,
        "generated_files": 0, "embed": False, "concurrency": False, "http": False,
        "database": False, "htmx": False, "pgo": False, "go_directives": [],
    }
    for module in modules:
        signals = module.get("support_signals", {})
        for key in ["unsafe", "cgo", "assembly", "generation", "embed", "concurrency", "http", "database", "htmx", "pgo"]:
            result[key] = bool(result[key] or signals.get(key))
        result["generated_files"] += int(signals.get("generated_files", 0))
        result["go_directives"].extend(signals.get("go_directives", []))
    result["go_directives"] = sorted(set(result["go_directives"]))
    return result


def preflight(root_arg: Path, *, run_tools: bool = False) -> dict[str, Any]:
    root, work_path, nearest_mod = find_go_root(root_arg)
    module_roots = resolve_workspace_modules(root, work_path, nearest_mod)
    modules = [module_summary(root, module) for module in module_roots]
    work = None
    if work_path is not None:
        work = {"path": relpath(work_path, root), "sha256": sha256_file(work_path), "directives": parse_go_directives(work_path)}
    result: dict[str, Any] = {
        "schema": "bbk.go-preflight.v1",
        "profile": {"id": PROFILE["id"], "version": PROFILE["version"], "maturity": PROFILE["maturity"]},
        "root": str(root),
        "workspace": {
            "active": work_path is not None,
            "go_work": work,
            "nearest_go_mod": relpath(nearest_mod, root) if nearest_mod else None,
            "module_roots": [module["root"] for module in modules],
            "module_paths": [module["module_path"] for module in modules],
        },
        "modules": modules,
        "toolchain": {
            "workspace_go": work["directives"].get("go") if work else None,
            "workspace_toolchain": work["directives"].get("toolchain") if work else None,
            "module_go": {module["module_path"]: module["go_mod"]["directives"].get("go") for module in modules},
            "module_toolchain": {module["module_path"]: module["go_mod"]["directives"].get("toolchain") for module in modules},
        },
        "configuration": configuration_summary(root),
        "repository_commands": detect_repository_commands(root),
        "support_signals": aggregate_support(modules),
        "tool_observations": {},
    }
    if run_tools:
        observations: dict[str, Any] = {}
        observations["go_version"] = compact_tool_result(run_command(["go", "version"], root))
        env_names = ["GOOS", "GOARCH", "CGO_ENABLED", "GOVERSION", "GOTOOLCHAIN", "GOWORK", "GOMOD", "GOFLAGS", "GOEXPERIMENT", "GOPROXY", "GOSUMDB", "GOPRIVATE", "GONOPROXY", "GONOSUMDB", "GOVCS", "GOAUTH", "CC", "CXX"]
        env_result = compact_tool_result(run_command(["go", "env", "-json", *env_names], root))
        if env_result.get("returncode") == 0:
            try:
                raw = json.loads(env_result.get("stdout") or "{}")
                safe = {key: value for key, value in raw.items() if key in {"GOOS", "GOARCH", "CGO_ENABLED", "GOVERSION", "GOTOOLCHAIN", "GOWORK", "GOMOD", "GOFLAGS", "GOEXPERIMENT", "CC", "CXX"}}
                sensitive = {key: {"sha256": sha256_bytes(str(value).encode("utf-8")), "bytes": len(str(value).encode("utf-8"))} for key, value in raw.items() if key not in safe}
                env_result["parsed"] = {"safe": safe, "redacted": sensitive}
                env_result.pop("stdout", None)
            except json.JSONDecodeError:
                pass
        observations["go_env"] = env_result
        module_results: list[dict[str, Any]] = []
        for module_root in module_roots:
            value = compact_tool_result(run_command(["go", "list", "-m", "-json"], module_root, timeout=30.0))
            if value.get("returncode") == 0:
                try:
                    parsed = json.loads(value.get("stdout") or "{}")
                    value["parsed"] = {key: parsed.get(key) for key in ["Path", "Main", "Dir", "GoMod", "GoVersion"]}
                    value.pop("stdout", None)
                except json.JSONDecodeError:
                    pass
            module_results.append({"root": relpath(module_root, root), "result": value})
        observations["modules"] = module_results
        result["tool_observations"] = observations
    payload = dict(result)
    payload.pop("digest", None)
    result["digest"] = sha256_bytes(canonical_bytes(payload))
    return result


def normalize_role(value: str | None) -> str:
    role = (value or "worker").strip().lower().replace("-", "_")
    aliases = {"workerdesigner": "worker_designer", "verificationdesigner": "verification_designer", "architect": "reviewer"}
    return aliases.get(role, role)


def load_work_unit(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    value = read_json(path)
    if not isinstance(value, dict):
        raise GoProfileError("work unit must be a JSON object")
    return value


def listify(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, (str, int, float))]
    return []


def git_changed_paths(root: Path) -> list[str]:
    if not shutil.which("git"):
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
    values: list[str] = []
    chunks = completed.stdout.split(b"\0")
    index = 0
    while index < len(chunks):
        chunk = chunks[index]
        index += 1
        if not chunk:
            continue
        text = chunk.decode("utf-8", "replace")
        status = text[:2]
        path = text[3:]
        if status and status[0] in {"R", "C"} and index < len(chunks):
            path = chunks[index].decode("utf-8", "replace")
            index += 1
        values.append(path)
    return sorted(set(values))


def collect_scope_paths(root: Path, explicit: Sequence[str], work_unit: dict[str, Any]) -> tuple[list[str], str]:
    candidates = list(explicit)
    source = "explicit"
    if not candidates:
        candidates = listify(work_unit.get("paths")) or listify(work_unit.get("scope"))
        source = "work-unit" if candidates else "git"
    if not candidates:
        candidates = git_changed_paths(root)
    normalized: list[str] = []
    for raw in candidates:
        path = Path(raw)
        if path.is_absolute():
            try:
                value = path.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                continue
        else:
            value = PurePosixPath(raw.replace("\\", "/")).as_posix().lstrip("./")
        if value and value not in normalized:
            normalized.append(value)
    return sorted(normalized), source


def path_glob_match(path: str, pattern: str) -> bool:
    value = path.replace("\\", "/")
    return fnmatch.fnmatch(value, pattern) or PurePosixPath(value).match(pattern)


def scan_excluded(rel: str, patterns: Sequence[str]) -> bool:
    value = rel.lstrip("./")
    for pattern in patterns:
        pattern = str(pattern).lstrip("./")
        if fnmatch.fnmatch(value, pattern):
            return True
        if pattern.endswith("/**"):
            base = pattern[:-3].rstrip("/")
            if value == base or value.startswith(base + "/"):
                return True
    return False


def expand_scan_files(root: Path, scope_paths: Sequence[str], cfg: dict[str, Any]) -> list[Path]:
    max_files = int(cfg.get("max_files", 5000))
    extensions = {str(item).lower() for item in cfg.get("source_extensions", [])}
    excludes = [str(item) for item in cfg.get("exclude_globs", [])]
    candidates: list[Path] = []
    roots: list[Path] = []
    if scope_paths:
        for raw in scope_paths:
            path = (root / raw).resolve()
            try:
                path.relative_to(root.resolve())
            except ValueError:
                continue
            if path.exists():
                roots.append(path)
    else:
        roots.append(root)
    for item in roots:
        if item.is_file():
            rel = relpath(item, root)
            if item.suffix.lower() in extensions and not scan_excluded(rel, excludes):
                candidates.append(item)
            continue
        for path in item.rglob("*"):
            if len(candidates) >= max_files:
                break
            if not path.is_file() or path.is_symlink():
                continue
            rel = relpath(path, root)
            if path.suffix.lower() not in extensions or scan_excluded(rel, excludes):
                continue
            candidates.append(path)
    return sorted(set(candidates), key=lambda item: relpath(item, root))[:max_files]


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
            observations.append({"id": trigger["id"], "reasons": reasons, "select": trigger.get("select", []), "gate_tags": trigger.get("gate_tags", [])})
    return observations, {"scope_paths": list(scope_paths), "scanned_files": [relpath(path, root) for path in files], "truncated": len(files) >= int(scan_cfg.get("max_files", 5000))}


def skill_catalog() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in PROFILE.get("skills", []):
        path = PROFILE_ROOT / item["path"]
        result[item["id"]] = {**item, "sha256": sha256_file(path), "bytes": path.stat().st_size}
    return result


def add_component(target: dict[str, dict[str, Any]], catalog: dict[str, dict[str, Any]], component_id: str, reason: str) -> None:
    if component_id not in catalog:
        raise GoProfileError(f"profile references unknown component: {component_id}")
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
    broad = any(item.get("id") == "broad-architecture" for item in trigger_observations)
    explicit_specific = any(
        item.get("id") != "broad-architecture" and any(reason.get("kind") in {"hint", "change-class", "path"} for reason in item.get("reasons", []))
        for item in trigger_observations
    )
    review_kinds = {"focused-review", "survey-review", "focused-assurance", "optional-stack-review"}
    for trigger in trigger_observations:
        if broad and not explicit_specific and trigger.get("id") != "broad-architecture":
            continue
        for component_id in trigger.get("select", []):
            item = catalog.get(component_id)
            if not item:
                continue
            reason = f"trigger {trigger['id']}"
            if role in {"worker", "worker_designer"} and item["kind"] in review_kinds:
                add_component(recommended, catalog, component_id, reason)
            else:
                add_component(selected, catalog, component_id, reason)
    return [selected[key] for key in sorted(selected)], [recommended[key] for key in sorted(recommended)]


def affected_scope(preflight_value: dict[str, Any], scope_paths: Sequence[str]) -> tuple[list[str], list[str], list[str]]:
    modules: set[str] = set()
    packages: set[str] = set()
    commands: set[str] = set()
    for module in preflight_value.get("modules", []):
        module_root = str(module.get("root") or "").rstrip("/")
        matched_module = not scope_paths
        for scope in scope_paths:
            if module_root in {"", "."} or scope == module_root or scope.startswith(module_root + "/"):
                matched_module = True
        if matched_module:
            modules.add(str(module.get("module_path")))
        for package in module.get("packages", []):
            pkg_dir = str(package.get("directory") or "").rstrip("/")
            full_dir = "/".join(part for part in [module_root, pkg_dir] if part not in {"", "."})
            if not scope_paths or any(full_dir in {"", "."} or scope == full_dir or scope.startswith(full_dir + "/") for scope in scope_paths):
                packages.add(str(package.get("import_path")))
                if package.get("main"):
                    commands.add(str(package.get("import_path")))
    if not packages:
        for module in preflight_value.get("modules", []):
            for package in module.get("packages", []):
                packages.add(str(package.get("import_path")))
    return sorted(modules), sorted(packages), sorted(commands)


def preferred_repo_command(preflight_value: dict[str, Any], gate_id: str) -> list[str] | None:
    recipes = preflight_value.get("repository_commands", {}).get("recipes", {})
    mapping = {
        "go-format-check": "format", "go-focused-tests": "test", "go-test-fresh-affected": "test",
        "go-compile-affected": "check", "go-vet-affected": "lint", "go-generate-diff": "generate",
        "go-race": "race", "go-fuzz": "fuzz", "go-coverage": "coverage", "go-vulncheck": "vuln",
        "go-supported-matrix": "matrix", "go-module-release": "package", "go-release-build": "release",
        "go-mutation": "mutation",
    }
    key = mapping.get(gate_id)
    value = recipes.get(key) if key else None
    return value if isinstance(value, list) else None


def compile_gate_plan(tier: str, observations: Sequence[dict[str, Any]], preflight_value: dict[str, Any], scope_paths: Sequence[str]) -> dict[str, Any]:
    gate_file = PROFILE_ROOT / PROFILE["gates"]
    definitions = read_json(gate_file)
    trigger_ids = {item["id"] for item in observations}
    tags = {str(tag) for item in observations for tag in item.get("gate_tags", [])}
    matched_inputs = {
        str(value)
        for item in observations
        for reason in item.get("reasons", [])
        if reason.get("kind") in {"hint", "change-class"}
        for value in reason.get("values", [])
    }
    hints = trigger_ids | tags | matched_inputs | {tier}
    modules, packages, commands = affected_scope(preflight_value, scope_paths)
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
        matched = recipe_triggers & hints
        if matched:
            applicable = True
            reasons.append("matched: " + ", ".join(sorted(matched)))
        if recipe["id"] == "go-build-commands" and commands and TIER_RANK[tier] >= TIER_RANK["material"]:
            applicable = True
            reasons.append("material-or-higher command work requires an actual linked build")
        if not applicable:
            skipped.append({"id": recipe["id"], "reason": "no applicable trigger"})
            continue
        preferred = preferred_repo_command(preflight_value, recipe["id"])
        selected.append({
            **recipe,
            "selection_reasons": reasons,
            "affected_modules": modules,
            "affected_packages": packages,
            "affected_commands": commands,
            "preferred_command": preferred or recipe.get("command"),
            "repository_override": preferred is not None,
            "execution": "planned-only",
        })
    payload = {
        "schema": "bbk.go-gate-plan.v1", "tier": tier,
        "affected_modules": modules, "affected_packages": packages, "affected_commands": commands,
        "trigger_ids": sorted(trigger_ids), "policy": definitions.get("policy", {}),
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


def make_lock(root: Path, preflight_value: dict[str, Any], selected: Sequence[dict[str, Any]], gate_plan: dict[str, Any], inputs: dict[str, Any], *, structure_projection: dict[str, Any] | None = None, slice_projection: dict[str, Any] | None = None) -> dict[str, Any]:
    profile_record = {
        "id": PROFILE["id"], "package": PROFILE.get("package"), "version": PROFILE["version"], "maturity": PROFILE["maturity"],
        "profile_manifest_sha256": sha256_file(PROFILE_ROOT / "PROFILE.json"), "package_root_sha256": profile_package_root_digest(),
        "preflight_sha256": preflight_value["digest"], "gate_plan_sha256": gate_plan["digest"],
        "selected_components": [{"id": item["id"], "kind": item["kind"], "sha256": item["sha256"]} for item in selected],
        "inputs": inputs,
        "implementation_structure": {
            "support": PROFILE.get("capabilities", {}).get("implementation_structure", {}).get("status", "legacy-unprojected"),
            "contract_sha256": inputs.get("structure_contract_sha256"),
            "projection_sha256": structure_projection.get("output_sha256") if structure_projection else None,
            "structure_projection_sha256": structure_projection.get("output_sha256") if structure_projection else None,
            "slice_sha256": inputs.get("execution_slice_sha256"),
            "slice_projection_sha256": slice_projection.get("output_sha256") if slice_projection else None,
        },
    }
    digest_payload = {"schema": "bbk.profile-lock-effective.v1", "project_root": str(root), "profiles": [profile_record]}
    effective = sha256_bytes(canonical_bytes(digest_payload))
    timestamp = os.environ.get("BBK_LOCK_TIMESTAMP") or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {"schema": "bbk.profile-lock.v1", "generated_at": timestamp, "project_root": str(root), "profiles": [profile_record], "effective_sha256": effective}


def resolve(args: argparse.Namespace) -> dict[str, Any]:
    root, _, _ = find_go_root(Path(args.root or Path.cwd()))
    work_unit = load_work_unit(Path(args.work_unit).expanduser().resolve() if args.work_unit else None)
    task_profile = args.task_profile or str(work_unit.get("task_profile") or "implementation")
    tier = args.assurance_tier or str(work_unit.get("assurance_tier") or work_unit.get("risk_tier") or "routine")
    if tier not in TIER_RANK:
        raise GoProfileError(f"unsupported assurance tier: {tier}")
    role = normalize_role(args.role or str(work_unit.get("role") or "worker"))
    hints = sorted(set(list(args.hint or []) + listify(work_unit.get("profile_hints")) + listify(work_unit.get("hints"))))
    change_classes = sorted(set(list(args.change_class or []) + listify(work_unit.get("change_classes"))))
    scope_paths, scope_source = collect_scope_paths(root, args.path or [], work_unit)
    structure_projection = None
    slice_projection = None
    structure_digest = None
    slice_digest = None
    if getattr(args, "contract", None):
        contract, structure_digest = load_validated(Path(args.contract).expanduser().resolve(), "bbk-implementation-structure-contract-v1.schema.json")
        hints = sorted(set(hints + ["implementation-structure", *listify(contract.get("applicability", {}).get("triggers"))]))
        if not args.task_profile:
            task_profile = "implementation-structure"
        structure_projection = project_structure(contract, structure_digest, root=root, role=role, task_profile=task_profile, tier=tier, run_tools=bool(args.run_tools))
    if getattr(args, "slice", None):
        slice_value, slice_digest = load_validated(Path(args.slice).expanduser().resolve(), "bbk-execution-slice-v1.schema.json")
        hints = sorted(set(hints + ["execution-slicing"]))
        if not args.task_profile:
            task_profile = "execution-slicing"
        slice_projection = project_slice(slice_value, slice_digest, root=root, role=role, task_profile=task_profile, tier=tier, run_tools=bool(args.run_tools))
    preflight_value = preflight(root, run_tools=bool(args.run_tools))
    observations, scan = detect_triggers(root, scope_paths, hints, change_classes)
    selected, recommended = select_components(role, task_profile, observations)
    gate_plan = compile_gate_plan(tier, observations, preflight_value, scope_paths)
    inputs = {
        "role": role, "task_profile": task_profile, "assurance_tier": tier,
        "hints": hints, "change_classes": change_classes, "scope_paths": scope_paths,
        "scope_source": scope_source, "run_tools": bool(args.run_tools),
        "work_unit_sha256": sha256_file(Path(args.work_unit).expanduser().resolve()) if args.work_unit else None,
        "structure_contract_sha256": structure_digest,
        "execution_slice_sha256": slice_digest,
    }
    lock = make_lock(root, preflight_value, selected, gate_plan, inputs, structure_projection=structure_projection, slice_projection=slice_projection)
    return {
        "schema": "bbk.go-profile-resolution.v1",
        "profile": {"id": PROFILE["id"], "package": PROFILE.get("package"), "version": PROFILE["version"], "maturity": PROFILE["maturity"]},
        "inputs": inputs,
        "observations": {"triggers": observations, "scan": scan, "preflight_digest": preflight_value["digest"]},
        "preflight": preflight_value,
        "selected_components": selected,
        "recommended_validator_packs": recommended,
        "gate_plan": gate_plan,
        "implementation_structure": {
            "support": PROFILE.get("capabilities", {}).get("implementation_structure", {}).get("status", "legacy-unprojected"),
            "structure_projection": structure_projection,
            "slice_projection": slice_projection,
        },
        "lock": lock,
        "effective_sha256": lock["effective_sha256"],
        "limitations": [
            "Profile selection and projection do not grant tool, network, credential, filesystem, publication, or execution authority.",
            "Planned gates are not executed by resolution.",
            "A Go projection is a view over the generic contract or slice, not a second source of truth.",
            "Race, fuzz, coverage, vulnerability, sanitizer, and static-analysis evidence is bounded by the exact configuration exercised.",
            "Partial or unqualified support domains require separate project qualification.",
        ],
    }


def gate_plan_command(args: argparse.Namespace) -> dict[str, Any]:
    return resolve(args)["gate_plan"]


def format_files(root: Path, explicit: Sequence[str]) -> list[Path]:
    values: list[Path] = []
    if explicit:
        candidates = [(root / raw).resolve() for raw in explicit]
    else:
        candidates = [root]
    for candidate in candidates:
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            continue
        if candidate.is_file() and candidate.suffix == ".go":
            values.append(candidate)
        elif candidate.is_dir():
            for path in candidate.rglob("*.go"):
                if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
                    continue
                values.append(path)
    return sorted(set(values), key=lambda item: relpath(item, root))


def check_format(args: argparse.Namespace) -> dict[str, Any]:
    root, _, _ = find_go_root(Path(args.root or Path.cwd()))
    files = format_files(root, args.path or [])
    if not shutil.which("gofmt"):
        return {"schema": "bbk.go-format-check.v1", "status": "BLOCKED", "root": str(root), "reason": "gofmt not found", "files": []}
    unformatted: list[str] = []
    errors: list[dict[str, Any]] = []
    for index in range(0, len(files), 200):
        chunk = files[index:index + 200]
        result = run_command(["gofmt", "-l", *[str(path) for path in chunk]], root, timeout=60)
        if result["returncode"] != 0:
            errors.append(result)
            continue
        for line in result.get("stdout", "").splitlines():
            path = Path(line)
            unformatted.append(relpath(path, root) if path.is_absolute() else line)
    status = "ERROR" if errors else ("FAIL" if unformatted else "PASS")
    return {"schema": "bbk.go-format-check.v1", "status": status, "root": str(root), "checked_files": len(files), "unformatted": sorted(set(unformatted)), "errors": errors}


# --- BBK alpha.4 implementation-structure and execution-slice support ---
BBK_TARGET_VERSION = "0.1.0-alpha.4"
NO_AUTHORITY_BOUNDARY = {
    "may_declare_pass": False,
    "may_expand_work_scope": False,
    "may_grant_tools_or_effects": False,
    "may_reduce_assurance": False,
    "statement": "This profile projects, reviews, and plans evidence only. It does not mutate generic BBK objects, grant authority or effects, broaden scope, reduce assurance, or declare acceptance.",
}


def output_digest(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result.pop("output_sha256", None)
    result["output_sha256"] = sha256_bytes(canonical_bytes(result))
    return result


def schema_errors(value: Any, schema: dict[str, Any], path: str = "$", root_schema: dict[str, Any] | None = None) -> list[str]:
    root_schema = root_schema or schema
    errors: list[str] = []
    if "$ref" in schema:
        ref = str(schema["$ref"])
        if not ref.startswith("#/"):
            return [f"{path}: unsupported schema reference {ref!r}"]
        target: Any = root_schema
        for part in ref[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(target, dict) or part not in target:
                return [f"{path}: unresolved schema reference {ref!r}"]
            target = target[part]
        return schema_errors(value, target, path, root_schema)
    if "oneOf" in schema:
        variants = [schema_errors(value, item, path, root_schema) for item in schema["oneOf"]]
        if not any(not item for item in variants):
            errors.append(f"{path}: does not satisfy any allowed schema")
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']!r}")
    expected = schema.get("type")
    expected_types = expected if isinstance(expected, list) else [expected] if expected else []
    if expected_types:
        valid_type = any(
            (item == "object" and isinstance(value, dict))
            or (item == "array" and isinstance(value, list))
            or (item == "string" and isinstance(value, str))
            or (item == "boolean" and isinstance(value, bool))
            or (item == "integer" and isinstance(value, int) and not isinstance(value, bool))
            or (item == "number" and isinstance(value, (int, float)) and not isinstance(value, bool))
            or (item == "null" and value is None)
            for item in expected_types
        )
        if not valid_type:
            errors.append(f"{path}: expected type {expected_types!r}")
            return errors
    if isinstance(value, str):
        if "minLength" in schema and len(value) < int(schema["minLength"]):
            errors.append(f"{path}: string is shorter than {schema['minLength']}")
        if "pattern" in schema and re.fullmatch(str(schema["pattern"]), value) is None:
            errors.append(f"{path}: string does not match {schema['pattern']!r}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < int(schema["minItems"]):
            errors.append(f"{path}: array has fewer than {schema['minItems']} items")
        if isinstance(schema.get("items"), dict):
            for index, item in enumerate(value):
                errors.extend(schema_errors(item, schema["items"], f"{path}[{index}]", root_schema))
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")
        for key, child in schema.get("properties", {}).items():
            if key in value:
                errors.extend(schema_errors(value[key], child, f"{path}.{key}", root_schema))
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}))
            for key in value:
                if key not in allowed:
                    errors.append(f"{path}: unexpected property {key!r}")
    return errors


def load_validated(path: Path, schema_name: str) -> tuple[dict[str, Any], str]:
    value = read_json(path)
    if not isinstance(value, dict):
        raise GoProfileError(f"expected a JSON object in {path}")
    schema = read_json(PROFILE_ROOT / "schemas" / schema_name)
    errors = schema_errors(value, schema)
    if errors:
        raise GoProfileError(f"schema validation failed for {path}:\n- " + "\n- ".join(errors[:50]))
    return value, sha256_file(path)


def maybe_preflight(root: Path, *, run_tools: bool = False) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        return preflight(root, run_tools=run_tools), []
    except GoProfileError as exc:
        return None, [{"code": "GO_ROOT_UNAVAILABLE", "message": str(exc)}]


def requested_tool_blockers(preflight_value: dict[str, Any] | None, run_tools: bool) -> list[dict[str, Any]]:
    if not run_tools or preflight_value is None:
        return []
    go_version = preflight_value.get("tool_observations", {}).get("go_version", {})
    if go_version.get("returncode") not in {0, None}:
        return [{"code": "REQUIRED_GO_TOOL_UNAVAILABLE", "message": "The invocation explicitly requested Go tool interrogation, but the local go command was unavailable or failed.", "observation": go_version}]
    return []


def input_record(kind: str, object_id: str, revision: str | None, digest: str) -> dict[str, Any]:
    return {"kind": kind, "id": object_id, "revision": revision, "sha256": digest}


def structure_subject_support(contract: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    kind = str(contract.get("subject", {}).get("kind") or "other")
    if kind == "software":
        return "SUPPORTED", []
    if kind == "mixed":
        return "PARTIAL", [{"code": "MIXED_SUBJECT", "message": "The Go profile projects only the Go/software portion; adjacent procedural, hardware, data, or operational obligations remain outside this profile."}]
    return "UNSUPPORTED", [{"code": "NON_GO_SUBJECT", "message": f"Subject kind {kind!r} is not a Go/software realization. Use the generic BBK object or a matching domain profile."}]


def go_artifact_kind(item: dict[str, Any]) -> str:
    generic = str(item.get("kind") or "artifact").lower()
    path = str(item.get("logicalPath") or item.get("path") or "").lower()
    responsibility = str(item.get("responsibility") or "").lower()
    if path.endswith("go.work") or "workspace" in generic:
        return "go-workspace"
    if path.endswith("go.mod") or generic in {"module", "distribution"} and "module" in responsibility:
        return "go-module"
    if path.endswith("_test.go") or generic == "test":
        return "go-test-package"
    if "generated" in generic or "generated" in responsibility:
        return "go-generated-artifact"
    if "cgo" in generic or "ffi" in generic or "native" in generic or path.endswith((".s", ".c", ".h")):
        return "go-native-boundary"
    if generic in {"command", "cli", "binary"} or "/cmd/" in f"/{path}":
        return "go-command"
    if generic in {"package", "module", "adapter", "service", "component"}:
        return "go-package"
    if path.endswith(".go"):
        return "go-source-file"
    return "go-artifact"


def go_contract_kind(item: dict[str, Any]) -> str:
    text = " ".join(str(item.get(key) or "") for key in ["kind", "name", "responsibility", "shape"]).lower()
    if "interface" in text:
        return "consumer-interface"
    if "request" in text or "command" in text or "query" in text:
        return "request-struct"
    if "result" in text or "response" in text:
        return "result-struct"
    if "error" in text or "failure" in text:
        return "typed-error"
    if any(word in text for word in ["json", "wire", "schema", "protobuf", "grpc", "http"]):
        return "wire-schema"
    if "channel" in text:
        return "channel-protocol"
    if "context" in text or "cancel" in text:
        return "context-cancellation"
    return "exported-api" if str(item.get("visibility") or "").lower() in {"public", "shared", "exported"} else "package-contract"


def type_guidance(contract: dict[str, Any]) -> dict[str, Any]:
    contracts = contract.get("structure", {}).get("keyContracts", [])
    fixed_text = " ".join(str(item.get("statement") or "") for item in contract.get("decisions", {}).get("fixed", [])).lower()
    guidance = {
        "identity_types": [
            "Use a defined Go type for materially distinct identities, units, states, or names that must not be interchanged accidentally.",
            "Keep wire text conversion at the adapter boundary; do not let arbitrary strings remain authoritative after parsing.",
        ],
        "state_types": [
            "Use an explicit struct plus typed constants for closed state where Go has no native algebraic data type; make invalid zero values either useful by design or rejected by constructors/validation.",
            "Keep transition authority in the owning package and test illegal or stale transitions at runtime.",
        ],
        "boundary_types": [
            "Use explicit request/result structs, stable error contracts, and consumer-defined interfaces only at real substitution or test seams.",
            "Treat static Go types as compile-time structure, not runtime validation of untrusted JSON, HTTP, database, or message data.",
        ],
        "ownership_types": [
            "Represent package ownership and mutation authority in API shape and documentation; name the owner of every goroutine, channel close, timer, ticker, pool, lock, and shutdown path.",
            "Use context parameters for request-scoped cancellation and deadlines; do not hide lifecycle context in long-lived fields without a documented owner.",
        ],
        "failure_types": [
            "Use sentinel or typed errors only when callers need stable classification; preserve identity intentionally with errors.Is/errors.As and wrapping.",
            "Distinguish absence, rejection, cancellation, timeout, partial completion, retryable failure, stale state, and degraded operation where callers act differently.",
        ],
        "evidence_types": [
            "Keep NOT_RUN, BLOCKED, ERROR, INCONCLUSIVE, PASS, FAIL, FLAKY, and NOT_APPLICABLE distinct in test and validation evidence.",
        ],
        "static_limits": [
            "Go types cannot prove goroutine termination, race freedom, protocol ordering, persistence durability, cgo pointer lifetime, runtime schema validity, or operational recovery; use targeted runtime and tool evidence.",
        ],
    }
    if "zero" in fixed_text:
        guidance["state_types"].append("The contract explicitly constrains zero-value behavior; preserve and test that decision.")
    if contracts:
        guidance["projected_contracts"] = [{"id": item.get("id"), "name": item.get("name"), "go_kind": go_contract_kind(item)} for item in contracts]
    return guidance


def project_structure(contract: dict[str, Any], contract_digest: str, *, root: Path, role: str, task_profile: str, tier: str, run_tools: bool = False) -> dict[str, Any]:
    applicability = contract.get("applicability", {})
    level = str(applicability.get("level") or "none")
    support, unsupported = structure_subject_support(contract)
    preflight_value, preflight_notes = maybe_preflight(root, run_tools=run_tools)
    advisories: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = requested_tool_blockers(preflight_value, run_tools)
    unsupported.extend(preflight_notes)
    if level == "none":
        disposition = "NOT_APPLICABLE"
    elif support == "UNSUPPORTED":
        disposition = "UNSUPPORTED"
    elif support == "PARTIAL":
        disposition = "PARTIAL"
    else:
        disposition = "SUPPORTED"
    structure = contract.get("structure", {})
    artifacts = []
    for item in structure.get("artifactTopology", []):
        if not isinstance(item, dict):
            continue
        artifacts.append({
            "id": item.get("id"), "go_kind": go_artifact_kind(item), "generic_kind": item.get("kind"),
            "logical_path": item.get("logicalPath"), "action": item.get("action"), "owner": item.get("owner"),
            "responsibility": item.get("responsibility"), "source_refs": item.get("sourceRefs", []),
            "conformance": "fixed only when referenced by a fixed decision or public/shared contract; otherwise private placement may vary",
        })
    contracts = []
    for item in structure.get("keyContracts", []):
        if not isinstance(item, dict):
            continue
        contracts.append({
            "id": item.get("id"), "name": item.get("name"), "go_kind": go_contract_kind(item),
            "generic_kind": item.get("kind"), "visibility": item.get("visibility"), "shape": item.get("shape"),
            "responsibility": item.get("responsibility"), "invariants": item.get("invariants", []),
            "failure_semantics": item.get("failureSemantics", []), "source_refs": item.get("sourceRefs", []),
            "runtime_validation_required": any(token in " ".join(map(str, item.values())).lower() for token in ["json", "wire", "http", "database", "external", "untrusted"]),
        })
    ownership = []
    for item in structure.get("stateOwnership", []):
        if not isinstance(item, dict):
            continue
        ownership.append({
            "state": item.get("state"), "owner": item.get("owner"), "lifetime": item.get("lifetime"),
            "mutation_authority": item.get("mutationAuthority"), "concurrency": item.get("concurrency"),
            "consistency": item.get("consistency"), "recovery": item.get("recovery"),
            "go_review": ["package ownership", "goroutine lifecycle", "channel close ownership", "context cancellation", "lock/atomic invariants", "zero-value and nil behavior"],
        })
    behavior_paths = []
    for item in structure.get("behaviorPaths", []):
        if not isinstance(item, dict):
            continue
        behavior_paths.append({
            "id": item.get("id"), "name": item.get("name"), "trigger": item.get("trigger"), "success": item.get("success"),
            "steps": item.get("steps", []), "failure_and_recovery": item.get("failureAndRecovery", []),
            "interface_refs": item.get("interfaceRefs", []),
            "go_review": ["context propagation", "error classification", "partial result behavior", "goroutine/channel cleanup", "retry/idempotency", "observability"],
        })
    projected = {
        "subject": contract.get("subject", {}),
        "go_topology": {
            "artifacts": artifacts,
            "contracts": contracts,
            "packages_from_preflight": [item.get("packages", []) for item in (preflight_value or {}).get("modules", [])],
            "commands_from_preflight": [item.get("command_packages", []) for item in (preflight_value or {}).get("modules", [])],
        },
        "type_driven_development": type_guidance(contract),
        "behavior_paths": behavior_paths,
        "state_and_lifecycle_ownership": ownership,
        "effect_boundaries": structure.get("effectBoundaries", []),
        "test_seams": structure.get("testSeams", []),
        "observability_points": structure.get("observabilityPoints", []),
        "migration_touchpoints": structure.get("migrationTouchpoints", []),
        "fixed_decisions": contract.get("decisions", {}).get("fixed", []),
        "delegated_freedom": contract.get("decisions", {}).get("delegated", []),
        "prohibited_shortcuts": contract.get("decisions", {}).get("prohibited", []),
        "acceptance_criteria": contract.get("review", {}).get("acceptanceCriteria", []),
    }
    trigger_set = set(str(item) for item in applicability.get("triggers", []))
    material_triggers = trigger_set & {"public-interface", "public-api", "shared-contract", "cross-module", "state-ownership", "concurrency", "cancellation", "recovery", "migration", "persistence", "multi-module", "cgo", "unsafe", "release"}
    review_required = level == "contract" and (TIER_RANK.get(tier, 0) >= TIER_RANK["material"] or bool(material_triggers))
    if level == "inline":
        advisories.append({"code": "INLINE_STRUCTURE", "message": "Carry the compact Go projection in the work unit; a standalone focused reviewer is not selected unless another material trigger requires it."})
    if level == "contract" and contract.get("status") not in {"accepted", "in-review"}:
        blockers.append({"code": "CONTRACT_NOT_ACCEPTED", "message": "A contract-level structure cannot govern independent implementation until its review/acceptance state is resolved."})
    payload = {
        "schema": "bbk.go.implementation-structure-projection.v1",
        "profile": {"id": "go", "version": VERSION},
        "bbk_version": BBK_TARGET_VERSION,
        "input": input_record("ImplementationStructureContract", str(contract.get("contractId")), str(contract.get("revision")), contract_digest),
        "preflight_sha256": preflight_value.get("digest") if preflight_value else None,
        "role": role,
        "task_profile": task_profile,
        "assurance_tier": tier,
        "applicability": {"level": level, "disposition": disposition, "rationale": str(applicability.get("rationale") or ""), "triggers": list(applicability.get("triggers", []))},
        "projection": projected if disposition in {"SUPPORTED", "PARTIAL"} else {},
        "review_selection": {"selected": review_required, "skill": "go-implementation-structure-review" if review_required else None, "reason": "contract-level consequential Go shape" if review_required else "ordinary or inline treatment"},
        "unsupported_or_uncertain": unsupported + list(contract.get("uncertainties", [])),
        "advisories": advisories,
        "blockers": blockers,
        "authority_boundary": dict(NO_AUTHORITY_BOUNDARY),
    }
    return output_digest(payload)


def foundation_assessment(slice_value: dict[str, Any], tier: str) -> dict[str, Any]:
    text = " ".join([str(slice_value.get("title") or ""), str(slice_value.get("objective") or ""), " ".join(map(str, slice_value.get("flow", {}).get("steps", [])))]).lower()
    markers = [item for item in ["foundation", "infrastructure", "framework", "scaffolding", "base layer", "platform setup", "only types", "only schema"] if item in text]
    touchpoint = slice_value.get("touchpoint", {})
    expected = str(touchpoint.get("expectedObservation") or "").strip()
    exception = slice_value.get("metadata", {}).get("foundationException") if isinstance(slice_value.get("metadata"), dict) else None
    horizontal = bool(markers) and str(touchpoint.get("kind")) in {"other", "document", "report"}
    allowed = False
    reasons: list[str] = []
    if horizontal and isinstance(exception, dict):
        required = ["risk", "ownTouchpoint", "enablesNext"]
        allowed = all(str(exception.get(key) or "").strip() for key in required)
        if allowed:
            reasons.append("documented foundation exception retires a named risk and enables an integrated next slice")
    if not horizontal:
        reasons.append("slice exposes a domain-relevant touchpoint rather than an obviously layer-only increment")
    if not expected:
        reasons.append("expected observation is missing")
    status = "ACCEPTABLE" if (not horizontal or allowed) and bool(expected) else ("ADVISORY" if TIER_RANK.get(tier, 0) < 2 else "BLOCKING")
    return {"status": status, "horizontal_markers": markers, "foundation_exception": exception, "allowed_exception": allowed, "reasons": reasons}


def go_touchpoint_projection(touchpoint: dict[str, Any]) -> dict[str, Any]:
    kind = str(touchpoint.get("kind") or "other")
    mapping = {
        "cli": "go-command",
        "api": "package-api-or-downstream-consumer",
        "ui": "http-handler-template-or-browser-boundary",
        "report": "generated-report",
        "procedure": "mixed-procedure-with-go-support",
        "simulation": "simulator-or-fixture-run",
        "physical-observation": "adjacent-physical-observation",
        "document": "reviewable-design-or-release-document",
        "package": "module-release-or-binary-archive",
        "protocol-trace": "http-rpc-message-or-cgo-trace",
        "other": "explicit-project-touchpoint",
    }
    return {"generic_kind": kind, "go_kind": mapping.get(kind, "explicit-project-touchpoint"), **{key: touchpoint.get(key) for key in ["actor", "interaction", "expectedObservation", "environment"]}}


def project_slice(slice_value: dict[str, Any], slice_digest: str, *, root: Path, role: str, task_profile: str, tier: str, run_tools: bool = False) -> dict[str, Any]:
    preflight_value, preflight_notes = maybe_preflight(root, run_tools=run_tools)
    foundation = foundation_assessment(slice_value, tier)
    advisories: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = requested_tool_blockers(preflight_value, run_tools)
    if foundation["status"] == "BLOCKING":
        blockers.append({"code": "HORIZONTAL_SLICE_WITHOUT_EXCEPTION", "message": "The slice appears layer-only and lacks a complete foundation exception with its own touchpoint and named next integrated slice."})
    elif foundation["status"] == "ADVISORY":
        advisories.append({"code": "FOUNDATION_SLICE_REVIEW", "message": "Confirm that this foundation slice has a meaningful technical touchpoint and immediately enables an integrated slice."})
    atomicity = slice_value.get("atomicity", {})
    for key in ["coherent", "reviewable", "independentlyVerifiable", "containedOrReversible"]:
        if atomicity.get(key) is not True:
            blockers.append({"code": "SLICE_ATOMICITY_GAP", "field": key, "message": f"ExecutionSlice must positively establish {key}."})
    scaffolding_risks = []
    for item in slice_value.get("scaffolding", []):
        if not isinstance(item, dict):
            continue
        disposition = str(item.get("disposition") or "").strip()
        risk = {"id": item.get("id"), "purpose": item.get("purpose"), "owner": item.get("owner"), "disposition": disposition, "risk": None}
        if not disposition:
            risk["risk"] = "missing disposition"
            blockers.append({"code": "SCAFFOLDING_DISPOSITION_MISSING", "ref": item.get("id"), "message": "Temporary scaffolding must be removed, retained as a named fixture, or assigned to an explicit successor."})
        elif disposition.lower() in {"retain", "keep", "permanent"}:
            risk["risk"] = "ambiguous permanent promotion"
            advisories.append({"code": "SCAFFOLDING_PROMOTION_AMBIGUOUS", "ref": item.get("id"), "message": "Use an explicit production-review or retain-as-fixture disposition rather than silently promoting scaffolding."})
        scaffolding_risks.append(risk)
    assertions = []
    for item in slice_value.get("assertions", []):
        if not isinstance(item, dict):
            continue
        method = str(item.get("method") or "inspection")
        go_method = {
            "test": "go test or repository-equivalent targeted test",
            "analysis": "static/source/module analysis",
            "inspection": "manifest/source/generated-artifact inspection",
            "demonstration": "run the declared command/API/package touchpoint",
            "operational-validation": "qualified runtime or deployment observation",
            "review": "focused assertion-scoped review",
        }.get(method, method)
        assertions.append({**item, "go_method": go_method, "candidate_bound": True})
    modules = [item.get("module_path") for item in (preflight_value or {}).get("modules", [])]
    packages = [pkg.get("import_path") for module in (preflight_value or {}).get("modules", []) for pkg in module.get("packages", [])]
    commands = [cmd for module in (preflight_value or {}).get("modules", []) for cmd in module.get("command_packages", [])]
    projection = {
        "touchpoint": go_touchpoint_projection(slice_value.get("touchpoint", {})),
        "dependency_closure": {
            "slice_dependencies": slice_value.get("dependencies", []),
            "structure_contract_refs": slice_value.get("structureContractRefs", []),
            "work_unit_refs": slice_value.get("workUnitRefs", []),
            "interface_refs": slice_value.get("flow", {}).get("interfaceRefs", []),
            "participants": slice_value.get("flow", {}).get("participants", []),
            "observed_modules": modules,
            "observed_packages": packages,
            "observed_commands": commands,
        },
        "flow": slice_value.get("flow", {}),
        "integration_owner": slice_value.get("integrationOwner"),
        "assertion_evidence": assertions,
        "entry_conditions": slice_value.get("entryConditions", []),
        "exit_conditions": slice_value.get("exitConditions", []),
        "candidate_boundary": "one exact candidate or tightly coupled cohort that contains every work unit necessary for the touchpoint",
        "validation_boundary": "assertion-scoped evidence for this slice; do not merge unrelated reviewer charters",
        "scaffolding": scaffolding_risks,
        "go_specific_checks": [
            "the touchpoint uses the declared module/workspace, build tags, GOOS/GOARCH, CGO, and toolchain configuration",
            "goroutines, channels, contexts, timers, processes, files, and network resources created by the slice have explicit owners and cleanup",
            "public declarations, error contracts, wire forms, generated code, and downstream consumers affected by the slice are included in evidence",
        ],
    }
    payload = {
        "schema": "bbk.go.execution-slice-projection.v1",
        "profile": {"id": "go", "version": VERSION},
        "bbk_version": BBK_TARGET_VERSION,
        "input": input_record("ExecutionSlice", str(slice_value.get("sliceId")), str(slice_value.get("metadata", {}).get("revision") or slice_value.get("status")), slice_digest),
        "preflight_sha256": preflight_value.get("digest") if preflight_value else None,
        "role": role,
        "task_profile": task_profile,
        "assurance_tier": tier,
        "applicability": {"level": "contract" if slice_value.get("structureContractRefs") else "inline", "disposition": "SUPPORTED" if preflight_value else "PARTIAL", "rationale": "ExecutionSlice explicitly requests a Go projection.", "triggers": ["execution-slicing"]},
        "projection": projection,
        "foundation_assessment": foundation,
        "unsupported_or_uncertain": preflight_notes,
        "advisories": advisories,
        "blockers": blockers,
        "authority_boundary": dict(NO_AUTHORITY_BOUNDARY),
    }
    return output_digest(payload)


def exported_declarations(text: str, path: str, package: str) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    patterns = [
        ("type", re.compile(r"(?m)^type\s+([A-Z][A-Za-z0-9_]*)\s+([^\n{]+|struct\s*\{|interface\s*\{)")),
        ("function", re.compile(r"(?m)^func\s+([A-Z][A-Za-z0-9_]*)\s*\(")),
        ("method", re.compile(r"(?m)^func\s*\([^)]*\)\s*([A-Z][A-Za-z0-9_]*)\s*\(")),
        ("var", re.compile(r"(?m)^var\s+([A-Z][A-Za-z0-9_]*)\b")),
        ("const", re.compile(r"(?m)^const\s+([A-Z][A-Za-z0-9_]*)\b")),
    ]
    for kind, pattern in patterns:
        for match in pattern.finditer(text):
            values.append({"kind": kind, "name": match.group(1), "package": package, "path": path, "visibility": "exported"})
    for match in re.finditer(r"(?m)^var\s+(Err[A-Z][A-Za-z0-9_]*)\s*=", text):
        values.append({"kind": "sentinel-error", "name": match.group(1), "package": package, "path": path, "visibility": "exported"})
    return values


def build_actual_inventory(root: Path, *, run_tools: bool = False) -> dict[str, Any]:
    preflight_value, notes = maybe_preflight(root, run_tools=run_tools)
    if preflight_value is None:
        payload = {"schema": "bbk.go.actual-structure-inventory.v1", "root": str(root.resolve()), "preflight_sha256": None, "artifacts": [], "contracts": [], "ownership": [], "behavior_paths": [], "fixed_decisions": [], "delegated_differences": [], "unsupported_or_uncertain": notes}
        return output_digest(payload)
    artifacts: list[dict[str, Any]] = []
    contracts: list[dict[str, Any]] = []
    ownership: list[dict[str, Any]] = []
    behavior: list[dict[str, Any]] = []
    work = preflight_value.get("workspace", {}).get("go_work")
    if work:
        artifacts.append({"kind": "go-workspace", "path": work.get("path"), "sha256": work.get("sha256")})
    for module in preflight_value.get("modules", []):
        artifacts.append({"kind": "go-module", "path": module.get("go_mod", {}).get("path"), "module_path": module.get("module_path"), "sha256": module.get("go_mod", {}).get("sha256")})
        module_root = root / str(module.get("root") or ".")
        for package in module.get("packages", []):
            artifacts.append({"kind": "go-command" if package.get("main") else "go-package", "path": "/".join(part for part in [str(module.get("root") or "").strip("/"), str(package.get("directory") or "").strip("/")] if part and part != "."), "import_path": package.get("import_path"), "internal": package.get("internal")})
        for path in iter_source_files(module_root):
            if path.suffix != ".go":
                continue
            rel = relpath(path, root)
            text = path.read_text(encoding="utf-8", errors="replace") if path.stat().st_size <= 1024 * 1024 else ""
            pkg = package_name(text) or "<unknown>"
            generated = bool(re.search(r"(?m)^// Code generated .* DO NOT EDIT\.?$", text))
            artifacts.append({"kind": "go-generated-artifact" if generated else ("go-test-file" if path.name.endswith("_test.go") else "go-source-file"), "path": rel, "sha256": sha256_file(path), "package": pkg})
            contracts.extend(exported_declarations(text, rel, pkg))
            if re.search(r"\bgo\s+[A-Za-z_(]", text):
                ownership.append({"kind": "goroutine", "path": rel, "status": "requires-owner-review"})
            if re.search(r"\bchan\b|make\s*\(\s*chan\b", text):
                ownership.append({"kind": "channel", "path": rel, "status": "requires-close-and-backpressure-review"})
            if "context.Context" in text:
                ownership.append({"kind": "context", "path": rel, "status": "requires-cancellation-owner-review"})
            if re.search(r"sync\.(Mutex|RWMutex|Once|Cond|WaitGroup)|atomic\.", text):
                ownership.append({"kind": "synchronization", "path": rel, "status": "requires-invariant-and-copy-review"})
            for match in re.finditer(r"(?m)^func\s+(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\(", text):
                behavior.append({"kind": "function-or-method", "name": match.group(1), "path": rel})
    payload = {"schema": "bbk.go.actual-structure-inventory.v1", "root": str(root.resolve()), "preflight_sha256": preflight_value.get("digest"), "artifacts": artifacts, "contracts": contracts, "ownership": ownership, "behavior_paths": behavior, "fixed_decisions": [], "delegated_differences": [], "unsupported_or_uncertain": notes}
    return output_digest(payload)


def normalize_actual_inventory(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result.pop("output_sha256", None)
    return output_digest(result)


def compare_structure(contract: dict[str, Any], contract_digest: str, actual: dict[str, Any], *, tier: str) -> dict[str, Any]:
    actual = normalize_actual_inventory(actual)
    artifacts_by_path = {str(item.get("path") or item.get("logical_path") or "").replace("\\", "/"): item for item in actual.get("artifacts", []) if isinstance(item, dict)}
    contracts_by_name = {str(item.get("name") or ""): item for item in actual.get("contracts", []) if isinstance(item, dict)}
    fixed_by_id = {str(item.get("id") or ""): item for item in actual.get("fixed_decisions", []) if isinstance(item, dict)}
    differences: list[dict[str, Any]] = []
    for planned in contract.get("structure", {}).get("artifactTopology", []):
        if not isinstance(planned, dict):
            continue
        path = str(planned.get("logicalPath") or "").replace("\\", "/")
        if path and path not in artifacts_by_path:
            material = str(planned.get("kind") or "").lower() in {"module", "adapter", "command", "public-api", "generated-artifact"} or "public" in str(planned.get("responsibility") or "").lower()
            differences.append({"class": "material" if material else "advisory", "kind": "planned-artifact-missing", "planned_ref": planned.get("id"), "path": path, "message": "Planned artifact was not observed in the actual inventory."})
    for planned in contract.get("structure", {}).get("keyContracts", []):
        if not isinstance(planned, dict):
            continue
        name = str(planned.get("name") or "")
        visibility = str(planned.get("visibility") or "").lower()
        if name and name not in contracts_by_name:
            material = visibility in {"public", "shared", "exported"}
            differences.append({"class": "material" if material else "unknown", "kind": "planned-contract-not-observed", "planned_ref": planned.get("id"), "name": name, "message": "Planned contract was not observed by name; generated or dynamic declarations may require tool or human evidence."})
    for fixed in contract.get("decisions", {}).get("fixed", []):
        if not isinstance(fixed, dict):
            continue
        ref = str(fixed.get("id") or "")
        evidence = fixed_by_id.get(ref)
        if evidence is None:
            differences.append({"class": "unknown", "kind": "fixed-decision-evidence-missing", "planned_ref": ref, "message": "No actual-inventory evidence was supplied for this fixed decision."})
        else:
            status = str(evidence.get("status") or "unknown").lower()
            if status in {"violated", "diverged", "fail", "failed"}:
                differences.append({"class": "material", "kind": "fixed-decision-divergence", "planned_ref": ref, "evidence": evidence.get("evidence"), "message": evidence.get("message") or "Actual realization violates a fixed decision."})
            elif status not in {"satisfied", "conforms", "pass", "passed"}:
                differences.append({"class": "unknown", "kind": "fixed-decision-unknown", "planned_ref": ref, "evidence": evidence.get("evidence"), "message": evidence.get("message") or "Fixed decision conformance is unknown."})
    for item in actual.get("delegated_differences", []):
        if not isinstance(item, dict):
            continue
        if item.get("independent_quality_finding"):
            differences.append({"class": "advisory", "kind": "delegated-quality-finding", "message": item.get("message"), "evidence": item})
        else:
            differences.append({"class": "within-delegated-freedom", "kind": "delegated-difference", "message": item.get("message"), "evidence": item})
    counts = {key: sum(1 for item in differences if item["class"] == key) for key in ["material", "advisory", "unknown", "within-delegated-freedom"]}
    if counts["material"]:
        disposition = "MATERIAL_DIVERGENCE"
    elif counts["unknown"] and TIER_RANK.get(tier, 0) >= TIER_RANK["consequential"]:
        disposition = "BLOCKED"
    elif counts["advisory"] or counts["unknown"]:
        disposition = "ADVISORY_DIVERGENCE"
    else:
        disposition = "CONFORMS"
    payload = {
        "schema": "bbk.go.planned-actual-structure-comparison.v1",
        "profile": {"id": "go", "version": VERSION},
        "bbk_version": BBK_TARGET_VERSION,
        "input": input_record("ImplementationStructureContract", str(contract.get("contractId")), str(contract.get("revision")), contract_digest),
        "preflight_sha256": actual.get("preflight_sha256"),
        "applicability": {"level": str(contract.get("applicability", {}).get("level") or "none"), "disposition": "SUPPORTED", "rationale": str(contract.get("applicability", {}).get("rationale") or ""), "triggers": list(contract.get("applicability", {}).get("triggers", []))},
        "planned_contract_sha256": contract_digest,
        "actual_inventory_sha256": actual["output_sha256"],
        "differences": differences,
        "summary": counts,
        "disposition": disposition,
        "unsupported_or_uncertain": list(actual.get("unsupported_or_uncertain", [])),
        "advisories": [item for item in differences if item["class"] == "advisory"],
        "blockers": [item for item in differences if item["class"] in {"material", "unknown"} and disposition in {"MATERIAL_DIVERGENCE", "BLOCKED"}],
        "authority_boundary": dict(NO_AUTHORITY_BOUNDARY),
    }
    return output_digest(payload)


def structure_command(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.contract).expanduser().resolve()
    contract, digest = load_validated(path, "bbk-implementation-structure-contract-v1.schema.json")
    root = Path(args.root or Path.cwd()).expanduser().resolve()
    tier = args.assurance_tier or str(contract.get("review", {}).get("assuranceTier") or "material")
    if tier not in TIER_RANK:
        raise GoProfileError(f"unsupported assurance tier: {tier}")
    return project_structure(contract, digest, root=root, role=normalize_role(args.role or "architect"), task_profile=args.task_profile or "implementation-structure", tier=tier, run_tools=bool(args.run_tools))


def slice_command(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.slice).expanduser().resolve()
    value, digest = load_validated(path, "bbk-execution-slice-v1.schema.json")
    root = Path(args.root or Path.cwd()).expanduser().resolve()
    tier = args.assurance_tier or "material"
    if tier not in TIER_RANK:
        raise GoProfileError(f"unsupported assurance tier: {tier}")
    return project_slice(value, digest, root=root, role=normalize_role(args.role or "planning_wayfinder"), task_profile=args.task_profile or "execution-slicing", tier=tier, run_tools=bool(args.run_tools))


def inventory_command(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root or Path.cwd()).expanduser().resolve()
    return build_actual_inventory(root, run_tools=bool(args.run_tools))


def structure_review_command(args: argparse.Namespace) -> dict[str, Any]:
    contract_path = Path(args.contract).expanduser().resolve()
    contract, contract_digest = load_validated(contract_path, "bbk-implementation-structure-contract-v1.schema.json")
    root = Path(args.root or Path.cwd()).expanduser().resolve()
    tier = args.assurance_tier or str(contract.get("review", {}).get("assuranceTier") or "material")
    if tier not in TIER_RANK:
        raise GoProfileError(f"unsupported assurance tier: {tier}")
    level = str(contract.get("applicability", {}).get("level") or "none")
    candidate_path = Path(args.candidate).expanduser().resolve()
    candidate = read_json(candidate_path)
    candidate_digest = sha256_file(candidate_path)
    if args.actual_inventory:
        actual_path = Path(args.actual_inventory).expanduser().resolve()
        actual = read_json(actual_path)
        errors = schema_errors(actual, read_json(PROFILE_ROOT / "schemas" / "bbk-go-actual-structure-inventory-v1.schema.json"))
        if errors:
            raise GoProfileError("actual inventory schema validation failed:\n- " + "\n- ".join(errors[:50]))
    else:
        actual = build_actual_inventory(root, run_tools=bool(args.run_tools))
    if level == "none":
        comparison = compare_structure(contract, contract_digest, actual, tier=tier)
        disposition = "NOT_APPLICABLE"
        findings: list[dict[str, Any]] = []
    else:
        comparison = compare_structure(contract, contract_digest, actual, tier=tier)
        disposition = comparison["disposition"]
        findings = [item for item in comparison.get("differences", []) if item.get("class") not in {"within-delegated-freedom"}]
    review_id = args.review_id or f"GO-STRUCTURE-REVIEW-{contract.get('contractId')}-{candidate_digest[:12]}"
    payload = {
        "schema": "bbk.go.structure-review-result.v1",
        "profile": {"id": "go", "version": VERSION},
        "bbk_version": BBK_TARGET_VERSION,
        "input": input_record("ImplementationStructureContract", str(contract.get("contractId")), str(contract.get("revision")), contract_digest),
        "preflight_sha256": actual.get("preflight_sha256"),
        "applicability": {"level": level, "disposition": "NOT_APPLICABLE" if level == "none" else "SUPPORTED", "rationale": str(contract.get("applicability", {}).get("rationale") or ""), "triggers": list(contract.get("applicability", {}).get("triggers", []))},
        "review_id": review_id,
        "candidate": {"path": str(candidate_path), "sha256": candidate_digest, "manifest_identity": candidate.get("candidate_id") or candidate.get("id") or candidate.get("manifest_content_sha256") or candidate.get("content_sha256")},
        "actual_inventory_sha256": actual.get("output_sha256"),
        "comparison": comparison,
        "findings": findings,
        "disposition": disposition,
        "unsupported_or_uncertain": comparison.get("unsupported_or_uncertain", []),
        "advisories": comparison.get("advisories", []),
        "blockers": comparison.get("blockers", []),
        "authority_boundary": dict(NO_AUTHORITY_BOUNDARY),
    }
    return output_digest(payload)


def human(value: dict[str, Any]) -> str:
    schema = value.get("schema")
    if schema == "bbk.go-preflight.v1":
        return f"Go preflight: {value['root']}\nModules: {len(value['modules'])}\nWorkspace: {value['workspace']['active']}\nDigest: {value['digest']}"
    if schema == "bbk.go-profile-resolution.v1":
        items = ", ".join(item["id"] for item in value["selected_components"])
        return f"Go profile resolution\nRole: {value['inputs']['role']}\nTier: {value['inputs']['assurance_tier']}\nComponents: {items}\nGates: {len(value['gate_plan']['selected'])}\nEffective digest: {value['effective_sha256']}"
    if schema == "bbk.go-gate-plan.v1":
        return "\n".join([f"Go gate plan ({value['tier']}):", *[f"- {item['id']}" for item in value["selected"]], f"Digest: {value['digest']}"])
    if schema == "bbk.go-format-check.v1":
        return f"Go format check: {value['status']}\nChecked: {value.get('checked_files', 0)}\nUnformatted: {len(value.get('unformatted', []))}"
    if schema == "bbk.go.implementation-structure-projection.v1":
        return f"Go structure projection: {value['applicability']['disposition']}\nContract: {value['input']['id']}@{value['input']['revision']}\nReview selected: {value['review_selection']['selected']}\nDigest: {value['output_sha256']}"
    if schema == "bbk.go.execution-slice-projection.v1":
        return f"Go execution slice projection: {value['applicability']['disposition']}\nSlice: {value['input']['id']}\nFoundation: {value['foundation_assessment']['status']}\nDigest: {value['output_sha256']}"
    if schema == "bbk.go.structure-review-result.v1":
        return f"Go structure review: {value['disposition']}\nFindings: {len(value['findings'])}\nDigest: {value['output_sha256']}"
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
    parser.add_argument("--contract")
    parser.add_argument("--slice")
    parser.add_argument("--run-tools", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bbk-go", description=__doc__)
    parser.add_argument("--version", action="version", version=f"bbk-profile-go {VERSION}")
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
    p.add_argument("--task-profile")
    p.add_argument("--assurance-tier", choices=list(TIER_RANK))
    p.add_argument("--run-tools", action="store_true")
    p.set_defaults(func=structure_command)
    p = sub.add_parser("slice")
    p.add_argument("--root")
    p.add_argument("--slice", required=True)
    p.add_argument("--role")
    p.add_argument("--task-profile")
    p.add_argument("--assurance-tier", choices=list(TIER_RANK))
    p.add_argument("--run-tools", action="store_true")
    p.set_defaults(func=slice_command)
    p = sub.add_parser("inventory")
    p.add_argument("--root")
    p.add_argument("--run-tools", action="store_true")
    p.set_defaults(func=inventory_command)
    p = sub.add_parser("structure-review")
    p.add_argument("--root")
    p.add_argument("--contract", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--actual-inventory")
    p.add_argument("--assurance-tier", choices=list(TIER_RANK))
    p.add_argument("--review-id")
    p.add_argument("--run-tools", action="store_true")
    p.set_defaults(func=structure_review_command)
    p = sub.add_parser("check-format")
    p.add_argument("--root")
    p.add_argument("--path", action="append")
    p.set_defaults(func=check_format)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    normalized = list(sys.argv[1:] if argv is None else argv)
    if "--json" in normalized and normalized and normalized[0] != "--json":
        normalized.remove("--json")
        normalized.insert(0, "--json")
    args = build_parser().parse_args(normalized)
    try:
        value = args.func(args)
    except GoProfileError as exc:
        if args.json:
            print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"bbk-go: error: {exc}", file=sys.stderr)
        return 2
    print(pretty(value), end="") if args.json else print(human(value))
    status = value.get("status") if isinstance(value, dict) else None
    disposition = value.get("disposition") if isinstance(value, dict) else None
    blockers = value.get("blockers") if isinstance(value, dict) else None
    if status in {"FAIL", "ERROR", "BLOCKED"}:
        return 1
    if disposition in {"BLOCKED", "MATERIAL_DIVERGENCE"}:
        return 1
    if isinstance(blockers, list) and blockers:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
