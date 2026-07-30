#!/usr/bin/env python3
"""Deterministic resolver and preflight CLI for bbk-profile-python.

The profile adds procedure, routing, review criteria, and gate recipes. It never
creates environments, installs tools, grants effects, broadens scope, or declares
a verification pass.
"""
from __future__ import annotations

import argparse
import ast
import configparser
import datetime as dt
import fnmatch
import hashlib
import importlib.metadata
import importlib.util
import json
import locale
import os
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import time
import tomllib
from pathlib import Path
from typing import Any, Iterable, Sequence

PROFILE_ROOT = Path(os.environ.get("BBK_PROFILE_ROOT", Path(__file__).resolve().parents[1])).resolve()
PROFILE = json.loads((PROFILE_ROOT / "PROFILE.json").read_text(encoding="utf-8"))
VERSION = (PROFILE_ROOT / "VERSION").read_text(encoding="utf-8").strip()
TIER_RANK = {"routine": 0, "material": 1, "consequential": 2, "critical": 3}
SECRET_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL", "PRIVATE_KEY", "AUTH", "COOKIE")
MAX_CAPTURE = 256 * 1024


class PythonProfileError(RuntimeError):
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
        raise PythonProfileError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PythonProfileError(f"invalid JSON in {path}: {exc}") from exc


def read_toml(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PythonProfileError(f"missing file: {path}") from exc
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise PythonProfileError(f"invalid TOML in {path}: {exc}") from exc


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def find_python_root(start: Path) -> Path:
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    fallback: Path | None = None
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
        if fallback is None and ((candidate / "setup.cfg").is_file() or (candidate / "setup.py").is_file()):
            fallback = candidate
    if fallback:
        return fallback
    raise PythonProfileError(f"no pyproject.toml, setup.cfg, or setup.py found from {current}")


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, (str, int, float))]
    return []


def project_metadata(root: Path) -> dict[str, Any]:
    pyproject_path = root / "pyproject.toml"
    setup_cfg = root / "setup.cfg"
    setup_py = root / "setup.py"
    data: dict[str, Any] = read_toml(pyproject_path) if pyproject_path.is_file() else {}
    project = data.get("project") if isinstance(data.get("project"), dict) else {}
    build = data.get("build-system") if isinstance(data.get("build-system"), dict) else {}
    optional = project.get("optional-dependencies") if isinstance(project.get("optional-dependencies"), dict) else {}
    scripts = project.get("scripts") if isinstance(project.get("scripts"), dict) else {}
    gui_scripts = project.get("gui-scripts") if isinstance(project.get("gui-scripts"), dict) else {}
    entry_points = project.get("entry-points") if isinstance(project.get("entry-points"), dict) else {}
    tools = data.get("tool") if isinstance(data.get("tool"), dict) else {}
    setuptools = tools.get("setuptools") if isinstance(tools.get("setuptools"), dict) else {}
    package_dir = setuptools.get("package-dir") if isinstance(setuptools.get("package-dir"), dict) else {}
    find_cfg = setuptools.get("packages", {}).get("find", {}) if isinstance(setuptools.get("packages"), dict) and isinstance(setuptools.get("packages", {}).get("find"), dict) else {}
    source_roots: list[str] = []
    if isinstance(package_dir.get(""), str):
        source_roots.append(package_dir[""])
    source_roots.extend(str(item) for item in listify(find_cfg.get("where")))
    for conventional in ("src", "lib"):
        if (root / conventional).is_dir():
            source_roots.append(conventional)
    if not source_roots:
        source_roots.append(".")
    source_roots = sorted(dict.fromkeys(source_roots))

    dependency_records: list[dict[str, Any]] = []
    for raw in listify(project.get("dependencies")):
        dependency_records.append({"group": "runtime", "spec": raw})
    for name, values in optional.items():
        for raw in listify(values):
            dependency_records.append({"group": f"extra:{name}", "spec": raw})

    files = []
    for path in (pyproject_path, setup_cfg, setup_py):
        if path.is_file():
            files.append({"path": relpath(path, root), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    return {
        "metadata_files": files,
        "name": project.get("name") or root.name,
        "version": project.get("version"),
        "dynamic": sorted(listify(project.get("dynamic"))),
        "requires_python": project.get("requires-python"),
        "dependencies": dependency_records,
        "optional_dependency_groups": sorted(str(name) for name in optional),
        "scripts": {str(key): str(value) for key, value in scripts.items()},
        "gui_scripts": {str(key): str(value) for key, value in gui_scripts.items()},
        "entry_point_groups": sorted(str(name) for name in entry_points),
        "build_backend": build.get("build-backend"),
        "build_requires": listify(build.get("requires")),
        "source_roots": source_roots,
        "src_layout": "src" in source_roots,
        "tool_sections": sorted(str(name) for name in tools),
        "has_setup_cfg": setup_cfg.is_file(),
        "has_setup_py": setup_py.is_file(),
    }


def discover_packages(root: Path, source_roots: Sequence[str]) -> dict[str, Any]:
    packages: set[str] = set()
    modules: set[str] = set()
    namespace_candidates: set[str] = set()
    py_files = 0
    pyi_files = 0
    for raw_root in source_roots:
        base = (root / raw_root).resolve() if raw_root != "." else root.resolve()
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if any(part.startswith(".") or part in {"__pycache__", ".venv", "venv", "build", "dist"} for part in path.relative_to(root).parts):
                continue
            py_files += 1
            if path.name == "__init__.py":
                try:
                    package = ".".join(path.parent.relative_to(base).parts)
                except ValueError:
                    package = ""
                if package:
                    packages.add(package)
            elif path.parent == base:
                modules.add(path.stem)
            else:
                parent = path.parent
                if not (parent / "__init__.py").is_file():
                    try:
                        candidate = ".".join(parent.relative_to(base).parts)
                    except ValueError:
                        candidate = ""
                    if candidate:
                        namespace_candidates.add(candidate)
        for path in base.rglob("*.pyi"):
            if not any(part.startswith(".") or part in {".venv", "venv", "build", "dist"} for part in path.relative_to(root).parts):
                pyi_files += 1
    return {
        "packages": sorted(packages),
        "top_level_modules": sorted(modules),
        "namespace_candidates": sorted(namespace_candidates),
        "python_file_count": py_files,
        "stub_file_count": pyi_files,
        "py_typed": sorted(relpath(path, root) for path in root.rglob("py.typed") if path.is_file()),
        "test_roots": [name for name in ("tests", "test") if (root / name).is_dir()],
    }


def interpreter_summary() -> dict[str, Any]:
    free_threaded: bool | None = None
    method = "unknown"
    is_gil_enabled = getattr(sys, "_is_gil_enabled", None)
    if callable(is_gil_enabled):
        try:
            free_threaded = not bool(is_gil_enabled())
            method = "sys._is_gil_enabled"
        except Exception:
            pass
    if free_threaded is None:
        raw = sysconfig.get_config_var("Py_GIL_DISABLED")
        if raw is not None:
            free_threaded = bool(raw)
            method = "sysconfig:Py_GIL_DISABLED"
    executable = Path(sys.executable).resolve()
    result = {
        "implementation": platform.python_implementation(),
        "version": platform.python_version(),
        "version_info": list(sys.version_info[:5]),
        "executable": str(executable),
        "executable_sha256": sha256_file(executable) if executable.is_file() else None,
        "cache_tag": getattr(sys.implementation, "cache_tag", None),
        "abi_flags": getattr(sys, "abiflags", ""),
        "soabi": sysconfig.get_config_var("SOABI"),
        "platform": sys.platform,
        "machine": platform.machine(),
        "architecture": platform.architecture()[0],
        "free_threaded": free_threaded,
        "free_threaded_detection": method,
        "debug_build": bool(sysconfig.get_config_var("Py_DEBUG")),
    }
    return result


def environment_summary(run_tools: bool) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    relevant = {
        "PYTHONPATH", "PYTHONHASHSEED", "PYTHONUTF8", "PYTHONIOENCODING", "PYTHONDONTWRITEBYTECODE",
        "VIRTUAL_ENV", "CONDA_PREFIX", "PIP_CONFIG_FILE", "PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL",
        "UV_PROJECT_ENVIRONMENT", "UV_PYTHON", "POETRY_ACTIVE", "PDM_PROJECT_ROOT", "TZ", "LANG", "LC_ALL",
    }
    for key, value in sorted(os.environ.items()):
        if key not in relevant and not key.startswith(("PYTHON", "PIP_", "UV_", "POETRY_", "PDM_", "CONDA_")):
            continue
        if any(marker in key.upper() for marker in SECRET_MARKERS):
            continue
        encoded = value.encode("utf-8", "replace")
        records.append({"name": key, "value_sha256": sha256_bytes(encoded), "bytes": len(encoded)})
    result: dict[str, Any] = {
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
        "exec_prefix": sys.exec_prefix,
        "virtual_environment": sys.prefix != sys.base_prefix or bool(os.environ.get("VIRTUAL_ENV") or os.environ.get("CONDA_PREFIX")),
        "preferred_encoding": locale.getpreferredencoding(False),
        "filesystem_encoding": sys.getfilesystemencoding(),
        "timezone": list(time.tzname),
        "environment_inputs": records,
    }
    if run_tools:
        distributions = []
        for dist in importlib.metadata.distributions():
            name = dist.metadata.get("Name") or "<unknown>"
            distributions.append(f"{name}=={dist.version}")
        distributions.sort(key=str.lower)
        result["installed_distribution_count"] = len(distributions)
        result["installed_distributions_sha256"] = sha256_bytes("\n".join(distributions).encode("utf-8"))
    return result


def lock_summary(root: Path) -> dict[str, Any]:
    names = [
        "pylock.toml", "uv.lock", "poetry.lock", "pdm.lock", "Pipfile.lock", "requirements.lock",
        "conda-lock.yml", "conda-lock.yaml", "environment.yml", "environment.yaml",
    ]
    records: list[dict[str, Any]] = []
    for name in names:
        path = root / name
        if path.is_file():
            records.append({"path": name, "sha256": sha256_file(path), "bytes": path.stat().st_size, "kind": name})
    for path in sorted(root.glob("requirements*.txt")):
        records.append({"path": relpath(path, root), "sha256": sha256_file(path), "bytes": path.stat().st_size, "kind": "requirements"})
    return {"files": records, "policy_detected": bool(records)}


def parse_simple_targets(path: Path) -> list[str]:
    if not path.is_file():
        return []
    values: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line[0].isspace() or line.startswith(("#", ".")):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*:(?:\s|$)", line)
        if match:
            values.append(match.group(1))
    return sorted(set(values))


def detect_repository_commands(root: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    just_targets = parse_simple_targets(root / "Justfile")
    make_targets = parse_simple_targets(root / "Makefile")
    nox_sessions: list[str] = []
    noxfile = root / "noxfile.py"
    if noxfile.is_file():
        text = noxfile.read_text(encoding="utf-8", errors="replace")
        nox_sessions = sorted(set(re.findall(r"(?m)^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text)))
    tox = (root / "tox.ini").is_file() or (root / "tox.toml").is_file()
    pyproject = read_toml(root / "pyproject.toml") if (root / "pyproject.toml").is_file() else {}
    tools = pyproject.get("tool") if isinstance(pyproject.get("tool"), dict) else {}

    aliases = {
        "format": ["fmt-check", "format-check", "fmt", "format"],
        "lint": ["lint", "ruff", "check"],
        "type": ["type", "typing", "mypy", "pyright", "typecheck"],
        "test": ["test", "tests", "pytest"],
        "integration": ["integration", "integration-test", "test-integration"],
        "build": ["build", "package"],
        "installed-wheel": ["test-wheel", "wheel-test", "installed-test"],
        "package-inspection": ["inspect-package", "package-check"],
        "matrix": ["matrix", "test-matrix", "tox", "nox"],
        "extras-matrix": ["extras-matrix", "test-extras"],
        "sdist-wheel-roundtrip": ["package-roundtrip", "sdist-test"],
        "compatibility": ["compat", "compatibility", "api-check"],
        "async-cancellation": ["test-cancellation", "async-test"],
        "process-matrix": ["process-test", "multiprocessing-test"],
        "free-threaded": ["free-threaded", "nogil-test"],
        "native-test": ["native-test", "ffi-test"],
        "migration-test": ["migration-test", "migrations"],
        "security-test": ["security-test", "security"],
        "dependency-audit": ["audit", "dependency-audit"],
        "property-test": ["property-test", "hypothesis"],
        "fuzz": ["fuzz"],
        "mutation": ["mutation", "mutate"],
        "benchmark": ["benchmark", "bench"],
        "operational-test": ["operational-test", "smoke", "service-test"],
    }
    all_targets = [("just", name) for name in just_targets] + [("make", name) for name in make_targets]
    commands: dict[str, list[str]] = {}
    sources: dict[str, str] = {}
    for key, candidates in aliases.items():
        for kind, target in all_targets:
            if target in candidates:
                commands[key] = [kind, target] if kind == "make" else ["just", target]
                sources[key] = f"{kind}:{target}"
                break
    if "test" not in commands and ("pytest" in tools or (root / "pytest.ini").is_file() or (root / "tests").is_dir()):
        commands["test"] = [sys.executable, "-m", "pytest"]
        sources["test"] = "detected-pytest"
    if "format" not in commands:
        if "ruff" in tools:
            commands["format"] = ["ruff", "format", "--check", "."]
            sources["format"] = "pyproject:tool.ruff"
        elif "black" in tools:
            commands["format"] = ["black", "--check", "."]
            sources["format"] = "pyproject:tool.black"
    if "lint" not in commands and "ruff" in tools:
        commands["lint"] = ["ruff", "check", "."]
        sources["lint"] = "pyproject:tool.ruff"
    if "type" not in commands:
        if "mypy" in tools or (root / "mypy.ini").is_file():
            commands["type"] = ["mypy"]
            sources["type"] = "detected-mypy"
        elif (root / "pyrightconfig.json").is_file() or "pyright" in tools:
            commands["type"] = ["pyright"]
            sources["type"] = "detected-pyright"
    if "build" not in commands and metadata.get("build_backend"):
        commands["build"] = [sys.executable, "-m", "build"]
        sources["build"] = "declared-build-backend"
    if "matrix" not in commands:
        if nox_sessions:
            commands["matrix"] = ["nox"]
            sources["matrix"] = "noxfile.py"
        elif tox:
            commands["matrix"] = ["tox"]
            sources["matrix"] = "tox-config"
    return {
        "commands": commands,
        "sources": sources,
        "just_targets": just_targets,
        "make_targets": make_targets,
        "nox_sessions": nox_sessions,
        "tox_configured": tox,
    }


def iter_scan_files(root: Path, *, max_files: int = 5000) -> Iterable[Path]:
    excluded = {".git", ".venv", "venv", "node_modules", "dist", "build", ".tox", ".nox", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"}
    count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in excluded for part in parts):
            continue
        count += 1
        if count > max_files:
            break
        yield path


def scan_support_signals(root: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    suffix_counts: dict[str, int] = {}
    signals = {
        "asyncio": False, "threading": False, "multiprocessing": False, "free_threaded": False,
        "typing": False, "runtime_annotations": False, "plugins": bool(metadata.get("entry_point_groups")),
        "native_extension": False, "migrations": False, "web": False, "dynamic_execution": False,
        "deserialization": False, "subprocess": False, "archives": False,
    }
    patterns = {
        "asyncio": re.compile(r"async\s+def|asyncio\.|TaskGroup|create_task"),
        "threading": re.compile(r"threading\.|ThreadPoolExecutor"),
        "multiprocessing": re.compile(r"multiprocessing\.|ProcessPoolExecutor"),
        "free_threaded": re.compile(r"Py_GIL_DISABLED|_is_gil_enabled|free.thread"),
        "typing": re.compile(r"from\s+typing\s+import|typing_extensions|\.pyi\b"),
        "runtime_annotations": re.compile(r"get_type_hints|annotationlib|__annotations__"),
        "plugins": re.compile(r"importlib\.metadata|entry_points|import_module"),
        "web": re.compile(r"FastAPI|Django|Flask|Starlette|HTMX|hx-target|aiohttp"),
        "dynamic_execution": re.compile(r"(?<![A-Za-z0-9_])(eval|exec|compile)\s*\("),
        "deserialization": re.compile(r"pickle\.(load|loads)|yaml\.(load|unsafe_load)|shelve\."),
        "subprocess": re.compile(r"subprocess\.|os\.system|shell\s*=\s*True"),
        "archives": re.compile(r"tarfile\.|zipfile\.|unpack_archive"),
    }
    scanned = 0
    for path in iter_scan_files(root):
        suffix_counts[path.suffix.lower()] = suffix_counts.get(path.suffix.lower(), 0) + 1
        rel = relpath(path, root)
        if path.suffix.lower() in {".c", ".cc", ".cpp", ".h", ".hpp", ".pyx", ".pxd"} or path.name == "Cargo.toml":
            signals["native_extension"] = True
        if "migration" in rel.lower() or rel.startswith("alembic/"):
            signals["migrations"] = True
        if path.stat().st_size > 512 * 1024 or path.suffix.lower() not in {".py", ".pyi", ".toml", ".ini", ".cfg", ".txt", ".yaml", ".yml", ".json", ".c", ".h", ".cc", ".cpp", ".hpp", ".pyx", ".pxd"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        scanned += 1
        for key, pattern in patterns.items():
            if not signals[key] and pattern.search(text):
                signals[key] = True
    return {"signals": signals, "suffix_counts": dict(sorted(suffix_counts.items())), "text_files_scanned": scanned}


def run_command(argv: Sequence[str], cwd: Path, timeout: float = 20.0) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            [str(item) for item in argv], cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
        stdout, stderr = completed.stdout, completed.stderr
        if len(stdout.encode("utf-8")) > MAX_CAPTURE:
            stdout = stdout.encode("utf-8")[:MAX_CAPTURE].decode("utf-8", "replace") + "\n[truncated]\n"
        if len(stderr.encode("utf-8")) > MAX_CAPTURE:
            stderr = stderr.encode("utf-8")[:MAX_CAPTURE].decode("utf-8", "replace") + "\n[truncated]\n"
        return {"argv": [str(item) for item in argv], "returncode": completed.returncode, "stdout": stdout, "stderr": stderr, "duration_seconds": round(time.monotonic() - started, 6)}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"argv": [str(item) for item in argv], "returncode": 124 if isinstance(exc, subprocess.TimeoutExpired) else 127, "stdout": "", "stderr": str(exc), "duration_seconds": round(time.monotonic() - started, 6)}


def tool_summary(root: Path, run_tools: bool) -> dict[str, Any]:
    names = ["python", "pip", "uv", "poetry", "pdm", "hatch", "tox", "nox", "pytest", "ruff", "mypy", "pyright", "build", "twine", "pip-audit"]
    values: dict[str, Any] = {}
    for name in names:
        if name == "python":
            path = sys.executable
        else:
            path = shutil.which(name)
        item: dict[str, Any] = {"available": bool(path), "path": str(path) if path else None}
        if path and run_tools:
            argv = [path, "--version"]
            if name == "pip" and not shutil.which("pip"):
                argv = [sys.executable, "-m", "pip", "--version"]
            item["version_probe"] = run_command(argv, root)
        values[name] = item
    return values


def preflight(root_arg: Path, *, run_tools: bool = False) -> dict[str, Any]:
    root = find_python_root(root_arg)
    metadata = project_metadata(root)
    packages = discover_packages(root, metadata["source_roots"])
    locks = lock_summary(root)
    commands = detect_repository_commands(root, metadata)
    support = scan_support_signals(root, metadata)
    packaging = {
        "build_backend": metadata.get("build_backend"),
        "build_requires": metadata.get("build_requires"),
        "requires_python": metadata.get("requires_python"),
        "source_roots": metadata.get("source_roots"),
        "src_layout": metadata.get("src_layout"),
        "packages": packages,
        "scripts": metadata.get("scripts"),
        "gui_scripts": metadata.get("gui_scripts"),
        "entry_point_groups": metadata.get("entry_point_groups"),
        "locks": locks,
    }
    payload: dict[str, Any] = {
        "schema": "bbk.python-preflight.v1",
        "profile": {"id": PROFILE["id"], "version": VERSION},
        "root": str(root),
        "project": metadata,
        "interpreter": interpreter_summary(),
        "environment": environment_summary(run_tools),
        "packaging": packaging,
        "repository_commands": commands,
        "support_signals": support,
        "tools": tool_summary(root, run_tools),
        "run_tools": run_tools,
        "limitations": [
            "Static preflight does not import the application, create an environment, install dependencies, or run repository commands.",
            "Detected support signals indicate possible applicability; they are not proof that a capability is supported or correct.",
        ],
    }
    payload["digest"] = sha256_bytes(canonical_bytes(payload))
    return payload


def normalize_role(value: str | None) -> str:
    raw = (value or "worker").strip().lower().replace("_", "-")
    aliases = {
        "verification_designer": "verification-designer", "worker_designer": "worker-designer",
        "review": "reviewer", "validation": "validator",
    }
    return aliases.get(raw, raw)


def load_work_unit(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    value = read_json(path)
    if not isinstance(value, dict):
        raise PythonProfileError("work unit must be a JSON object")
    return value


def git_changed_paths(root: Path) -> list[str]:
    if not (root / ".git").exists() and not (root / ".git").is_file():
        return []
    result = run_command(["git", "status", "--porcelain=v1", "--untracked-files=all"], root)
    if result["returncode"] != 0:
        return []
    values: list[str] = []
    for line in result["stdout"].splitlines():
        raw = line[3:] if len(line) > 3 else line
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        raw = raw.strip().strip('"')
        if raw:
            values.append(raw.replace("\\", "/"))
    return sorted(set(values))


def collect_scope_paths(root: Path, supplied: Sequence[str], work_unit: dict[str, Any]) -> tuple[list[str], str]:
    values: list[str] = []
    source = "explicit"
    if supplied:
        values.extend(str(item) for item in supplied)
    else:
        for key in ("paths", "scope_paths", "writable_paths", "readable_paths"):
            values.extend(listify(work_unit.get(key)))
        if values:
            source = "work-unit"
        else:
            values = git_changed_paths(root)
            source = "git-changed" if values else "project-default"
    normalized: list[str] = []
    for raw in values:
        path = Path(raw)
        if path.is_absolute():
            try:
                raw = path.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                raw = str(path.resolve())
        normalized.append(str(raw).replace("\\", "/").lstrip("./"))
    if not normalized:
        normalized = ["pyproject.toml", *project_metadata(root).get("source_roots", ["."])]
    return sorted(dict.fromkeys(normalized)), source


def path_glob_match(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/").lstrip("./")
    pattern = pattern.replace("\\", "/").lstrip("./")
    return fnmatch.fnmatch(path, pattern) or (pattern.startswith("**/") and fnmatch.fnmatch(path, pattern[3:]))


def excluded_path(rel: str, excludes: Sequence[str]) -> bool:
    return any(path_glob_match(rel, pattern) or (pattern.endswith("/**") and (rel == pattern[:-3] or rel.startswith(pattern[:-3].rstrip("/") + "/"))) for pattern in excludes)


def expand_scope_files(root: Path, scope_paths: Sequence[str], scan: dict[str, Any]) -> list[Path]:
    extensions = set(str(item) for item in scan.get("extensions", []))
    excludes = listify(scan.get("exclude_globs"))
    max_files = int(scan.get("max_files", 2000))
    values: set[Path] = set()
    for raw in scope_paths:
        candidate = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            rel = relpath(candidate, root)
            if candidate.suffix.lower() in extensions and not excluded_path(rel, excludes):
                values.add(candidate)
        elif candidate.is_dir():
            for path in candidate.rglob("*"):
                if not path.is_file() or path.is_symlink() or path.suffix.lower() not in extensions:
                    continue
                rel = relpath(path, root)
                if not excluded_path(rel, excludes):
                    values.add(path.resolve())
                if len(values) >= max_files:
                    break
        if len(values) >= max_files:
            break
    return sorted(values, key=lambda item: relpath(item, root))[:max_files]


def detect_triggers(root: Path, scope_paths: Sequence[str], hints: Sequence[str], change_classes: Sequence[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mapping = read_json(PROFILE_ROOT / PROFILE["selection"]["risk_trigger_map"])
    scan_cfg = mapping.get("scan", {})
    files = expand_scope_files(root, scope_paths, scan_cfg)
    max_bytes = int(scan_cfg.get("max_file_bytes", 524288))
    texts: dict[Path, str] = {}
    for path in files:
        try:
            if path.stat().st_size <= max_bytes:
                texts[path] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    hint_set = {str(item).strip().lower() for item in hints if str(item).strip()}
    class_set = {str(item).strip().lower() for item in change_classes if str(item).strip()}
    observations: list[dict[str, Any]] = []
    for trigger in mapping.get("triggers", []):
        reasons: list[str] = []
        trigger_hints = {str(item).lower() for item in trigger.get("hints", [])}
        matched_hints = sorted(hint_set & (trigger_hints | {str(trigger.get("id", "")).lower()}))
        if matched_hints:
            reasons.append("hints: " + ", ".join(matched_hints))
        matched_classes = sorted(class_set & {str(item).lower() for item in trigger.get("change_classes", [])})
        if matched_classes:
            reasons.append("change classes: " + ", ".join(matched_classes))
        matched_paths: list[str] = []
        for path in files:
            rel = relpath(path, root)
            if any(path_glob_match(rel, pattern) for pattern in trigger.get("path_globs", [])):
                matched_paths.append(rel)
        if matched_paths:
            reasons.append("paths: " + ", ".join(matched_paths[:8]))
        regex_hits: list[str] = []
        for pattern in trigger.get("regexes", []):
            try:
                compiled = re.compile(pattern)
            except re.error as exc:
                raise PythonProfileError(f"invalid trigger regex {pattern!r}: {exc}") from exc
            for path, text in texts.items():
                if compiled.search(text):
                    regex_hits.append(relpath(path, root))
                    break
        if regex_hits:
            reasons.append("content: " + ", ".join(sorted(set(regex_hits))))
        if reasons:
            observations.append({
                "id": trigger["id"], "reasons": reasons,
                "skills": trigger.get("skills", []), "skills_by_role": trigger.get("skills_by_role", {}),
                "gate_tags": trigger.get("gate_tags", []), "exclusive_survey": bool(trigger.get("exclusive_survey", False)),
            })
    scan_result = {
        "scope_paths": list(scope_paths),
        "files_considered": [relpath(path, root) for path in files],
        "text_files_scanned": len(texts),
        "mapping_sha256": sha256_file(PROFILE_ROOT / PROFILE["selection"]["risk_trigger_map"]),
    }
    return sorted(observations, key=lambda item: item["id"]), scan_result


def skill_catalog() -> dict[str, dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    for item in PROFILE.get("skills", []):
        path = PROFILE_ROOT / item["path"]
        values[item["id"]] = {**item, "sha256": sha256_file(path), "bytes": path.stat().st_size}
    return values


def add_component(target: dict[str, dict[str, Any]], catalog: dict[str, dict[str, Any]], component_id: str, reason: str) -> None:
    if component_id not in catalog:
        raise PythonProfileError(f"unknown profile component: {component_id}")
    if component_id not in target:
        target[component_id] = {**catalog[component_id], "selection_reasons": []}
    if reason not in target[component_id]["selection_reasons"]:
        target[component_id]["selection_reasons"].append(reason)


def select_components(role: str, task_profile: str, observations: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    catalog = skill_catalog()
    task_map = read_json(PROFILE_ROOT / PROFILE["selection"]["task_skill_map"])
    selected: dict[str, dict[str, Any]] = {}
    recommended: dict[str, dict[str, Any]] = {}
    add_component(selected, catalog, "bbk-python", "base Python profile router")

    broad = next((item for item in observations if item.get("exclusive_survey")), None)
    if broad and role in {"reviewer", "architect"}:
        for component in broad.get("skills_by_role", {}).get(role, ["comprehensive-analysis-python"]):
            add_component(selected, catalog, component, f"exclusive broad survey: {broad['id']}")
        return list(selected.values()), []

    role_defaults = task_map.get("roles", {}).get(role, {}).get("default", [])
    for component in role_defaults:
        add_component(selected, catalog, component, f"default for role {role}")
    task_components = task_map.get("task_profiles", {}).get(task_profile, {}).get(role, [])
    for component in task_components:
        add_component(selected, catalog, component, f"task profile {task_profile}")

    for observation in observations:
        components = list(observation.get("skills", []))
        components.extend(observation.get("skills_by_role", {}).get(role, []))
        for component in components:
            kind = catalog.get(component, {}).get("kind", "")
            reason = f"trigger {observation['id']}: {'; '.join(observation['reasons'])}"
            if role == "worker" and kind in {"focused-review", "survey-review", "optional-focused-review", "focused-assurance"}:
                add_component(recommended, catalog, component, reason)
                continue
            if role in {"worker-designer", "architect"} and kind in {"focused-review", "focused-assurance", "optional-focused-review"}:
                add_component(recommended, catalog, component, reason)
                continue
            add_component(selected, catalog, component, reason)
    # Recommend focused validators for a worker even when no trigger was found.
    if role == "worker" and not recommended:
        for component in ("python-runtime-correctness-review", "python-test-strategy-review"):
            add_component(recommended, catalog, component, "candidate validator pack; final selection depends on assertions and changed behavior")
    return list(selected.values()), list(recommended.values())


def preferred_repo_command(preflight_value: dict[str, Any], gate_id: str) -> list[str] | None:
    commands = preflight_value.get("repository_commands", {}).get("commands", {})
    mapping = {
        "python-format-check": "format", "python-lint-check": "lint", "python-focused-tests": "test",
        "python-type-check-affected": "type", "python-build-distributions": "build",
        "python-installed-wheel-tests": "installed-wheel", "python-package-contents": "package-inspection",
        "python-integration-tests": "integration", "python-supported-version-matrix": "matrix",
        "python-extras-dependency-matrix": "extras-matrix", "python-sdist-wheel-roundtrip": "sdist-wheel-roundtrip",
        "python-api-typing-compatibility": "compatibility", "python-async-cancellation": "async-cancellation",
        "python-process-start-methods": "process-matrix", "python-free-threaded": "free-threaded",
        "python-native-extension": "native-test", "python-migration-rollback": "migration-test",
        "python-security-boundary": "security-test", "python-dependency-audit": "dependency-audit",
        "python-property-stateful": "property-test", "python-fuzz": "fuzz", "python-mutation": "mutation",
        "python-performance-benchmark": "benchmark", "python-operational-startup-shutdown": "operational-test",
    }
    key = mapping.get(gate_id)
    value = commands.get(key) if key else None
    return list(value) if isinstance(value, list) else None


def requirement_availability(requirement: str, preflight_value: dict[str, Any], preferred: list[str] | None) -> tuple[str, str]:
    if requirement == "bbk-python":
        return "AVAILABLE", "provided by this profile package"
    if requirement == "bbk-structure-contract-validator":
        detected = detect_structure_contract_validator()
        return detected["status"], detected["detail"]
    if requirement == "repository-defined":
        return ("AVAILABLE", "repository command detected") if preferred else ("MISSING", "no repository command detected")
    if requirement == "repository-defined-or-python-build":
        if preferred:
            return "AVAILABLE", "repository build command detected"
        return ("AVAILABLE", "python build module is installed") if importlib.util.find_spec("build") else ("MISSING", "no repository build command and python-build is unavailable")
    if requirement == "qualified-free-threaded-python":
        return ("AVAILABLE", "current interpreter is free-threaded") if preflight_value.get("interpreter", {}).get("free_threaded") else ("MISSING", "current interpreter is not a qualified free-threaded build")
    if requirement == "qualified-native-toolchain":
        signals = preflight_value.get("support_signals", {}).get("signals", {})
        return ("UNKNOWN", "native sources detected; project-specific toolchain qualification required") if signals.get("native_extension") else ("MISSING", "no native toolchain qualification is declared")
    path = shutil.which(requirement)
    return ("AVAILABLE", path) if path else ("MISSING", f"executable not found: {requirement}")


def compile_gate_plan(tier: str, observations: Sequence[dict[str, Any]], preflight_value: dict[str, Any], scope_paths: Sequence[str]) -> dict[str, Any]:
    gate_file = PROFILE_ROOT / PROFILE["gates"]
    definitions = read_json(gate_file)
    trigger_ids = {item["id"] for item in observations}
    tags = {str(tag) for item in observations for tag in item.get("gate_tags", [])}
    hints = trigger_ids | tags | {tier}
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for recipe in definitions.get("recipes", []):
        minimum = recipe.get("minimum_tier", "critical")
        if TIER_RANK.get(minimum, 99) > TIER_RANK[tier]:
            skipped.append({"id": recipe["id"], "reason": f"minimum tier is {minimum}"})
            continue
        preferred = preferred_repo_command(preflight_value, recipe["id"])
        recipe_triggers = {str(item) for item in recipe.get("triggers", [])}
        cls = recipe.get("class")
        applicable = False
        reasons: list[str] = []
        if cls == "always-cheap":
            applicable = True
            reasons.append(f"always-cheap at {tier} tier")
        elif cls == "required-if-configured" and preferred is not None:
            applicable = True
            reasons.append("repository configuration detected")
        if recipe_triggers & hints:
            applicable = True
            reasons.append("matched: " + ", ".join(sorted(recipe_triggers & hints)))
        if not applicable:
            skipped.append({"id": recipe["id"], "reason": "no applicable trigger or repository configuration"})
            continue
        command = preferred or recipe.get("command")
        availability = []
        missing = []
        unknown = []
        for requirement in recipe.get("requires", []):
            status, detail = requirement_availability(str(requirement), preflight_value, preferred)
            availability.append({"requirement": requirement, "status": status, "detail": detail})
            if status == "MISSING":
                missing.append(str(requirement))
            elif status == "UNKNOWN":
                unknown.append(str(requirement))
        if missing:
            planning_status = "BLOCKED_INPUT" if cls != "manual-experimental" else "ADVISORY_UNAVAILABLE"
        elif unknown:
            planning_status = "QUALIFICATION_REQUIRED"
        else:
            planning_status = "PLANNED"
        selected.append({
            **recipe,
            "selection_reasons": reasons,
            "scope_paths": list(scope_paths),
            "preferred_command": command,
            "repository_override": preferred is not None,
            "availability": availability,
            "planning_status": planning_status,
            "execution": "planned-only",
        })
    payload = {
        "schema": "bbk.python-gate-plan.v1", "tier": tier,
        "trigger_ids": sorted(trigger_ids), "scope_paths": list(scope_paths),
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


def make_lock(
    root: Path,
    preflight_value: dict[str, Any],
    selected: Sequence[dict[str, Any]],
    gate_plan: dict[str, Any],
    inputs: dict[str, Any],
    structure_records: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile_record = {
        "id": PROFILE["id"], "package": PROFILE.get("package"), "version": PROFILE["version"],
        "maturity": PROFILE["maturity"],
        "profile_manifest_sha256": sha256_file(PROFILE_ROOT / "PROFILE.json"),
        "package_root_sha256": profile_package_root_digest(),
        "preflight_sha256": preflight_value["digest"],
        "gate_plan_sha256": gate_plan["digest"],
        "selected_components": [{"id": item["id"], "kind": item["kind"], "sha256": item["sha256"]} for item in selected],
        "inputs": inputs,
        "implementation_structure": structure_records or {
            "support_status": "supported",
            "contract_digest": None,
            "contract_projection_digest": None,
            "slice_digest": None,
            "slice_projection_digest": None,
        },
    }
    digest_payload = {"schema": "bbk.profile-lock-effective.v1", "project_root": str(root), "profiles": [profile_record]}
    effective = sha256_bytes(canonical_bytes(digest_payload))
    timestamp = os.environ.get("BBK_LOCK_TIMESTAMP") or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {"schema": "bbk.profile-lock.v1", "generated_at": timestamp, "project_root": str(root), "profiles": [profile_record], "effective_sha256": effective}


def resolve(args: argparse.Namespace) -> dict[str, Any]:
    root = find_python_root(Path(args.root or Path.cwd()))
    work_unit = load_work_unit(Path(args.work_unit).expanduser().resolve() if args.work_unit else None)
    contract_path = Path(args.structure_contract).expanduser().resolve() if getattr(args, "structure_contract", None) else None
    slice_path = Path(args.execution_slice).expanduser().resolve() if getattr(args, "execution_slice", None) else None
    contract_value = load_generic_contract(contract_path) if contract_path else None
    slice_value = load_execution_slice(slice_path) if slice_path else None
    inferred_task = "execution-slicing" if slice_value else ("implementation-structure" if contract_value and contract_value.get("applicability", {}).get("level") != "none" else "implementation")
    task_profile = args.task_profile or str(work_unit.get("task_profile") or inferred_task)
    tier = args.assurance_tier or str(work_unit.get("assurance_tier") or work_unit.get("risk_tier") or "routine")
    if tier not in TIER_RANK:
        raise PythonProfileError(f"unsupported assurance tier: {tier}")
    role = normalize_role(args.role or str(work_unit.get("role") or "worker"))
    hints = sorted(set(list(args.hint or []) + listify(work_unit.get("profile_hints")) + listify(work_unit.get("hints"))))
    change_classes = sorted(set(list(args.change_class or []) + listify(work_unit.get("change_classes"))))
    scope_paths, scope_source = collect_scope_paths(root, args.path or [], work_unit)
    preflight_value = preflight(root, run_tools=bool(args.run_tools))
    observations, scan = detect_triggers(root, scope_paths, hints, change_classes)
    trigger_catalog = {item["id"]: item for item in read_json(PROFILE_ROOT / PROFILE["selection"]["risk_trigger_map"])["triggers"]}
    if contract_value and contract_value.get("applicability", {}).get("level") != "none" and not any(item.get("id") == "implementation-structure" for item in observations):
        trigger = trigger_catalog["implementation-structure"]
        observations.append({
            "id": "implementation-structure",
            "reasons": [f"generic contract {contract_value['contractId']}@{contract_value['revision']} supplied"],
            "skills": trigger.get("skills", []),
            "skills_by_role": trigger.get("skills_by_role", {}),
            "gate_tags": trigger.get("gate_tags", []),
            "exclusive_survey": False,
        })
        key_contracts = contract_value.get("structure", {}).get("keyContracts", [])
        if any(item.get("visibility") in {"public", "shared", "external"} for item in key_contracts):
            public_trigger = trigger_catalog["public-api"]
            if not any(item.get("id") == "public-api" for item in observations):
                observations.append({
                    "id": "public-api",
                    "reasons": ["generic structure contract contains public/shared/external key contracts"],
                    "skills": public_trigger.get("skills", []),
                    "skills_by_role": public_trigger.get("skills_by_role", {}),
                    "gate_tags": public_trigger.get("gate_tags", []),
                    "exclusive_survey": False,
                })
        if contract_value.get("structure", {}).get("stateOwnership"):
            owner_trigger = trigger_catalog["state-ownership-structure"]
            if not any(item.get("id") == "state-ownership-structure" for item in observations):
                observations.append({
                    "id": "state-ownership-structure",
                    "reasons": ["generic structure contract declares state ownership"],
                    "skills": owner_trigger.get("skills", []),
                    "skills_by_role": owner_trigger.get("skills_by_role", {}),
                    "gate_tags": owner_trigger.get("gate_tags", []),
                    "exclusive_survey": False,
                })
    if slice_value and not any(item.get("id") == "execution-slicing" for item in observations):
        observations.append({
            "id": "execution-slicing",
            "reasons": [f"generic execution slice {slice_value['sliceId']} supplied"],
            "skills": [],
            "skills_by_role": {},
            "gate_tags": ["execution-slice"],
            "exclusive_survey": False,
        })
    observations = sorted(observations, key=lambda item: item["id"])
    selected, recommended = select_components(role, task_profile, observations)
    gate_plan = compile_gate_plan(tier, observations, preflight_value, scope_paths)
    inputs = {
        "role": role, "task_profile": task_profile, "assurance_tier": tier,
        "hints": hints, "change_classes": change_classes, "scope_paths": scope_paths,
        "scope_source": scope_source, "run_tools": bool(args.run_tools),
        "work_unit_sha256": sha256_file(Path(args.work_unit).expanduser().resolve()) if args.work_unit else None,
        "structure_contract_sha256": canonical_object_digest(contract_value) if contract_value else None,
        "execution_slice_sha256": canonical_object_digest(slice_value) if slice_value else None,
    }
    structure_projection = structure_projection_value(contract_value, contract_path, root, role, task_profile, tier) if contract_value and contract_path else None
    slice_projection = slice_projection_value(slice_value, slice_path, root, role, task_profile, tier, contract_path) if slice_value and slice_path else None
    structure_records = {
        "support_status": "supported",
        "contract_digest": canonical_object_digest(contract_value) if contract_value else None,
        "contract_projection_digest": structure_projection.get("output_digest") if structure_projection else None,
        "slice_digest": canonical_object_digest(slice_value) if slice_value else None,
        "slice_projection_digest": slice_projection.get("output_digest") if slice_projection else None,
    }
    lock = make_lock(root, preflight_value, selected, gate_plan, inputs, structure_records)
    return {
        "schema": "bbk.python-profile-resolution.v1",
        "profile": {"id": PROFILE["id"], "package": PROFILE.get("package"), "version": PROFILE["version"], "maturity": PROFILE["maturity"]},
        "inputs": inputs,
        "observations": {"triggers": observations, "scan": scan, "preflight_digest": preflight_value["digest"]},
        "preflight": preflight_value,
        "selected_components": selected,
        "recommended_validator_packs": recommended,
        "gate_plan": gate_plan,
        "implementation_structure": {
            **structure_records,
            "contract_projection": structure_projection,
            "slice_projection": slice_projection,
        },
        "lock": lock,
        "effective_sha256": lock["effective_sha256"],
        "limitations": [
            "Profile selection does not grant tool, environment, network, credential, filesystem, publication, deployment, migration, or execution authority.",
            "Planned gates are not executed by resolution.",
            "Source-tree, editable, installed-wheel, sdist-derived, image, and deployed evidence are distinct subjects.",
            "Partial or unqualified support domains require separate project qualification.",
            "Profile structure and slice projections are views over generic BBK objects, not second sources of truth.",
        ],
    }


def gate_plan_command(args: argparse.Namespace) -> dict[str, Any]:
    return resolve(args)["gate_plan"]


def syntax_check(args: argparse.Namespace) -> dict[str, Any]:
    root = find_python_root(Path(args.root or Path.cwd()))
    scope = list(args.path or [])
    if not scope:
        metadata = project_metadata(root)
        scope = list(metadata.get("source_roots", ["."]))
    scan = {"extensions": [".py", ".pyi"], "exclude_globs": [".git/**", ".venv/**", "venv/**", "build/**", "dist/**", "__pycache__/**"], "max_files": 10000}
    files = expand_scope_files(root, scope, scan)
    results = []
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec", ast.PyCF_ONLY_AST, dont_inherit=True)
            results.append({"path": relpath(path, root), "status": "PASS"})
        except (SyntaxError, UnicodeDecodeError, OSError) as exc:
            results.append({"path": relpath(path, root), "status": "FAIL", "error": str(exc)})
    status = "PASS" if files and all(item["status"] == "PASS" for item in results) else ("BLOCKED" if not files else "FAIL")
    payload = {"schema": "bbk.python-syntax-check.v1", "root": str(root), "scope_paths": scope, "status": status, "file_count": len(files), "results": results}
    payload["digest"] = sha256_bytes(canonical_bytes(payload))
    return payload


DEFAULT_BBK_MINIMUM = str(PROFILE["requires"]["bbk_minimum"])


def effective_bbk_version() -> str:
    return os.environ.get("BBK_CORE_VERSION") or DEFAULT_BBK_MINIMUM


STRUCTURE_CONTRACT_DIALECT = "0.1.0-alpha.4"


def _parse_bbk_version(value: str) -> tuple[tuple[int, int, int], tuple[str, tuple[int, ...]] | None] | None:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:-([A-Za-z]+)(?:\.([0-9.]+))?)?(?:\+[-0-9A-Za-z.]+)?", value.strip())
    if not match:
        return None
    base = tuple(int(match.group(index)) for index in (1, 2, 3))
    label = match.group(4)
    if label is None:
        return base, None
    numeric = tuple(int(part) for part in (match.group(5) or "").split(".") if part)
    return base, (label.lower(), numeric)


def version_supports_structure_contract(value: str) -> bool:
    parsed = _parse_bbk_version(value)
    if parsed is None:
        return False
    base, prerelease = parsed
    introduced_base = (0, 1, 0)
    if base > introduced_base:
        return True
    if base < introduced_base:
        return False
    if prerelease is None:
        return True
    label, numeric = prerelease
    return label == "alpha" and bool(numeric) and numeric[0] >= 4


def _candidate_bbk_roots() -> list[Path]:
    candidates: list[Path] = []
    raw_root = os.environ.get("BBK_CORE_ROOT")
    if raw_root:
        candidates.append(Path(raw_root).expanduser())
    raw_cli = os.environ.get("BBK_CORE_CLI")
    if raw_cli:
        cli = Path(raw_cli).expanduser()
        candidates.extend([cli.parent.parent, cli.parent])
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        key = os.path.normcase(str(resolved))
        if key not in seen:
            seen.add(key)
            unique.append(resolved)
    return unique


def detect_structure_contract_validator() -> dict[str, str]:
    for root in _candidate_bbk_roots():
        schema = root / "schemas" / "bbk-implementation-structure-contract-v1.schema.json"
        cli = root / "tools" / "bbk.py"
        if schema.is_file() and cli.is_file():
            return {
                "status": "AVAILABLE",
                "detail": f"BBK structure-contract capability detected at {root}; schema={schema.name}",
                "source": "capability-detection",
            }
    version = effective_bbk_version()
    if version_supports_structure_contract(version):
        return {
            "status": "AVAILABLE",
            "detail": f"BBK core {version} is compatible with the structure-contract dialect introduced in {STRUCTURE_CONTRACT_DIALECT}",
            "source": "version-fallback",
        }
    return {
        "status": "MISSING",
        "detail": f"BBK core {version} predates or does not declare the structure-contract capability introduced in {STRUCTURE_CONTRACT_DIALECT}",
        "source": "version-fallback",
    }


def no_authority_boundary() -> dict[str, Any]:
    return {
        "may_declare_pass": False,
        "may_expand_work_scope": False,
        "may_grant_tools_or_effects": False,
        "may_reduce_assurance": False,
        "statement": "This profile projection is advisory procedure and comparison evidence only. It does not change the generic BBK object, grant tools or effects, broaden scope, reduce assurance, or declare acceptance, verification, readiness, completion, or release.",
    }


def with_output_digest(value: dict[str, Any], field: str = "output_digest") -> dict[str, Any]:
    result = dict(value)
    result.pop(field, None)
    result[field] = sha256_bytes(canonical_bytes(result))
    return result


def canonical_object_digest(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PythonProfileError(f"{label} must be a JSON object")
    return value


def require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PythonProfileError(f"{label} must be a non-empty string")
    return value


def load_generic_contract(path: Path) -> dict[str, Any]:
    value = require_object(read_json(path), "implementation structure contract")
    if value.get("schema") != "bbk.implementation-structure-contract.v1":
        raise PythonProfileError("contract schema must be bbk.implementation-structure-contract.v1")
    for key in ("contractId", "revision", "title", "status", "subject", "applicability", "structure", "decisions", "review"):
        if key not in value:
            raise PythonProfileError(f"contract is missing required field: {key}")
    require_nonempty_string(value.get("contractId"), "contractId")
    require_nonempty_string(str(value.get("revision", "")), "revision")
    subject = require_object(value.get("subject"), "contract subject")
    require_nonempty_string(subject.get("kind"), "contract subject.kind")
    applicability_value = require_object(value.get("applicability"), "contract applicability")
    if applicability_value.get("level") not in {"none", "inline", "contract"}:
        raise PythonProfileError("contract applicability.level must be none, inline, or contract")
    structure_value = require_object(value.get("structure"), "contract structure")
    for key in ("artifactTopology", "keyContracts", "behaviorPaths", "stateOwnership", "effectBoundaries", "testSeams"):
        if not isinstance(structure_value.get(key), list):
            raise PythonProfileError(f"contract structure.{key} must be an array")
    decisions = require_object(value.get("decisions"), "contract decisions")
    for key in ("fixed", "delegated", "prohibited"):
        if not isinstance(decisions.get(key), list):
            raise PythonProfileError(f"contract decisions.{key} must be an array")
    return value


def load_execution_slice(path: Path) -> dict[str, Any]:
    value = require_object(read_json(path), "execution slice")
    if value.get("schema") != "bbk.execution-slice.v1":
        raise PythonProfileError("slice schema must be bbk.execution-slice.v1")
    for key in ("sliceId", "title", "status", "parentCapabilityRefs", "structureContractRefs", "objective", "touchpoint", "flow", "workUnitRefs", "integrationOwner", "assertions", "entryConditions", "exitConditions", "atomicity", "scaffolding"):
        if key not in value:
            raise PythonProfileError(f"slice is missing required field: {key}")
    require_nonempty_string(value.get("sliceId"), "sliceId")
    touchpoint = require_object(value.get("touchpoint"), "slice touchpoint")
    for key in ("kind", "actor", "interaction", "expectedObservation", "environment"):
        require_nonempty_string(touchpoint.get(key), f"slice touchpoint.{key}")
    atomicity = require_object(value.get("atomicity"), "slice atomicity")
    for key in ("coherent", "reviewable", "independentlyVerifiable", "containedOrReversible"):
        if not isinstance(atomicity.get(key), bool):
            raise PythonProfileError(f"slice atomicity.{key} must be boolean")
    return value


def generic_input_record(kind: str, value: dict[str, Any], path: Path) -> dict[str, Any]:
    if kind == "implementation-structure-contract":
        object_id = value["contractId"]
        revision: str | None = str(value.get("revision"))
    else:
        object_id = value["sliceId"]
        metadata = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
        revision = str(metadata.get("revision")) if metadata.get("revision") is not None else None
    return {
        "kind": kind,
        "id": object_id,
        "revision": revision,
        "digest": canonical_object_digest(value),
        "path": str(path.resolve()),
    }


def contract_applicability(contract: dict[str, Any], disposition: str = "PROJECTED") -> dict[str, Any]:
    value = contract.get("applicability", {})
    return {
        "level": value.get("level", "none"),
        "disposition": disposition,
        "rationale": str(value.get("rationale", "")),
        "triggers": sorted(str(item) for item in value.get("triggers", [])),
    }


def safe_preflight(root_arg: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return preflight(root_arg, run_tools=False), []
    except PythonProfileError as exc:
        return None, [str(exc)]


def python_artifact_kind(item: dict[str, Any]) -> str:
    path = str(item.get("logicalPath", "")).replace("\\", "/").lower()
    declared = str(item.get("kind", "artifact")).lower()
    if path.endswith("pyproject.toml"):
        return "distribution"
    if path.endswith("/py.typed") or path == "py.typed":
        return "py-typed-marker"
    if path.endswith(".pyi"):
        return "stub-module"
    if path.endswith("/__init__.py"):
        return "package-surface"
    if "/migrations/" in f"/{path}" or "migration" in declared:
        return "migration"
    if path.endswith((".c", ".cc", ".cpp", ".h", ".so", ".pyd", ".dll", ".dylib")) or "native" in declared:
        return "native-extension"
    if "test" in declared or "/tests/" in f"/{path}" or path.startswith("tests/"):
        return "test"
    if "adapter" in declared:
        return "adapter-module"
    if path.endswith(".py"):
        return "python-module"
    return declared or "artifact"


def classify_key_contract(item: dict[str, Any]) -> dict[str, Any]:
    kind = str(item.get("kind", "contract")).lower()
    name = str(item.get("name", ""))
    shape = str(item.get("shape", ""))
    text = f"{kind} {name} {shape}".lower()
    if any(token in text for token in ("enum", "state", "order", "status", "outcome")):
        concept = "enum-state"
    elif any(token in text for token in ("protocol", "port", "repository", "consumer")):
        concept = "protocol-seam"
    elif any(token in text for token in ("typeddict", "mapping", "payload", "message")):
        concept = "typed-mapping"
    elif any(token in text for token in ("schema", "validated", "external", "json", "request")):
        concept = "runtime-schema-or-value-object"
    elif any(token in text for token in ("error", "failure", "exception", "result")):
        concept = "exception-or-result-disposition"
    else:
        concept = "dataclass-or-domain-value"
    runtime_validation = item.get("visibility") in {"external"} or any(token in text for token in ("external", "json", "wire", "schema", "untrusted"))
    return {
        "contract_id": item.get("id"),
        "name": name,
        "kind": kind,
        "visibility": item.get("visibility"),
        "shape": shape,
        "responsibility": item.get("responsibility"),
        "invariants": item.get("invariants", []),
        "failure_semantics": item.get("failureSemantics", []),
        "source_refs": item.get("sourceRefs", []),
        "python_type_concept": concept,
        "runtime_validation_required": bool(runtime_validation),
        "reason": "Protect the declared invariant or boundary; static annotations alone do not establish runtime truth." if runtime_validation else "Use the least powerful Python form that preserves the declared invariant and boundary.",
    }


def structure_selected_skills(contract: dict[str, Any], role: str) -> list[str]:
    values = ["bbk-python"]
    if role in {"reviewer", "validator"}:
        values.append("python-implementation-structure-review")
    else:
        values.append("python-implementation-structure-authoring")
    structure_value = contract.get("structure", {})
    contracts = structure_value.get("keyContracts", [])
    combined = " ".join(
        str(value)
        for item in contracts
        for value in (item.get("kind", ""), item.get("name", ""), item.get("shape", ""), item.get("visibility", ""))
    ).lower()
    artifacts = " ".join(str(item.get("logicalPath", "")) for item in structure_value.get("artifactTopology", [])).lower()
    triggers = {str(item).lower() for item in contract.get("applicability", {}).get("triggers", [])}
    if any(item.get("visibility") in {"public", "shared", "external"} for item in contracts) or triggers & {"public-api", "public-interface", "packaging", "consumer-shape"}:
        values.extend(["python-api-package-boundary-review", "python-typing-contract-review"])
    if structure_value.get("stateOwnership") or triggers & {"state-ownership", "concurrency", "cancellation", "recovery", "persistence"}:
        values.append("python-runtime-correctness-review")
    if any(item.get("runtime_validation_required") for item in map(classify_key_contract, contracts)) or triggers & {"runtime-validation", "external-boundary", "serialization"}:
        values.append("python-security-supply-chain-review")
    if "migration" in artifacts or structure_value.get("migrationTouchpoints") or triggers & {"migration", "persistence"}:
        values.extend(["python-operational-readiness-review", "python-test-strategy-review"])
    if structure_value.get("effectBoundaries") or triggers & {"effect-boundary", "security", "external-boundary"}:
        values.extend(["python-runtime-correctness-review", "python-security-supply-chain-review"])
    if any(token in artifacts or token in combined for token in ("native", "ffi", "abi3", "pyo3", "c-api")):
        values.append("python-native-extension-review")
    return list(dict.fromkeys(values))


def structure_planned_gates(contract: dict[str, Any], role: str) -> list[str]:
    gates = ["python-generic-structure-contract-validate", "python-structure-projection-validate"]
    structure_value = contract.get("structure", {})
    contracts = structure_value.get("keyContracts", [])
    triggers = {str(item).lower() for item in contract.get("applicability", {}).get("triggers", [])}
    if any(item.get("visibility") in {"public", "shared", "external"} for item in contracts):
        gates.append("python-public-shared-contract-drift")
    if structure_value.get("stateOwnership") or triggers & {"state-ownership", "concurrency", "cancellation", "recovery", "persistence"}:
        gates.append("python-state-ownership-drift")
    if role in {"reviewer", "validator"} or contract.get("applicability", {}).get("level") == "contract":
        gates.append("python-planned-actual-structure-compare")
    paths = " ".join(str(item.get("logicalPath", "")) for item in structure_value.get("artifactTopology", [])).lower()
    if any(token in paths for token in ("pyproject.toml", "dist/", "wheel", "sdist")):
        gates.extend(["python-build-distributions", "python-installed-wheel-tests", "python-package-contents"])
    if structure_value.get("migrationTouchpoints"):
        gates.append("python-migration-rollback")
    if structure_value.get("effectBoundaries"):
        gates.append("python-security-boundary")
    return list(dict.fromkeys(gates))


def structure_projection_value(contract: dict[str, Any], contract_path: Path, root_arg: Path, role: str, task_profile: str, tier: str) -> dict[str, Any]:
    input_record = generic_input_record("implementation-structure-contract", contract, contract_path)
    subject_kind = str(contract.get("subject", {}).get("kind", "unknown"))
    level = contract.get("applicability", {}).get("level", "none")
    preflight_value: dict[str, Any] | None = None
    unsupported: list[str] = []
    advisories: list[str] = []
    blockers: list[str] = []
    disposition = "PROJECTED"
    python_subjects: list[str] = []
    if level == "none":
        disposition = "NOT_APPLICABLE"
    elif subject_kind not in {"software", "mixed", "software-and-procedure", "application", "library", "service"}:
        disposition = "UNSUPPORTED"
        unsupported.append(f"subject kind {subject_kind!r} is outside the Python profile projection")
    else:
        preflight_value, errors = safe_preflight(root_arg)
        if errors:
            disposition = "PARTIAL"
            unsupported.extend(errors)
            advisories.append("Projection was produced from the generic contract without repository preflight; repository-dependent claims remain uncertain.")
        else:
            project = preflight_value.get("project", {})
            packaging = preflight_value.get("packaging", {})
            python_subjects.extend(["source-tree"])
            if project.get("name"):
                python_subjects.append(f"distribution:{project['name']}")
            if packaging.get("packages", {}).get("packages"):
                python_subjects.extend(f"package:{name}" for name in packaging["packages"]["packages"])
            if project.get("build_backend"):
                python_subjects.extend(["editable-install", "wheel", "sdist-derived-wheel"])
            if project.get("scripts") or project.get("entry_point_groups"):
                python_subjects.append("installed-entry-points")
    structure_value = contract.get("structure", {})
    contracts = [classify_key_contract(item) for item in structure_value.get("keyContracts", [])]
    runtime_boundaries = [
        {
            "contract_id": item["contract_id"],
            "name": item["name"],
            "static_contract": "annotation/type-checker",
            "runtime_contract": "explicit parser, constructor invariant, validation library, or boundary check",
            "operational_evidence": "consumer or environment evidence remains separate",
        }
        for item in contracts if item.get("runtime_validation_required")
    ]
    projection = {
        "subject_kind": subject_kind,
        "python_subjects": list(dict.fromkeys(python_subjects)),
        "artifact_topology": [
            {
                "artifact_id": item.get("id"), "logical_path": item.get("logicalPath"),
                "generic_kind": item.get("kind"), "python_kind": python_artifact_kind(item),
                "action": item.get("action"), "owner": item.get("owner"),
                "responsibility": item.get("responsibility"),
            }
            for item in structure_value.get("artifactTopology", [])
        ],
        "key_contracts": contracts,
        "type_strategy": contracts,
        "runtime_validation_boundaries": runtime_boundaries,
        "ownership": [
            {
                "state": item.get("state"), "owner": item.get("owner"), "lifetime": item.get("lifetime"),
                "mutation_authority": item.get("mutationAuthority"), "consistency": item.get("consistency"),
                "concurrency": item.get("concurrency", ""), "recovery": item.get("recovery"),
                "python_guidance": "Make resource/task/process/context ownership explicit; type hints do not enforce lifetime or cleanup.",
            }
            for item in structure_value.get("stateOwnership", [])
        ],
        "behavior_paths": [
            {
                "id": item.get("id"), "name": item.get("name"), "trigger": item.get("trigger"),
                "steps": item.get("steps", []), "success": item.get("success"),
                "failure_and_recovery": item.get("failureAndRecovery", []),
                "python_review": ["exception taxonomy", "cancellation and cleanup", "retry/idempotency", "runtime validation", "consumer/package subject"],
            }
            for item in structure_value.get("behaviorPaths", [])
        ],
        "effect_boundaries": [
            {
                "effect": item.get("effect"), "owner": item.get("owner"), "authorization": item.get("authorization"),
                "idempotency": item.get("idempotency"), "failure": item.get("failure"), "recovery": item.get("recovery"),
                "python_guidance": "Bind filesystem, subprocess, network, database, package, credential, and publication effects to an explicit owner and authorization; annotations do not grant effects."
            }
            for item in structure_value.get("effectBoundaries", [])
        ],
        "observability_points": [
            {"id": item.get("id"), "statement": item.get("statement"), "source_refs": item.get("sourceRefs", [])}
            for item in structure_value.get("observabilityPoints", [])
        ],
        "migration_touchpoints": [
            {"id": item.get("id"), "statement": item.get("statement"), "source_refs": item.get("sourceRefs", []),
             "python_guidance": "Bind schema/data transformation, mixed-version behavior, restart, rollback, and installed/deployed package subjects."}
            for item in structure_value.get("migrationTouchpoints", [])
        ],
        "test_seams": [
            {"id": item.get("id"), "statement": item.get("statement"), "source_refs": item.get("sourceRefs", [])}
            for item in structure_value.get("testSeams", [])
        ],
        "review_policy": {
            "assurance_tier": contract.get("review", {}).get("assuranceTier"),
            "required_reviewers": contract.get("review", {}).get("requiredReviewers", []),
            "acceptance_criteria": contract.get("review", {}).get("acceptanceCriteria", []),
            "accepted_by": contract.get("review", {}).get("acceptedBy", []),
            "review_refs": contract.get("review", {}).get("reviewRefs", []),
        },
        "package_subjects": list(dict.fromkeys(python_subjects)),
        "fixed_decisions": contract.get("decisions", {}).get("fixed", []),
        "delegated_freedom": contract.get("decisions", {}).get("delegated", []),
        "prohibited_shortcuts": contract.get("decisions", {}).get("prohibited", []),
        "selected_skills": structure_selected_skills(contract, role) if disposition == "PROJECTED" else ["bbk-python"],
        "planned_gates": structure_planned_gates(contract, role) if disposition == "PROJECTED" else [],
        "profile_input_projection": contract.get("profileProjections", {}).get("python") if isinstance(contract.get("profileProjections"), dict) else None,
    }
    payload = {
        "schema": "bbk.python.implementation-structure-projection.v1",
        "profile": {"id": "python", "version": VERSION},
        "bbk_version": STRUCTURE_CONTRACT_DIALECT,
        "bbk_core_version": effective_bbk_version(),
        "input": input_record,
        "preflight_digest": preflight_value.get("digest") if preflight_value else None,
        "applicability": contract_applicability(contract, disposition),
        "projection": projection,
        "unsupported_or_uncertain": unsupported + [str(item.get("statement")) for item in contract.get("uncertainties", []) if item.get("disposition") in {"blocked", "resolve-before-work"}],
        "advisories": advisories,
        "blockers": blockers,
        "no_authority": no_authority_boundary(),
    }
    return with_output_digest(payload)


def structure_command(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.contract).expanduser().resolve()
    contract = load_generic_contract(path)
    role = normalize_role(args.role)
    tier = args.assurance_tier or str(contract.get("review", {}).get("assuranceTier") or "material")
    if tier not in TIER_RANK:
        raise PythonProfileError(f"unsupported assurance tier: {tier}")
    return structure_projection_value(contract, path, Path(args.root or Path.cwd()), role, args.task_profile or "implementation-structure", tier)


def slice_touchpoint_projection(slice_value: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
    touch = slice_value.get("touchpoint", {})
    kind = str(touch.get("kind", "other"))
    text = " ".join([kind, str(touch.get("interaction", "")), str(touch.get("expectedObservation", "")), slice_value.get("title", ""), slice_value.get("objective", "")]).lower()
    if kind == "package" or any(token in text for token in ("wheel", "sdist", "installed package", "package install")):
        python_kind = "wheel-consumer"
        plan = ["Build the declared distribution subject through the repository backend.", "Install the exact wheel in a clean environment.", "Exercise the declared consumer from outside the checkout and inspect included metadata/resources."]
        skills = ["python-package-release-gates", "python-api-package-boundary-review"]
    elif kind == "cli":
        python_kind = "cli"
        plan = ["Invoke the declared console entry point or module command through its normal installed/import subject.", "Capture exit status, stdout/stderr contract, failure behavior, and cleanup."]
        skills = ["python-api-package-boundary-review"]
    elif kind == "api":
        python_kind = "api"
        plan = ["Invoke the public runtime API through its declared import surface.", "Exercise valid, invalid, and failure outcomes using the supported package subject."]
        skills = ["python-api-package-boundary-review", "python-runtime-correctness-review"]
    elif any(token in text for token in ("async", "cancel", "taskgroup", "await")):
        python_kind = "async-flow"
        plan = ["Observe task creation and ownership.", "Cancel at the declared boundary and prove cleanup, propagation, and result disposition."]
        skills = ["python-runtime-correctness-review", "python-test-strategy-review"]
    elif any(token in text for token in ("process", "multiprocessing", "job", "queue")):
        python_kind = "process-handoff"
        plan = ["Serialize and hand off the declared message through the selected process start method.", "Observe worker failure, timeout, cleanup, and duplicate-work behavior."]
        skills = ["python-runtime-correctness-review", "python-test-strategy-review"]
    elif any(token in text for token in ("plugin", "entry point", "entry-point")):
        python_kind = "plugin-discovery"
        plan = ["Install or expose the declared distribution.", "Discover the exact entry-point group and invoke the plugin through the consumer path."]
        skills = ["python-api-package-boundary-review", "python-test-strategy-review"]
    elif any(token in text for token in ("migration", "schema upgrade", "rollback")):
        python_kind = "migration-rehearsal"
        plan = ["Apply the migration to a bounded realistic fixture.", "Exercise failure and rollback or forward-recovery disposition.", "Compare persisted compatibility and operational evidence."]
        skills = ["python-operational-readiness-review", "python-runtime-correctness-review", "python-test-strategy-review"]
    elif any(token in text for token in ("json", "validation", "schema", "untrusted")):
        python_kind = "runtime-validation"
        plan = ["Feed valid and invalid external data through the actual parser/validator.", "Prove that invalid data cannot become trusted domain state solely because annotations exist."]
        skills = ["python-runtime-correctness-review", "python-security-supply-chain-review", "python-test-strategy-review"]
    else:
        python_kind = "test-or-report"
        plan = ["Exercise the declared observation through the repository's normal Python subject.", "Bind evidence to the exact candidate, interpreter, environment, dependencies, and profile projection."]
        skills = ["python-test-strategy-review"]
    projected = {**touch, "python_kind": python_kind}
    return projected, plan, skills


def slice_projection_value(slice_value: dict[str, Any], slice_path: Path, root_arg: Path, role: str, task_profile: str, tier: str, contract_path: Path | None = None) -> dict[str, Any]:
    input_record = generic_input_record("execution-slice", slice_value, slice_path)
    preflight_value, errors = safe_preflight(root_arg)
    disposition = "PROJECTED" if not errors else "PARTIAL"
    projected_touch, inspection_plan, skills = slice_touchpoint_projection(slice_value)
    contract: dict[str, Any] | None = None
    if contract_path:
        contract = load_generic_contract(contract_path)
    dependency_closure: list[str] = []
    dependency_closure.extend(str(item) for item in slice_value.get("structureContractRefs", []))
    dependency_closure.extend(str(item) for item in slice_value.get("workUnitRefs", []))
    flow = slice_value.get("flow", {})
    for key in ("architectureRefs", "interfaceRefs", "participants"):
        dependency_closure.extend(str(item) for item in flow.get(key, []))
    dependency_closure.extend(str(item.get("id")) for item in slice_value.get("scaffolding", []) if item.get("id"))
    if contract:
        dependency_closure.extend(str(item.get("logicalPath")) for item in contract.get("structure", {}).get("artifactTopology", []) if item.get("logicalPath"))
        dependency_closure.extend(str(item.get("id")) for item in contract.get("structure", {}).get("keyContracts", []) if item.get("id"))
    atomicity = slice_value.get("atomicity", {})
    participants = flow.get("participants", [])
    metadata = slice_value.get("metadata") if isinstance(slice_value.get("metadata"), dict) else {}
    foundation = bool(metadata.get("foundationException") or metadata.get("foundation_exception"))
    integrated = len(participants) >= 2 or projected_touch["python_kind"] in {"wheel-consumer", "cli", "api", "plugin-discovery", "async-flow", "process-handoff", "migration-rehearsal", "runtime-validation"}
    horizontal_status = "FOUNDATION_EXCEPTION" if foundation else ("INTEGRATED" if integrated else "ADVISORY_HORIZONTAL")
    advisories: list[str] = []
    if horizontal_status == "ADVISORY_HORIZONTAL":
        advisories.append("The declared touchpoint appears weakly integrated. Add a real consumer/runtime/package observation or document a bounded foundation exception and the next integrated slice it enables.")
    if not all(bool(atomicity.get(key)) for key in ("coherent", "reviewable", "independentlyVerifiable", "containedOrReversible")):
        advisories.append("One or more generic slice atomicity properties are false; the slice should be revised or explicitly blocked before execution.")
    gates = ["python-slice-touchpoint-evidence", "python-scaffolding-disposition"]
    if projected_touch["python_kind"] == "wheel-consumer":
        gates.extend(["python-build-distributions", "python-installed-wheel-tests", "python-package-contents"])
    elif projected_touch["python_kind"] == "async-flow":
        gates.append("python-async-cancellation")
    elif projected_touch["python_kind"] == "process-handoff":
        gates.append("python-process-start-methods")
    elif projected_touch["python_kind"] == "migration-rehearsal":
        gates.append("python-migration-rollback")
    selected = ["bbk-python", "python-execution-slice-design", *skills]
    if role in {"reviewer", "validator", "verification-designer"}:
        selected.append("python-test-strategy-review")
    payload = {
        "schema": "bbk.python.execution-slice-projection.v1",
        "profile": {"id": "python", "version": VERSION},
        "bbk_version": STRUCTURE_CONTRACT_DIALECT,
        "bbk_core_version": effective_bbk_version(),
        "input": input_record,
        "preflight_digest": preflight_value.get("digest") if preflight_value else None,
        "applicability": {"level": "contract" if slice_value.get("structureContractRefs") else "inline", "disposition": disposition, "rationale": str(slice_value.get("atomicity", {}).get("rationale", "")), "triggers": ["execution-slicing"]},
        "projection": {
            "objective": slice_value.get("objective"),
            "flow": flow,
            "entry_conditions": slice_value.get("entryConditions", []),
            "exit_conditions": slice_value.get("exitConditions", []),
            "atomicity": atomicity,
            "integration_owner": slice_value.get("integrationOwner"),
            "assertions": slice_value.get("assertions", []),
            "touchpoint": projected_touch,
            "inspection_plan": inspection_plan,
            "dependency_closure": list(dict.fromkeys(dependency_closure)),
            "candidate_boundary": {"strategy": "single-coherent-candidate", "work_unit_refs": slice_value.get("workUnitRefs", []), "reason": "Keep the declared integrated touchpoint, repair, and rollback attributable to one coherent candidate unless the generic plan explicitly defines a tightly coupled cohort."},
            "validation_boundary": {"strategy": "assertion-scoped", "assertions": slice_value.get("assertions", []), "integration_owner": slice_value.get("integrationOwner"), "evidence_subject": projected_touch["python_kind"]},
            "scaffolding": [{**item, "python_risk": "Do not let test-only imports, editable installs, fake plugins, fixture queues, or migration snapshots become accidental production dependencies."} for item in slice_value.get("scaffolding", [])],
            "horizontal_sequence_assessment": {"status": horizontal_status, "foundation_exception": foundation, "integrated_participant_count": len(participants), "next_slice_required": bool(foundation)},
            "selected_skills": list(dict.fromkeys(selected)),
            "planned_gates": list(dict.fromkeys(gates)),
            "profile_input_projection": slice_value.get("profileProjections", {}).get("python") if isinstance(slice_value.get("profileProjections"), dict) else None,
        },
        "unsupported_or_uncertain": errors,
        "advisories": advisories,
        "blockers": [],
        "no_authority": no_authority_boundary(),
    }
    return with_output_digest(payload)


def slice_command(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.slice).expanduser().resolve()
    value = load_execution_slice(path)
    tier = args.assurance_tier or "material"
    if tier not in TIER_RANK:
        raise PythonProfileError(f"unsupported assurance tier: {tier}")
    contract_path = Path(args.contract).expanduser().resolve() if getattr(args, "contract", None) else None
    return slice_projection_value(value, path, Path(args.root or Path.cwd()), normalize_role(args.role), args.task_profile or "execution-slicing", tier, contract_path)


def ast_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = ast_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Subscript):
        return ast_name(node.value)
    return ""


def literal_string_list(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = []
        for item in node.elts:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                values.append(item.value)
        return values
    return []


def derive_actual_inventory(root_arg: Path) -> dict[str, Any]:
    root = find_python_root(root_arg)
    pf = preflight(root, run_tools=False)
    metadata = pf.get("project", {})
    artifacts: list[dict[str, Any]] = []
    contracts: list[dict[str, Any]] = []
    ownership: list[dict[str, Any]] = []
    source_roots = metadata.get("source_roots", ["."])
    scan = {"extensions": [".py", ".pyi", ".c", ".h", ".cpp", ".cc"], "exclude_globs": [".git/**", ".venv/**", "venv/**", "build/**", "dist/**", "__pycache__/**"], "max_files": 10000}
    files = expand_scope_files(root, source_roots, scan)
    for path in files:
        rel = relpath(path, root)
        suffix = path.suffix.lower()
        if suffix in {".c", ".h", ".cpp", ".cc"}:
            artifacts.append({"path": rel, "kind": "native-extension-source", "visibility": "internal"})
            continue
        kind = "stub-module" if suffix == ".pyi" else ("test" if rel.startswith("tests/") or "/tests/" in rel else ("package-surface" if path.name == "__init__.py" else "python-module"))
        artifacts.append({"path": rel, "kind": kind, "visibility": "public-candidate" if path.name in {"__init__.py", "__main__.py"} or suffix == ".pyi" else "internal"})
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        explicit_exports: set[str] = set()
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
                    explicit_exports.update(literal_string_list(node.value))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                bases = {ast_name(base).split(".")[-1] for base in node.bases}
                decorators = {ast_name(dec).split(".")[-1] for dec in node.decorator_list}
                if "Protocol" in bases:
                    ckind = "protocol"
                elif "TypedDict" in bases:
                    ckind = "typed-mapping"
                elif "Enum" in bases or "StrEnum" in bases or "IntEnum" in bases:
                    ckind = "enum-state"
                elif "ABC" in bases:
                    ckind = "abstract-base"
                elif "dataclass" in decorators:
                    ckind = "dataclass-value"
                else:
                    ckind = "class"
                visibility = "public" if node.name in explicit_exports or not node.name.startswith("_") else "private"
                contracts.append({"name": node.name, "kind": ckind, "path": rel, "visibility": visibility})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visibility = "public" if node.name in explicit_exports or not node.name.startswith("_") else "private"
                contracts.append({"name": node.name, "kind": "async-function" if isinstance(node, ast.AsyncFunctionDef) else "function", "path": rel, "visibility": visibility})
    for marker in pf.get("packaging", {}).get("packages", {}).get("py_typed", []):
        artifacts.append({"path": marker, "kind": "py-typed-marker", "visibility": "public"})
    for name, target in metadata.get("scripts", {}).items():
        contracts.append({"name": name, "kind": "console-entry-point", "target": target, "visibility": "external"})
    for group in metadata.get("entry_point_groups", []):
        contracts.append({"name": group, "kind": "plugin-entry-point-group", "visibility": "external"})
    inventory = {
        "schema": "bbk.python.actual-structure-inventory.v1",
        "root": str(root),
        "source": "derived-static",
        "preflight_digest": pf["digest"],
        "artifacts": sorted(artifacts, key=lambda item: (str(item.get("path", "")), str(item.get("kind", "")))),
        "contracts": sorted(contracts, key=lambda item: (str(item.get("name", "")), str(item.get("path", "")))),
        "ownership": ownership,
        "fixed_decision_evidence": [],
        "delegated_differences": [],
        "limitations": [
            "Static inventory does not import or execute the project and cannot prove runtime validation, state ownership, cancellation, process behavior, persistence, native ABI, or operational correctness.",
            "Public visibility inferred from naming or __all__ is advisory; generated exports and framework behavior may require project-specific evidence.",
        ],
    }
    inventory["digest"] = canonical_object_digest(inventory)
    return inventory


def normalize_actual_inventory(value: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    if value.get("schema") != "bbk.python.actual-structure-inventory.v1":
        raise PythonProfileError("actual inventory schema must be bbk.python.actual-structure-inventory.v1")
    for key in ("artifacts", "contracts", "ownership", "fixed_decision_evidence", "delegated_differences", "limitations"):
        if not isinstance(value.get(key), list):
            raise PythonProfileError(f"actual inventory {key} must be an array")
    result = dict(value)
    result["source"] = "supplied" if path else value.get("source", "derived-static")
    result.pop("digest", None)
    result["digest"] = canonical_object_digest(result)
    return result


def candidate_identity(value: dict[str, Any], path: Path) -> dict[str, Any]:
    digest = value.get("manifest_content_sha256") or value.get("content_sha256") or value.get("root_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        digest = canonical_object_digest(value)
    files = []
    for item in value.get("files", []):
        if isinstance(item, dict) and item.get("path"):
            files.append(str(item["path"]).replace("\\", "/").lstrip("./"))
    return {"schema": value.get("schema"), "id": value.get("candidate_id") or value.get("candidateId") or value.get("id"), "digest": digest, "path": str(path.resolve()), "files": sorted(set(files))}


def comparison_with_digest(value: dict[str, Any]) -> dict[str, Any]:
    return with_output_digest(value)


def compare_planned_actual(contract: dict[str, Any], contract_digest: str, candidate: dict[str, Any], inventory: dict[str, Any]) -> dict[str, Any]:
    actual_paths = {str(item.get("path", "")).replace("\\", "/").lstrip("./") for item in inventory.get("artifacts", []) if item.get("path")}
    actual_paths.update(candidate.get("files", []))
    actual_contracts = {str(item.get("name")) for item in inventory.get("contracts", []) if item.get("name")}
    artifact_diffs: list[dict[str, Any]] = []
    contract_diffs: list[dict[str, Any]] = []
    fixed_diffs: list[dict[str, Any]] = []
    delegated_diffs: list[dict[str, Any]] = list(inventory.get("delegated_differences", []))
    ownership_diffs: list[dict[str, Any]] = []
    unknowns: list[str] = []
    blocking_unknowns: list[str] = []
    structure_value = contract.get("structure", {})
    for item in structure_value.get("artifactTopology", []):
        path = str(item.get("logicalPath", "")).replace("\\", "/").lstrip("./")
        action = item.get("action")
        if action in {"create", "modify", "retain", "inspect"} and path and path not in actual_paths:
            publicish = path.endswith(("/__init__.py", ".pyi", "/py.typed", "pyproject.toml")) or python_artifact_kind(item) in {"distribution", "py-typed-marker", "stub-module", "package-surface", "migration", "native-extension"}
            artifact_diffs.append({"planned_ref": item.get("id"), "path": path, "kind": "missing-planned-artifact", "class": "material" if publicish else "advisory", "evidence": "path absent from candidate manifest and actual inventory"})
    for item in structure_value.get("keyContracts", []):
        name = str(item.get("name", ""))
        visibility = item.get("visibility")
        if name and name not in actual_contracts:
            if visibility in {"public", "shared", "external"}:
                contract_diffs.append({"planned_ref": item.get("id"), "name": name, "kind": "missing-shared-contract", "class": "material", "evidence": "named contract absent from supplied/derived inventory"})
            else:
                unknowns.append(f"Private/internal contract {item.get('id')} ({name}) was not identified statically; this may be within delegated implementation freedom.")
    evidence_by_id = {str(item.get("decision_id") or item.get("decisionId") or item.get("id")): item for item in inventory.get("fixed_decision_evidence", [])}
    for decision in contract.get("decisions", {}).get("fixed", []):
        decision_id = str(decision.get("id"))
        evidence = evidence_by_id.get(decision_id)
        if not evidence:
            statement = f"No direct actual evidence was supplied for fixed decision {decision_id}; static inventory cannot prove prose-level ownership or behavior."
            unknowns.append(statement)
            blocking_unknowns.append(statement)
            continue
        status = str(evidence.get("status", "unknown")).lower()
        if status in {"diverges", "divergent", "material-divergence", "fail"}:
            fixed_diffs.append({"planned_ref": decision_id, "kind": "fixed-decision-divergence", "class": "material", "evidence": str(evidence.get("evidence", "supplied divergence")), "actual": evidence.get("actual")})
        elif status not in {"conforms", "conformant", "pass"}:
            unknowns.append(f"Fixed decision {decision_id} evidence is {status!r}, not a conformance or divergence result.")
    owner_evidence = {(str(item.get("state")), str(item.get("planned_owner") or item.get("plannedOwner"))): item for item in inventory.get("ownership", [])}
    for owner in structure_value.get("stateOwnership", []):
        key = (str(owner.get("state")), str(owner.get("owner")))
        evidence = owner_evidence.get(key)
        if not evidence:
            statement = f"No ownership evidence supplied for state {key[0]!r} owned by {key[1]!r}; static inventory cannot prove runtime state, resource, task, process, or effect ownership."
            unknowns.append(statement)
            blocking_unknowns.append(statement)
            continue
        status = str(evidence.get("status", "unknown")).lower()
        actual_owner = evidence.get("actual_owner") or evidence.get("actualOwner")
        if status in {"diverges", "material-divergence", "fail"} or (actual_owner and str(actual_owner) != key[1]):
            ownership_diffs.append({"planned_ref": key[0], "planned_owner": key[1], "actual_owner": actual_owner, "kind": "ownership-divergence", "class": "material", "evidence": str(evidence.get("evidence", "supplied ownership divergence"))})
    all_diffs = artifact_diffs + contract_diffs + fixed_diffs + ownership_diffs
    material = sum(1 for item in all_diffs if item.get("class") == "material")
    advisory = sum(1 for item in all_diffs if item.get("class") == "advisory") + len(delegated_diffs)
    return comparison_with_digest({
        "schema": "bbk.python.planned-actual-structure-comparison.v1",
        "contract_id": contract["contractId"],
        "contract_revision": str(contract["revision"]),
        "contract_digest": contract_digest,
        "candidate_digest": candidate["digest"],
        "inventory_digest": inventory["digest"],
        "artifact_differences": artifact_diffs,
        "contract_differences": contract_diffs,
        "fixed_decision_differences": fixed_diffs,
        "delegated_differences": delegated_diffs,
        "ownership_differences": ownership_diffs,
        "unknowns": unknowns,
        "blocking_unknowns": blocking_unknowns,
        "material_difference_count": material,
        "advisory_difference_count": advisory,
    })


def structure_review_command(args: argparse.Namespace) -> dict[str, Any]:
    contract_path = Path(args.contract).expanduser().resolve()
    candidate_path = Path(args.candidate).expanduser().resolve()
    contract = load_generic_contract(contract_path)
    candidate_value = require_object(read_json(candidate_path), "candidate manifest")
    candidate = candidate_identity(candidate_value, candidate_path)
    subject_kind = str(contract.get("subject", {}).get("kind", "unknown"))
    level = contract.get("applicability", {}).get("level", "none")
    preflight_value: dict[str, Any] | None = None
    unsupported: list[str] = []
    advisories: list[str] = []
    blockers: list[str] = []
    if args.actual_inventory:
        inventory_path = Path(args.actual_inventory).expanduser().resolve()
        inventory = normalize_actual_inventory(require_object(read_json(inventory_path), "actual inventory"), inventory_path)
    else:
        try:
            inventory = derive_actual_inventory(Path(args.root or Path.cwd()))
            preflight_value = preflight(Path(args.root or Path.cwd()), run_tools=False)
        except PythonProfileError as exc:
            inventory = {"schema": "bbk.python.actual-structure-inventory.v1", "root": str(Path(args.root or Path.cwd()).resolve()), "source": "derived-static", "preflight_digest": None, "artifacts": [], "contracts": [], "ownership": [], "fixed_decision_evidence": [], "delegated_differences": [], "limitations": [str(exc)]}
            inventory["digest"] = canonical_object_digest(inventory)
            blockers.append(str(exc))
    comparison = compare_planned_actual(contract, canonical_object_digest(contract), candidate, inventory)
    blockers.extend(comparison.get("blocking_unknowns", []))
    findings: list[dict[str, Any]] = []
    index = 1
    for group, affected in (
        (comparison["artifact_differences"], "artifact topology or package subject"),
        (comparison["contract_differences"], "public/shared contract"),
        (comparison["fixed_decision_differences"], "fixed decision"),
        (comparison["ownership_differences"], "state or effect owner"),
    ):
        for item in group:
            findings.append({
                "id": f"PY-STRUCT-{index:03d}",
                "class": "material" if item.get("class") == "material" else "advisory",
                "planned_ref": str(item.get("planned_ref", "unknown")),
                "statement": str(item.get("kind", "planned/actual divergence")).replace("-", " "),
                "actual_evidence": str(item.get("evidence", item)),
                "affected_contract_or_owner": affected,
                "route": "contract impact review before candidate acceptance" if item.get("class") == "material" else "record or reconcile at the next safe contract refresh",
            })
            index += 1
    for statement in comparison.get("blocking_unknowns", []):
        findings.append({
            "id": f"PY-STRUCT-{index:03d}", "class": "blocker", "planned_ref": "evidence-gap",
            "statement": "Insufficient evidence for a governed fixed decision or ownership boundary.",
            "actual_evidence": statement, "affected_contract_or_owner": "fixed decision or state/effect owner",
            "route": "supply exact evidence or keep candidate acceptance blocked"
        })
        index += 1
    for item in comparison["delegated_differences"]:
        findings.append({
            "id": f"PY-STRUCT-{index:03d}", "class": "observation", "planned_ref": str(item.get("area") or item.get("planned_ref") or "delegated-freedom"),
            "statement": "Difference is reported inside delegated freedom and is not a material conformance failure unless independent quality evidence shows otherwise.",
            "actual_evidence": str(item.get("evidence", item)), "affected_contract_or_owner": "delegated implementation detail", "route": "no blocking route; retain as observation or advisory"
        })
        index += 1
    if level == "none" or subject_kind not in {"software", "mixed", "software-and-procedure", "application", "library", "service"}:
        disposition = "NOT_APPLICABLE"
        app_disposition = "NOT_APPLICABLE" if level == "none" else "UNSUPPORTED"
        if subject_kind not in {"software", "mixed", "software-and-procedure", "application", "library", "service"}:
            unsupported.append(f"subject kind {subject_kind!r} is outside the Python profile")
    elif blockers:
        disposition = "BLOCKED"
        app_disposition = "BLOCKED"
    elif comparison["material_difference_count"]:
        disposition = "MATERIAL_DIVERGENCE"
        app_disposition = "PROJECTED"
    elif comparison["advisory_difference_count"]:
        disposition = "ADVISORY_DIVERGENCE"
        app_disposition = "PROJECTED"
    else:
        disposition = "CONFORMS"
        app_disposition = "PROJECTED"
    payload = {
        "schema": "bbk.python.structure-review-result.v1",
        "profile": {"id": "python", "version": VERSION},
        "bbk_version": STRUCTURE_CONTRACT_DIALECT,
        "bbk_core_version": effective_bbk_version(),
        "input": generic_input_record("implementation-structure-contract", contract, contract_path),
        "preflight_digest": preflight_value.get("digest") if preflight_value else inventory.get("preflight_digest"),
        "applicability": contract_applicability(contract, app_disposition),
        "candidate": candidate,
        "inventory": {"schema": inventory.get("schema"), "source": inventory.get("source"), "digest": inventory.get("digest"), "artifact_count": len(inventory.get("artifacts", [])), "contract_count": len(inventory.get("contracts", [])), "limitations": inventory.get("limitations", [])},
        "comparison": comparison,
        "disposition": disposition,
        "coverage": ["public/shared package and import shape", "named key contracts", "supplied fixed-decision evidence", "supplied state/ownership evidence", "delegated private differences"],
        "findings": findings,
        "limitations": inventory.get("limitations", []) + ["CONFORMS is a bounded comparison disposition, not a verification, readiness, completion, or release pass."],
        "unsupported_or_uncertain": unsupported + comparison.get("unknowns", []),
        "advisories": advisories,
        "blockers": blockers,
        "no_authority": no_authority_boundary(),
    }
    return with_output_digest(payload)

def human(value: dict[str, Any]) -> str:
    schema = value.get("schema")
    if schema == "bbk.python-preflight.v1":
        return f"Python preflight: {value['root']}\nProject: {value['project'].get('name')}\nInterpreter: {value['interpreter']['implementation']} {value['interpreter']['version']}\nPackages: {len(value['packaging']['packages']['packages'])}\nDigest: {value['digest']}"
    if schema == "bbk.python-profile-resolution.v1":
        items = ", ".join(item["id"] for item in value["selected_components"])
        return f"Python profile resolution\nRole: {value['inputs']['role']}\nTier: {value['inputs']['assurance_tier']}\nComponents: {items}\nGates: {len(value['gate_plan']['selected'])}\nEffective digest: {value['effective_sha256']}"
    if schema == "bbk.python-gate-plan.v1":
        return "\n".join([f"Python gate plan ({value['tier']}):", *[f"- {item['id']} [{item['planning_status']}]" for item in value["selected"]], f"Digest: {value['digest']}"])
    if schema == "bbk.python-syntax-check.v1":
        return f"Python syntax check: {value['status']} ({value['file_count']} files)\nDigest: {value['digest']}"
    if schema == "bbk.python.implementation-structure-projection.v1":
        return f"Python structure projection: {value['applicability']['disposition']}\nContract: {value['input']['id']}@{value['input']['revision']}\nArtifacts: {len(value['projection']['artifact_topology'])}\nContracts: {len(value['projection']['key_contracts'])}\nDigest: {value['output_digest']}"
    if schema == "bbk.python.execution-slice-projection.v1":
        return f"Python execution-slice projection: {value['applicability']['disposition']}\nSlice: {value['input']['id']}\nTouchpoint: {value['projection']['touchpoint']['python_kind']}\nDigest: {value['output_digest']}"
    if schema == "bbk.python.structure-review-result.v1":
        return f"Python structure review: {value['disposition']}\nContract: {value['input']['id']}@{value['input']['revision']}\nFindings: {len(value['findings'])}\nDigest: {value['output_digest']}"
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
    parser = argparse.ArgumentParser(prog="bbk-python", description=__doc__)
    parser.add_argument("--version", action="version", version=f"bbk-profile-python {VERSION}")
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
    p = sub.add_parser("syntax-check")
    p.add_argument("--root")
    p.add_argument("--path", action="append")
    p.set_defaults(func=syntax_check)
    p = sub.add_parser("structure")
    p.add_argument("--root")
    p.add_argument("--contract", required=True)
    p.add_argument("--role", default="architect")
    p.add_argument("--task-profile", default="implementation-structure")
    p.add_argument("--assurance-tier", choices=list(TIER_RANK))
    p.set_defaults(func=structure_command)
    p = sub.add_parser("slice")
    p.add_argument("--root")
    p.add_argument("--slice", required=True)
    p.add_argument("--contract")
    p.add_argument("--role", default="worker-designer")
    p.add_argument("--task-profile", default="execution-slicing")
    p.add_argument("--assurance-tier", choices=list(TIER_RANK))
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
    except PythonProfileError as exc:
        if args.json:
            print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"bbk-python: error: {exc}", file=sys.stderr)
        return 2
    print(pretty(value), end="") if args.json else print(human(value))
    if isinstance(value, dict) and value.get("status") in {"FAIL", "BLOCKED", "ERROR"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
