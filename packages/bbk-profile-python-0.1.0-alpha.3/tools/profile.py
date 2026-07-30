#!/usr/bin/env python3
"""Exact BBK alpha.8 typed language-profile capability dispatcher.

The six operations are read-only and non-authority-bearing. Generic BBK remains
responsible for request construction, AssuranceContract and ReviewManifest
semantics, candidate identity, evidence eligibility, finding lifecycle,
aggregation, locks, and any Blueprint adoption or release decision.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "PROFILE.json").read_text(encoding="utf-8"))
PROFILE_ID = str(PROFILE["id"])
PROFILE_VERSION = str(PROFILE["version"])
REQUEST_SCHEMA = "bbk.profile-capability-request.v1"
RESULT_SCHEMA = "bbk.profile-capability-result.v1"
OPERATIONS = {
    "state-effect": "state_decision_effect",
    "state-effect-inventory": "state_decision_effect",
    "state-effect-review": "state_decision_effect",
    "review-context": "review_assurance",
    "review-lens": "review_assurance",
    "evidence-adapter": "review_assurance",
}
RESULT_STATUS = {"PASS", "PASS_ADVISORY", "PARTIAL", "BLOCKED", "UNSUPPORTED", "ERROR"}
TRUST_CLASSES = {
    "DETERMINISTIC_LOCAL", "QUALIFIED_TOOL", "QUALIFIED_EXTERNAL_CHECK",
    "SIMULATOR_OR_HARNESS", "AGENT_INSPECTION", "HUMAN_REVIEW",
    "OPERATIONAL_OBSERVATION", "UNSTRUCTURED_OBSERVATION", "LEGACY_IMPORTED",
}
DEFAULT_EXCLUDES = [
    ".git/**", ".jj/**", ".bbk/**", ".bbk-worktrees/**",
    "node_modules/**", "target/**", "dist/**", "build/**", "out/**", ".next/**",
    ".venv/**", "venv/**", "__pycache__/**", ".pytest_cache/**", ".mypy_cache/**",
    ".ruff_cache/**", ".cache/**", "*.pyc", "*.pyo", "*.swp", "*.tmp",
]
SCAN_EXCLUDED_PARTS = {
    ".git", ".jj", ".bbk", ".bbk-worktrees", "node_modules", "target", "dist",
    "build", "out", ".next", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".cache",
}
MAX_CONTEXT_FILES = 240
MAX_CONTEXT_BYTES = 8 * 1024 * 1024
MAX_INVENTORY_FILES = 800
MAX_INVENTORY_BYTES = 16 * 1024 * 1024
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class DispatchError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DispatchError(f"JSON root must be an object: {path.name}")
    return value


def mapping(name: str) -> dict[str, Any]:
    return read_json(ROOT / "mappings" / name)


def package_identity() -> dict[str, str]:
    manifest = read_json(ROOT / "PACKAGE-MANIFEST.json")
    return {
        "id": PROFILE_ID,
        "version": PROFILE_VERSION,
        "rootSha256": str(manifest.get("root_sha256", "")),
        "manifestSha256": canonical_digest(PROFILE),
    }


def is_excluded(rel: str, patterns: Sequence[str] = DEFAULT_EXCLUDES) -> bool:
    rel = rel.lstrip("./")
    for raw in patterns:
        pattern = raw.lstrip("./")
        if fnmatch.fnmatch(rel, pattern):
            return True
        if pattern.endswith("/**"):
            base = pattern[:-3].rstrip("/")
            if rel == base or rel.startswith(base + "/"):
                return True
    return False


def source_content_digest(root: Path) -> str:
    """Reproduce BBK alpha.8 collect_manifest().content_sha256.

    The absolute source path and timestamps are deliberately excluded. The root
    directory label, relative paths, bytes, modes, and canonical JSON digests are
    part of the exact source identity, matching the core-owned request builder.
    """
    root = root.resolve()
    files: list[dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        directory = Path(dirpath)
        kept: list[str] = []
        for name in sorted(dirnames):
            path = directory / name
            rel = path.relative_to(root).as_posix()
            if is_excluded(rel):
                continue
            if path.is_symlink():
                target = os.readlink(path)
                files.append({"path": rel, "type": "symlink", "target": target, "sha256": hashlib.sha256(target.encode()).hexdigest()})
            else:
                kept.append(name)
        dirnames[:] = kept
        for name in sorted(filenames):
            path = directory / name
            rel = path.relative_to(root).as_posix()
            if is_excluded(rel):
                continue
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                target = os.readlink(path)
                files.append({"path": rel, "type": "symlink", "target": target, "sha256": hashlib.sha256(target.encode()).hexdigest()})
                continue
            if not stat.S_ISREG(info.st_mode):
                continue
            record: dict[str, Any] = {
                "path": rel,
                "type": "file",
                "size": info.st_size,
                "executable": bool(info.st_mode & stat.S_IXUSR),
                "sha256": sha256_file(path),
            }
            if path.suffix.lower() == ".json":
                record["semantic_kind"] = "canonical-json"
                try:
                    record["semantic_sha256"] = canonical_digest(json.loads(path.read_text(encoding="utf-8")))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    record["semantic_sha256"] = None
                    record["semantic_error"] = str(exc)
            files.append(record)
    content = {"schema": "bbk.manifest-content.v1", "root_label": root.name, "files": files}
    return canonical_digest(content)


def safe_request_path(value: str, request_dir: Path) -> Path:
    rel = Path(value)
    if not value or rel.is_absolute() or ".." in rel.parts or "\\" in value:
        raise DispatchError(f"unsafe request-relative input path: {value!r}")
    candidate = (request_dir / rel).resolve()
    try:
        candidate.relative_to(request_dir.resolve())
    except ValueError as exc:
        raise DispatchError(f"request input escapes request directory: {value!r}") from exc
    if not candidate.is_file():
        raise DispatchError(f"request input is missing: {value!r}")
    return candidate


def validate_request(request: dict[str, Any], operation: str, request_path: Path) -> tuple[str, dict[str, str], dict[str, dict[str, Any]], Path]:
    required = {"schema", "requestId", "operation", "profile", "source", "subject", "inputs", "context", "authority", "requestDigest"}
    extra = set(request) - required
    missing = required - set(request)
    if missing:
        raise DispatchError("missing request fields: " + ", ".join(sorted(missing)))
    if extra:
        raise DispatchError("unexpected request fields: " + ", ".join(sorted(extra)))
    if request.get("schema") != REQUEST_SCHEMA:
        raise DispatchError(f"request.schema must equal {REQUEST_SCHEMA}")
    request_id = request.get("requestId")
    if not isinstance(request_id, str) or not SAFE_ID.fullmatch(request_id):
        raise DispatchError("requestId is invalid")
    if request.get("operation") != operation:
        raise DispatchError("request operation does not match the selected entrypoint")
    supplied = request.get("requestDigest")
    if not isinstance(supplied, str) or not HEX64.fullmatch(supplied):
        raise DispatchError("requestDigest must be a lowercase SHA-256 digest")
    calculated = canonical_digest({key: value for key, value in request.items() if key != "requestDigest"})
    if supplied != calculated:
        raise DispatchError(f"request digest mismatch: expected {calculated}")

    identity = package_identity()
    profile = request.get("profile")
    if not isinstance(profile, dict) or set(profile) != {"id", "version", "rootSha256", "manifestSha256"}:
        raise DispatchError("request.profile must contain exactly id, version, rootSha256 and manifestSha256")
    for field in ("rootSha256", "manifestSha256"):
        if not isinstance(profile.get(field), str) or not HEX64.fullmatch(profile[field]):
            raise DispatchError(f"request.profile.{field} must be a lowercase SHA-256 digest")
    for field, expected in identity.items():
        if profile.get(field) != expected:
            raise DispatchError(f"request.profile.{field} does not match the installed package")

    source = request.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("root"), str) or not isinstance(source.get("contentSha256"), str) or not HEX64.fullmatch(source["contentSha256"]):
        raise DispatchError("request.source is invalid")
    source_env = os.environ.get("BBK_PROFILE_SOURCE_ROOT")
    if not source_env:
        raise DispatchError("BBK_PROFILE_SOURCE_ROOT is required for exact source binding")
    source_root = Path(source_env).expanduser().resolve()
    if not source_root.is_dir():
        raise DispatchError("BBK_PROFILE_SOURCE_ROOT does not name a readable directory")
    actual_source = source_content_digest(source_root)
    if actual_source != source["contentSha256"]:
        raise DispatchError("request source content digest does not match BBK_PROFILE_SOURCE_ROOT")

    subject = request.get("subject")
    if not isinstance(subject, dict) or set(subject) != {"ref", "kind", "revision", "digest"}:
        raise DispatchError("request.subject must contain exactly ref, kind, revision and digest")
    for field in ("ref", "kind", "revision"):
        if not isinstance(subject.get(field), str) or not subject[field]:
            raise DispatchError(f"request.subject.{field} is required")
    if not isinstance(subject.get("digest"), str) or not HEX64.fullmatch(subject["digest"]):
        raise DispatchError("request.subject.digest must be a lowercase SHA-256 digest")

    context = request.get("context")
    if not isinstance(context, dict):
        raise DispatchError("request.context must be an object")
    for field in ("role", "taskProfile", "assuranceTier", "runTools"):
        if field not in context:
            raise DispatchError(f"request.context.{field} is required")
    if context.get("assuranceTier") not in {"routine", "material", "consequential", "critical"}:
        raise DispatchError("request.context.assuranceTier is invalid")
    if not isinstance(context.get("runTools"), bool):
        raise DispatchError("request.context.runTools must be boolean")
    for field in ("paths", "hints", "changeClasses", "lensIds", "assignmentIds"):
        if field in context and (not isinstance(context[field], list) or not all(isinstance(item, str) for item in context[field])):
            raise DispatchError(f"request.context.{field} must be an array of strings")

    authority = request.get("authority")
    if not isinstance(authority, dict):
        raise DispatchError("request.authority must be an object")
    if authority.get("readOnly") is not True or authority.get("mayMutateSubject") is not False or authority.get("mayGrantEffects") is not False:
        raise DispatchError("profile capability operations require readOnly=true, mayMutateSubject=false and mayGrantEffects=false")
    if "runQualifiedReadOnlyTools" in authority and not isinstance(authority["runQualifiedReadOnlyTools"], bool):
        raise DispatchError("request.authority.runQualifiedReadOnlyTools must be boolean")

    raw_inputs = request.get("inputs")
    if not isinstance(raw_inputs, list) or not raw_inputs:
        raise DispatchError("request.inputs must be a non-empty array")
    loaded: dict[str, dict[str, Any]] = {}
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(raw_inputs):
        if not isinstance(raw, dict):
            raise DispatchError(f"request.inputs[{index}] must be an object")
        for field in ("kind", "path", "sha256"):
            if not isinstance(raw.get(field), str) or not raw[field]:
                raise DispatchError(f"request.inputs[{index}].{field} is required")
        if not HEX64.fullmatch(raw["sha256"]):
            raise DispatchError(f"request.inputs[{index}].sha256 is invalid")
        key = (raw["kind"], raw["path"])
        if key in seen:
            raise DispatchError(f"duplicate request input binding: {key[0]} {key[1]}")
        seen.add(key)
        path = safe_request_path(raw["path"], request_path.parent)
        raw_bytes = path.read_bytes()
        actual = hashlib.sha256(raw_bytes).hexdigest()
        if actual != raw["sha256"]:
            raise DispatchError(f"request input digest mismatch: {raw['path']}")
        value: Any
        try:
            value = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            value = raw_bytes.decode("utf-8", errors="replace")
        canonical = raw.get("canonicalSha256")
        if canonical is not None:
            if not isinstance(canonical, str) or not HEX64.fullmatch(canonical):
                raise DispatchError(f"request.inputs[{index}].canonicalSha256 is invalid")
            if not isinstance(value, (dict, list)) or canonical_digest(value) != canonical:
                raise DispatchError(f"request input canonical digest mismatch: {raw['path']}")
        loaded[raw["kind"]] = {
            "binding": dict(raw), "path": path, "bytes": len(raw_bytes), "sha256": actual,
            "value": value, "canonicalSha256": canonical,
        }
    return supplied, identity, loaded, source_root


def input_value(inputs: dict[str, dict[str, Any]], kind: str) -> Any:
    item = inputs.get(kind)
    if item is None:
        raise DispatchError(f"required input is missing: {kind}")
    return item["value"]


def subject_matches(request: dict[str, Any], ref: str, digest: str) -> None:
    subject = request["subject"]
    if subject["digest"] != digest:
        raise DispatchError("request subject digest does not match the bound semantic input")
    if ref and subject["ref"] != ref and not subject["ref"].startswith(ref + "@"):
        # Revisions may be represented in the request ref; digest remains the hard fence.
        raise DispatchError("request subject reference does not match the bound semantic input")


def design_identity(design: dict[str, Any]) -> tuple[str, str]:
    ref = str(design.get("designId") or design.get("id") or "state-effect-design")
    return ref, canonical_digest(design)


def find_strings(value: Any, names: set[str]) -> list[str]:
    found: list[str] = []
    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                normalized = key.casefold().replace("_", "-")
                if normalized in names:
                    if isinstance(child, str):
                        found.append(child)
                    elif isinstance(child, list):
                        found.extend(str(value) for value in child if isinstance(value, (str, int, float, bool)))
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
    walk(value)
    return sorted(dict.fromkeys(found))


def applicability(design: dict[str, Any]) -> str:
    value = str(design.get("applicability") or "").upper().replace("-", "_")
    if value in {"NONE", "INLINE", "CONTRACT"}:
        return value
    blob = json.dumps(design, sort_keys=True).casefold()
    if any(token in blob for token in ("retry", "duplicate", "cancellation", "timeout", "ambiguous", "recovery", "external-effect", "persistence")):
        return "CONTRACT"
    if any(token in blob for token in ("state", "transition", "effect", "lifecycle")):
        return "INLINE"
    return "NONE"


def token_present(blob: str, token: Any) -> bool:
    value = str(token).strip().casefold()
    if not value:
        return False
    if re.fullmatch(r"[a-z0-9_]+", value):
        return re.search(r"(?<![a-z0-9_])" + re.escape(value) + r"(?![a-z0-9_])", blob) is not None
    return value in blob


def selected_state_skills(level: str, design: dict[str, Any]) -> list[dict[str, str]]:
    config = mapping("state-effect-map.json")
    selected = list((config.get("routing") or {}).get(level, {}).get("skills", []))
    blob = json.dumps(design, sort_keys=True).casefold()
    for rule in config.get("conditionalSkills") or []:
        if any(token_present(blob, token) for token in rule.get("tokens") or []):
            selected.extend(rule.get("skills") or [])
    return [
        {"skillId": skill, "rationale": f"smallest sufficient profile procedure for {level} State–Decision–Effect treatment"}
        for skill in dict.fromkeys(selected)
    ]


def operation_result(operation: str, status: str, request_digest: str, payload: dict[str, Any] | None, *, warnings: Iterable[str] = (), errors: Iterable[str] = ()) -> dict[str, Any]:
    if status not in RESULT_STATUS:
        status = "ERROR"
    capability = OPERATIONS[operation]
    limitations = list((PROFILE.get("capabilities", {}).get(capability) or {}).get("limitations") or [])
    return {
        "schema": RESULT_SCHEMA,
        "profileId": PROFILE_ID,
        "profileVersion": PROFILE_VERSION,
        "capability": capability,
        "operation": operation,
        "status": status,
        "requestDigest": request_digest,
        "payload": payload,
        "warnings": list(warnings),
        "errors": list(errors),
        "limitations": limitations,
    }


def op_state_effect(request: dict[str, Any], inputs: dict[str, dict[str, Any]], source_root: Path) -> tuple[str, dict[str, Any], list[str], list[str]]:
    design = input_value(inputs, "state-decision-effect")
    if not isinstance(design, dict):
        return "BLOCKED", {"blockers": ["StateDecisionEffectDesign input must be structured JSON"]}, [], ["invalid StateDecisionEffectDesign input"]
    ref, digest = design_identity(design)
    subject_matches(request, ref, digest)
    level = applicability(design)
    config = mapping("state-effect-map.json")
    payload = {
        "schema": f"bbk.{config['schemaPrefix']}-state-effect-projection.v1",
        "subject": dict(request["subject"]),
        "designRef": {"ref": ref, "revision": str(design.get("revision") or "unknown"), "digest": digest},
        "applicability": level,
        "representations": list(config.get("representations") or config.get("concepts") or []),
        "boundaryConcepts": list(config.get("concepts") or []),
        "antiPatterns": list(config.get("antiPatterns") or []),
        "selectedProcedures": selected_state_skills(level, design),
        "fixedChoices": find_strings(design, {"fixed", "fixed-choices", "fixed-decision-refs", "required"}),
        "delegatedFreedom": list(design.get("delegatedFreedom") or []),
        "expectedFacets": list(config.get("expectedFacets") or []),
        "formalModelTools": list(config.get("formalModelTools") or []),
        "authority": {"readOnly": True, "genericDesignRemainsAuthoritative": True, "mayDeclareGenericPass": False},
    }
    return "PASS", payload, [], []


def source_candidates(root: Path, requested: Sequence[str], extensions: set[str], *, limit_files: int, limit_bytes: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    paths: list[Path] = []
    errors: list[str] = []
    if requested:
        for raw in requested:
            rel = Path(raw)
            if rel.is_absolute() or ".." in rel.parts or "\\" in raw:
                errors.append(f"unsafe requested source path: {raw}")
                continue
            candidate = (root / rel).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                errors.append(f"requested source path escapes root: {raw}")
                continue
            if candidate.is_file():
                paths.append(candidate)
            elif candidate.is_dir():
                paths.extend(candidate.rglob("*"))
            else:
                errors.append(f"missing requested source path: {raw}")
    else:
        paths = list(root.rglob("*"))
    selected: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    total = 0
    for path in sorted(set(paths), key=lambda value: value.relative_to(root).as_posix() if value.exists() else str(value)):
        if not path.exists() or path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if any(part in SCAN_EXCLUDED_PARTS for part in Path(rel).parts) or is_excluded(rel):
            continue
        metadata_names = {
            "Cargo.toml", "Cargo.lock", "go.mod", "go.sum", "go.work", "go.work.sum",
            "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock",
            "pyproject.toml", "setup.py", "setup.cfg", "MANIFEST.in", "py.typed", "README.md",
        }
        if path.suffix.casefold() not in extensions and path.name not in metadata_names:
            continue
        size = path.stat().st_size
        if len(selected) >= limit_files or total + size > limit_bytes:
            omitted.append({"path": rel, "reason": "profile-context-limit", "bytes": size})
            continue
        selected.append({"path": rel, "bytes": size, "sha256": sha256_file(path)})
        total += size
    return selected, omitted, errors


def read_source_text(root: Path, records: Sequence[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in records:
        if int(item["bytes"]) > 1024 * 1024:
            continue
        try:
            result[item["path"]] = (root / item["path"]).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return result


def signal_inventory(texts: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    patterns = mapping("state-effect-map.json").get("signalPatterns") or {}
    result: dict[str, list[dict[str, Any]]] = {}
    for category, tokens in patterns.items():
        hits: list[dict[str, Any]] = []
        for rel, text in texts.items():
            lower = text.casefold()
            matched = [str(token) for token in tokens if str(token).casefold() in lower]
            if matched:
                hits.append({"path": rel, "signals": sorted(dict.fromkeys(matched))})
        result[str(category)] = hits
    return result


def op_state_effect_inventory(request: dict[str, Any], inputs: dict[str, dict[str, Any]], source_root: Path) -> tuple[str, dict[str, Any], list[str], list[str]]:
    design = input_value(inputs, "state-decision-effect")
    if not isinstance(design, dict):
        return "BLOCKED", {"blockers": ["StateDecisionEffectDesign input must be structured JSON"]}, [], ["invalid StateDecisionEffectDesign input"]
    ref, digest = design_identity(design)
    subject_matches(request, ref, digest)
    context = request.get("context") or {}
    config = mapping("review-context-map.json")
    extensions = {str(item).casefold() for item in config.get("sourceExtensions") or []}
    records, omitted, scan_errors = source_candidates(
        source_root, list(context.get("paths") or []), extensions,
        limit_files=MAX_INVENTORY_FILES, limit_bytes=MAX_INVENTORY_BYTES,
    )
    if not records:
        payload = {
            "schema": f"bbk.{mapping('state-effect-map.json')['schemaPrefix']}-state-effect-inventory.v1",
            "subject": dict(request["subject"]),
            "status": "BLOCKED",
            "blockers": scan_errors or ["no profile-relevant source files were available for inventory"],
            "authority": {"readOnly": True, "genericDesignRemainsAuthoritative": True},
        }
        return "BLOCKED", payload, [], list(payload["blockers"])
    signals = signal_inventory(read_source_text(source_root, records))
    state_config = mapping("state-effect-map.json")
    canonical = signals.get("canonicalOwners", [])
    representations = signals.get("stateRepresentations", [])
    decisions = signals.get("decisionEntrypoints", [])
    effects = signals.get("effectExecutors", [])
    shadow = list(signals.get("shadowState", [])) + list(signals.get("ambientState", [])) + list(signals.get("derivedState", []))
    hidden = signals.get("hiddenDependencies", [])
    mechanisms = {
        key: signals.get(key, [])
        for key in ("retry", "cancellation", "duplicate", "timeout", "acknowledgement", "persistence", "migration", "recovery", "shutdown", "testsTracesModels")
    }
    payload = {
        "schema": f"bbk.{state_config['schemaPrefix']}-state-effect-inventory.v1",
        "inventoryId": "SEI-" + request["requestDigest"][:20].upper(),
        "subject": dict(request["subject"]),
        "designRef": {"ref": ref, "revision": str(design.get("revision") or "unknown"), "digest": digest},
        "status": "COMPLETE" if not omitted and not scan_errors else "PARTIAL",
        "sourceContentSha256": request["source"]["contentSha256"],
        "scannedItems": records,
        "canonicalStateOwners": canonical,
        "stateRepresentations": representations,
        "decisionEntrypoints": decisions,
        "effectExecutors": effects,
        "derivedOrShadowState": shadow,
        "hiddenDependencies": hidden,
        "mechanisms": mechanisms,
        "unknownAreas": scan_errors,
        "omissions": omitted,
        "limitations": list(PROFILE["capabilities"]["state_decision_effect"].get("limitations") or []),
        "authority": {"readOnly": True, "inventoryIsObservationNotAuthority": True, "mayDeclareConformance": False},
    }
    status = "PASS" if payload["status"] == "COMPLETE" else "PARTIAL"
    warnings = [f"{len(omitted)} source item(s) omitted by bounded inventory policy"] if omitted else []
    return status, payload, warnings, []


def inventory_values(inventory: dict[str, Any], *names: str) -> list[Any]:
    for name in names:
        value = inventory.get(name)
        if isinstance(value, list):
            return value
    return []


def op_state_effect_review(request: dict[str, Any], inputs: dict[str, dict[str, Any]], source_root: Path) -> tuple[str, dict[str, Any], list[str], list[str]]:
    design = input_value(inputs, "state-decision-effect")
    inventory = input_value(inputs, "state-effect-inventory")
    if not isinstance(design, dict) or not isinstance(inventory, dict):
        return "BLOCKED", {"blockers": ["structured design and inventory inputs are required"]}, [], ["invalid review inputs"]
    ref, digest = design_identity(design)
    subject_matches(request, ref, digest)
    inventory_subject = inventory.get("subject") if isinstance(inventory.get("subject"), dict) else {}
    inventory_digest = inventory_subject.get("digest") or inventory.get("subjectDigest")
    if inventory_digest != digest:
        return "BLOCKED", {"schema": f"bbk.{mapping('state-effect-map.json')['schemaPrefix']}-state-effect-review.v1", "subject": dict(request["subject"]), "blockers": ["inventory subject digest does not match the design subject"]}, [], ["wrong-subject state-effect inventory"]

    canonical = design.get("canonicalState") if isinstance(design.get("canonicalState"), dict) else {}
    expected_owners = {str(canonical.get("semanticOwner"))} if canonical.get("semanticOwner") else set()
    expected_owners.update(str(item.get("owner")) for item in canonical.get("dimensions") or [] if isinstance(item, dict) and item.get("owner"))
    observed_owner_items = inventory_values(inventory, "canonicalStateOwners", "canonicalOwners")
    observed_owners = set()
    for item in observed_owner_items:
        if isinstance(item, str): observed_owners.add(item)
        elif isinstance(item, dict): observed_owners.update(str(item.get(key)) for key in ("owner", "symbol", "path") if item.get(key))
    expected_boundaries = {str(item.get("boundaryId")) for item in design.get("decisionBoundaries") or [] if isinstance(item, dict) and item.get("boundaryId")}
    expected_effects = {str(item.get("effectId")) for item in design.get("effectContracts") or [] if isinstance(item, dict) and item.get("effectId")}
    observed_boundaries = set()
    for item in inventory_values(inventory, "decisionBoundaryIds", "decisionEntrypoints"):
        if isinstance(item, str): observed_boundaries.add(item)
        elif isinstance(item, dict): observed_boundaries.update(str(item.get(key)) for key in ("boundaryId", "symbol", "path") if item.get(key))
    observed_effects = set()
    for item in inventory_values(inventory, "effectExecutorIds", "effectExecutors"):
        if isinstance(item, str): observed_effects.add(item)
        elif isinstance(item, dict): observed_effects.update(str(item.get(key)) for key in ("effectId", "symbol", "path") if item.get(key))
    shadow = inventory_values(inventory, "derivedOrShadowState", "shadowState")
    hidden = inventory_values(inventory, "hiddenDependencies")
    findings: list[dict[str, Any]] = []
    if shadow:
        findings.append({"code": "SHADOW_OR_AMBIENT_STATE", "severity": "material", "summary": "Observed derived, shadow, cached or ambient state may compete with the canonical owner.", "evidence": shadow})
    if hidden:
        findings.append({"code": "HIDDEN_DECISION_DEPENDENCY", "severity": "material", "summary": "Decision behavior appears to consume hidden or ambient dependencies.", "evidence": hidden})
    missing_owners = sorted(owner for owner in expected_owners if owner and owner not in observed_owners)
    missing_boundaries = sorted(expected_boundaries - observed_boundaries)
    missing_effects = sorted(expected_effects - observed_effects)
    if missing_owners:
        findings.append({"code": "CANONICAL_OWNER_NOT_OBSERVED", "severity": "material", "summary": "Planned canonical state owner was not observed.", "evidence": missing_owners})
    if missing_boundaries:
        findings.append({"code": "DECISION_BOUNDARY_NOT_OBSERVED", "severity": "material", "summary": "Planned decision boundary was not observed.", "evidence": missing_boundaries})
    if missing_effects:
        findings.append({"code": "EFFECT_EXECUTOR_NOT_OBSERVED", "severity": "material", "summary": "Planned effect executor was not observed.", "evidence": missing_effects})
    extras = sorted((observed_owners - expected_owners) | (observed_boundaries - expected_boundaries) | (observed_effects - expected_effects))
    material = bool(findings)
    classification = "MATERIAL_DIVERGENCE" if material else ("PRIVATE_DIVERGENCE_ACCEPTED" if extras else "CONFORMANT")
    payload = {
        "schema": f"bbk.{mapping('state-effect-map.json')['schemaPrefix']}-state-effect-review.v1",
        "subject": dict(request["subject"]),
        "designRef": {"ref": ref, "revision": str(design.get("revision") or "unknown"), "digest": digest},
        "inventoryRef": str(inventory.get("inventoryId") or inventory.get("subjectRef") or "inventory"),
        "classification": classification,
        "findings": findings,
        "delegatedPrivateDifferences": extras,
        "coverageGaps": [],
        "recommendedGenericDisposition": "REVIEW_REQUIRED" if material else "PROFILE_REVIEW_COMPLETE",
        "authority": {"readOnly": True, "genericConformanceRemainsAuthoritative": True, "mayCloseFindings": False},
    }
    return ("PASS_ADVISORY" if material else "PASS"), payload, (["profile review found material divergence"] if material else []), []


def canonical_context_items(items: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"path": item["path"], "sha256": item["sha256"], "bytes": item["bytes"], "sourceClass": item["sourceClass"], "redaction": item["redaction"]}
        for item in items
    ]


def shard_record(shard_id: str, group: str, items: Sequence[dict[str, Any]]) -> dict[str, Any]:
    content = canonical_context_items(items)
    return {
        "shardId": shard_id,
        "primaryGroup": group,
        "primaryItemRefs": [item["itemId"] for item in items],
        "sharedItemRefs": [],
        "bytes": sum(int(item["bytes"]) for item in items),
        "contentRoot": canonical_digest(content),
    }


def op_review_context(request: dict[str, Any], inputs: dict[str, dict[str, Any]], source_root: Path) -> tuple[str, dict[str, Any], list[str], list[str]]:
    assurance = input_value(inputs, "assurance-contract")
    manifest = input_value(inputs, "review-manifest")
    if not isinstance(assurance, dict) or not isinstance(manifest, dict):
        return "BLOCKED", {"blockers": ["structured AssuranceContract and ReviewManifest inputs are required"]}, [], ["invalid review context inputs"]
    manifest_subject = manifest.get("subject") if isinstance(manifest.get("subject"), dict) else {}
    if manifest_subject != request["subject"]:
        return "BLOCKED", {"blockers": ["ReviewManifest subject does not match the dispatch subject"]}, [], ["wrong-subject ReviewManifest"]
    assurance_ref = manifest.get("assuranceContract") if isinstance(manifest.get("assuranceContract"), dict) else {}
    if assurance_ref.get("digest") != canonical_digest(assurance):
        return "BLOCKED", {"blockers": ["ReviewManifest AssuranceContract digest does not match the bound contract"]}, [], ["stale or wrong AssuranceContract"]

    included: list[dict[str, Any]] = []
    for index, kind in enumerate(("assurance-contract", "review-manifest"), start=1):
        item = inputs[kind]
        included.append({
            "itemId": f"BOUND-{index:03d}", "kind": kind, "path": item["binding"]["path"],
            "bytes": item["bytes"], "sha256": item["sha256"], "sourceClass": "core-bound-input",
            "generated": False, "redaction": "none",
        })

    policy = manifest.get("contextPolicy") if isinstance(manifest.get("contextPolicy"), dict) else {}
    requested_paths = list(request.get("context", {}).get("paths") or [])
    required_paths = [str(value) for value in policy.get("requiredPaths") or []]
    scan_paths = list(dict.fromkeys(requested_paths + required_paths))
    context_map = mapping("review-context-map.json")
    extensions = {str(item).casefold() for item in context_map.get("sourceExtensions") or []}
    source_records, omitted, scan_errors = source_candidates(
        source_root, scan_paths, extensions,
        limit_files=MAX_CONTEXT_FILES, limit_bytes=MAX_CONTEXT_BYTES,
    )
    for index, item in enumerate(source_records, start=1):
        included.append({
            "itemId": f"SOURCE-{index:04d}", "kind": "subject-source", "path": "source/" + item["path"],
            "bytes": item["bytes"], "sha256": item["sha256"], "sourceClass": "subject-source",
            "generated": False, "redaction": "none",
        })
    included.sort(key=lambda item: item["path"])
    missing_required = [path for path in required_paths if not (source_root / path).is_file()]
    blockers = [f"required context path is missing: {path}" for path in missing_required]
    blockers.extend(scan_errors)
    completeness = "COMPLETE"
    if blockers:
        completeness = "BLOCKED_REQUIRED_CONTEXT_MISSING"
    elif omitted:
        completeness = "PARTIAL_NONBLOCKING"
    elif context_map.get("declaredExclusions"):
        completeness = "COMPLETE_WITH_DECLARED_EXCLUSIONS"

    cross = list((manifest.get("shardPlan") or {}).get("crossShardAssertionRefs") or [])
    if cross and len(included) >= 2:
        bound_items = [item for item in included if item["sourceClass"] == "core-bound-input"]
        source_items = [item for item in included if item["sourceClass"] != "core-bound-input"]
        if not source_items:
            source_items = [bound_items.pop()]
        shards = [shard_record("SHARD-SEMANTIC", "governing-contracts", bound_items), shard_record("SHARD-SOURCE", "changed-surface", source_items)]
    else:
        shards = [shard_record("SHARD-001", "bounded-profile-context", included)]
    packs = [
        {"packId": f"PACK-{item['shardId']}", "shardRef": item["shardId"], "contentRoot": item["contentRoot"], "bytes": item["bytes"]}
        for item in shards
    ]
    hints = list(request.get("context", {}).get("hints") or [])
    targeted = [hint.split(":", 1)[1] for hint in hints if hint.startswith("targeted-finding:") and ":" in hint]
    payload = {
        "schema": "bbk.review-context-manifest.v1",
        "contextManifestId": "RCM-" + request["requestDigest"][:20].upper(),
        "revision": "1",
        "subject": dict(request["subject"]),
        "reviewManifest": {"ref": str(manifest.get("manifestId") or "review-manifest"), "digest": canonical_digest(manifest)},
        "root": str(request["source"]["root"]),
        "contentRoot": canonical_digest(canonical_context_items(included)),
        "requiredSemanticObjects": sorted(dict.fromkeys(["assurance-contract", "review-manifest", *[str(value) for value in policy.get("requiredKinds") or []]])),
        "includedItems": included,
        "retrievalOnlyItems": [],
        "excludedItems": [{"reason": "declared-profile-exclusion", "description": value} for value in context_map.get("declaredExclusions") or []],
        "omissions": omitted,
        "redactions": [],
        "compiler": {
            "id": f"bbk-profile-{PROFILE_ID}", "version": PROFILE_VERSION,
            "policyDigest": canonical_digest(context_map),
            "priorFindingsVisibility": manifest.get("priorFindingsVisibility", "HIDDEN"),
            "targetedFindingIds": targeted,
            "selectors": list(PROFILE["capabilities"]["review_assurance"].get("context_selectors") or []),
            "readOnly": True,
        },
        "contextPacks": packs,
        "shards": shards,
        "crossShardAssertions": cross,
        "completeness": completeness,
        "blockers": blockers,
        "dependencyClosure": sorted(dict.fromkeys([
            request["subject"]["digest"], canonical_digest(assurance), canonical_digest(manifest),
            request["source"]["contentSha256"], canonical_digest(context_map),
        ])),
        "authorityDisclaimer": "This profile context is a bounded read-only projection. Generic BBK ReviewManifest, AssuranceContract, evidence, finding, aggregation and closure authority remain controlling.",
    }
    status = "BLOCKED" if blockers else ("PARTIAL" if completeness == "PARTIAL_NONBLOCKING" or PROFILE["capabilities"]["review_assurance"].get("status") == "partial" else "PASS")
    warnings = [f"{len(omitted)} context item(s) omitted by the bounded context policy"] if omitted else []
    return status, payload, warnings, blockers


def assignment_assertions(manifest: dict[str, Any], assignment_ids: set[str], lens_ids: set[str]) -> list[str]:
    refs: list[str] = []
    for item in manifest.get("lensAssignments") or []:
        if not isinstance(item, dict):
            continue
        assignment = str(item.get("assignmentId") or "")
        lens = str(item.get("lens") or "")
        if (assignment_ids and assignment in assignment_ids) or (lens_ids and lens in lens_ids):
            refs.extend(str(value) for value in item.get("primaryAssertionRefs") or [])
    return list(dict.fromkeys(refs))


def op_review_lens(request: dict[str, Any], inputs: dict[str, dict[str, Any]], source_root: Path) -> tuple[str, dict[str, Any], list[str], list[str]]:
    assurance = input_value(inputs, "assurance-contract")
    manifest = input_value(inputs, "review-manifest")
    review_context = input_value(inputs, "review-context")
    if not all(isinstance(value, dict) for value in (assurance, manifest, review_context)):
        return "BLOCKED", {"blockers": ["structured assurance, review manifest and review context inputs are required"]}, [], ["invalid review lens inputs"]
    if manifest.get("subject") != request["subject"] or review_context.get("subject") != request["subject"]:
        return "BLOCKED", {"blockers": ["review inputs do not match the dispatch subject"]}, [], ["wrong-subject review inputs"]
    if review_context.get("reviewManifest", {}).get("digest") != canonical_digest(manifest):
        return "BLOCKED", {"blockers": ["ReviewContextManifest is stale for the supplied ReviewManifest"]}, [], ["stale ReviewContextManifest"]
    requested_lenses = list(dict.fromkeys(request.get("context", {}).get("lensIds") or []))
    requested_assignments = list(dict.fromkeys(request.get("context", {}).get("assignmentIds") or []))
    if not requested_lenses:
        requested_lenses = [str(item.get("lens")) for item in manifest.get("lensAssignments") or [] if isinstance(item, dict) and item.get("lens")]
    lens_map = mapping("review-lens-map.json")
    supported_map = lens_map.get("lenses") or {}
    supported = [lens for lens in requested_lenses if lens in supported_map]
    unsupported = [lens for lens in requested_lenses if lens not in supported_map]
    procedure_records: list[dict[str, str]] = []
    request_blob = json.dumps(request, sort_keys=True).casefold()
    for lens in supported:
        entry = supported_map[lens]
        skills = list(entry.get("skills") or [])
        for rule in entry.get("conditionalSkills") or []:
            if any(token_present(request_blob, token) for token in rule.get("tokens") or []):
                skills.extend(rule.get("skills") or [])
        for skill in dict.fromkeys(skills):
            procedure_records.append({"lensId": lens, "skillId": skill, "rationale": f"mapped specifically from logical lens {lens}"})
    assertion_refs = assignment_assertions(manifest, set(requested_assignments), set(supported))
    if not assertion_refs:
        assertion_refs = [str(item.get("assertionId")) for item in assurance.get("assertions") or [] if isinstance(item, dict) and item.get("assertionId")]
    evaluations = [
        {"assertionId": ref, "status": "NOT_EVALUATED", "evidenceRefs": [], "rationale": "Profile procedure selection does not establish generic assertion satisfaction."}
        for ref in assertion_refs
    ]
    blockers: list[str] = []
    hints = {value.casefold() for value in request.get("context", {}).get("hints") or []}
    native_required = any("native-required" in value or "physical-target-required" in value for value in hints)
    partial_profile = PROFILE["capabilities"]["review_assurance"].get("status") == "partial"
    if partial_profile and native_required:
        blockers.append("required native evidence is unavailable in a currently qualified profile environment")
    payload = {
        "schema": f"bbk.{mapping('evidence-adapter-map.json')['schemaPrefix']}-review-lens-result.v1",
        "subject": dict(request["subject"]),
        "lensIds": requested_lenses,
        "assignmentIds": requested_assignments,
        "handledLensIds": supported,
        "unhandledLensIds": unsupported,
        "selectedProcedures": procedure_records,
        "assertionEvaluations": evaluations,
        "findings": [],
        "coverageGaps": assertion_refs,
        "blockedChecks": blockers,
        "priorFindingsVisibility": manifest.get("priorFindingsVisibility", "HIDDEN"),
        "recommendedGenericDisposition": "BLOCKED" if blockers else ("UNHANDLED_BY_PROFILE" if not supported else "PROFILE_PROCEDURE_COMPLETE_EVIDENCE_REQUIRED"),
        "authority": {"readOnly": True, "operationPassIsNotAssertionPass": True, "mayCloseFindings": False, "mayDeclareGenericPass": False},
    }
    if blockers:
        return "BLOCKED", payload, [], blockers
    if not supported:
        return "UNSUPPORTED", payload, ["none of the requested logical lenses are handled by this profile"], []
    status = "PARTIAL" if partial_profile or unsupported else "PASS"
    warnings = ["some requested lenses remain generic/unhandled"] if unsupported else []
    if request.get("context", {}).get("runTools"):
        warnings.append("no profile-qualified read-only tool was required; no tool was launched")
    return status, payload, warnings, []


def evidence_subject(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    subject = value.get("subject") if isinstance(value.get("subject"), dict) else {}
    ref = subject.get("ref") or subject.get("id") or value.get("subjectRef")
    digest = subject.get("digest") or value.get("subjectDigest")
    result: dict[str, Any] = {}
    if isinstance(ref, str) and ref: result["ref"] = ref
    if isinstance(digest, str) and HEX64.fullmatch(digest): result["digest"] = digest
    return result


def normalize_argv(value: Any) -> list[str]:
    if isinstance(value, list) and all(isinstance(item, str) and item for item in value):
        return value
    if isinstance(value, str) and value:
        return [value]
    return ["not-recorded"]


def map_native_receipt(request: dict[str, Any], item: dict[str, Any]) -> tuple[dict[str, Any], list[str], bool, bool]:
    value = item["value"]
    if isinstance(value, dict) and value.get("schema") == "bbk.evidence-receipt.v2":
        receipt = json.loads(json.dumps(value))
        freshness = receipt.get("freshness") if isinstance(receipt.get("freshness"), dict) else {}
        redaction = receipt.get("redaction") if isinstance(receipt.get("redaction"), dict) else {}
        stale = bool(freshness.get("stale"))
        redacted = bool(redaction.get("redactedFields") or redaction.get("fields") or redaction.get("classification") not in (None, "none", "NONE"))
        return receipt, [], stale, redacted

    fields = value if isinstance(value, dict) else {"rawText": str(value)}
    missing: list[str] = []
    command = fields.get("command") or fields.get("argv")
    if command in (None, "", []): missing.append("operation.argv")
    observed = fields.get("observedAt") or fields.get("completedAt") or fields.get("startedAt")
    if not observed: missing.extend(["startedAt", "completedAt"])
    exit_code = fields.get("exitStatus") if isinstance(fields.get("exitStatus"), int) else fields.get("exitCode")
    if not isinstance(exit_code, int): missing.append("outputs.exitCode")
    tool = fields.get("toolchain") if isinstance(fields.get("toolchain"), dict) else fields.get("toolIdentity")
    environment = fields.get("environment") if isinstance(fields.get("environment"), dict) else fields.get("environmentIdentity")
    if not isinstance(tool, dict) or not tool: missing.append("toolIdentity")
    if not isinstance(environment, dict) or not environment: missing.append("environmentIdentity")
    raw_subject = evidence_subject(fields)
    if not raw_subject: missing.append("subject")
    redacted_fields = fields.get("redactedFields") if isinstance(fields.get("redactedFields"), list) else []
    stale_value = fields.get("stale")
    if not isinstance(stale_value, bool):
        freshness_value = fields.get("freshness")
        stale_value = bool(isinstance(freshness_value, dict) and freshness_value.get("stale")) or str(freshness_value).upper() == "STALE"
    requested_trust = fields.get("trustClass")
    if isinstance(value, str) or "rawText" in fields and len(fields) == 1:
        trust = "UNSTRUCTURED_OBSERVATION"
    elif isinstance(requested_trust, str) and requested_trust in TRUST_CLASSES:
        trust = requested_trust
    elif missing:
        trust = "LEGACY_IMPORTED"
    else:
        trust = "QUALIFIED_TOOL"
    source_digest = item["sha256"]
    started = str(fields.get("startedAt") or observed or "not-recorded")
    completed = str(fields.get("completedAt") or observed or "not-recorded")
    result_value = fields.get("completionStatus") or fields.get("result") or fields.get("status")
    if not result_value and isinstance(exit_code, int):
        result_value = "PASS" if exit_code == 0 else "FAIL"
    receipt = {
        "schema": "bbk.evidence-receipt.v2",
        "receiptId": "ER-" + source_digest[:20].upper(),
        "kind": str(fields.get("kind") or fields.get("evidenceKind") or "profile-native-evidence"),
        "producer": f"bbk-profile-{PROFILE_ID}@{PROFILE_VERSION}",
        "subject": {"ref": request["subject"]["ref"], "digest": request["subject"]["digest"]},
        "assertionRefs": [str(value) for value in fields.get("assertionRefs") or [] if isinstance(value, str) and value],
        "operation": {
            "argv": normalize_argv(command),
            "workingDirectory": str(fields.get("workingDirectory") or "not-recorded"),
            "sanitized": bool(fields.get("sanitized", False)),
            "network": bool(fields.get("network", False)),
            "externalEffects": bool(fields.get("externalEffects", False)),
        },
        "startedAt": started,
        "completedAt": completed,
        "completionStatus": str(result_value or "NOT_RECORDED"),
        "outputs": {
            "exitCode": exit_code if isinstance(exit_code, int) else None,
            "stdoutDigest": fields.get("stdoutDigest") if isinstance(fields.get("stdoutDigest"), str) and HEX64.fullmatch(fields["stdoutDigest"]) else None,
            "stderrDigest": fields.get("stderrDigest") if isinstance(fields.get("stderrDigest"), str) and HEX64.fullmatch(fields["stderrDigest"]) else None,
            "reportRefs": [str(value) for value in fields.get("reportRefs") or [] if isinstance(value, str) and value],
            "artifactRefs": [str(value) for value in fields.get("artifactRefs") or [] if isinstance(value, str) and value],
            "traceRefs": [str(value) for value in fields.get("traceRefs") or [] if isinstance(value, str) and value],
        },
        "toolIdentity": tool if isinstance(tool, dict) and tool else {"status": "not-recorded"},
        "environmentIdentity": environment if isinstance(environment, dict) and environment else {"status": "not-recorded"},
        "dependencyFingerprint": canonical_digest({
            "subject": request["subject"], "sourceEvidenceSha256": source_digest,
            "profile": package_identity(), "sourceContentSha256": request["source"]["contentSha256"],
        }),
        "coverage": {
            "complete": not missing and not redacted_fields,
            "missingFields": sorted(dict.fromkeys(missing)),
            "redactedFields": redacted_fields,
            "sourceEvidenceSha256": source_digest,
            "adapterEstablishesGenericEligibility": False,
        },
        "trustClass": trust,
        "redaction": {"classification": "field-redacted" if redacted_fields else "none", "redactedFields": redacted_fields, "rawDigestBeforeRedaction": source_digest if redacted_fields else None},
        "freshness": {
            "dependencyKeys": ["subject", "source-evidence", "profile", "source-tree"],
            "validUntil": fields.get("validUntil") if isinstance(fields.get("validUntil"), str) else None,
            "stale": bool(stale_value),
        },
        "rawEvidenceRef": str(item["binding"].get("ref") or f"sha256:{source_digest}"),
    }
    return receipt, missing, bool(stale_value), bool(redacted_fields)


def op_evidence_adapter(request: dict[str, Any], inputs: dict[str, dict[str, Any]], source_root: Path) -> tuple[str, dict[str, Any], list[str], list[str]]:
    item = inputs.get("evidence-input")
    if item is None:
        return "BLOCKED", {"blockers": ["exact evidence-input is required"]}, [], ["missing evidence-input"]
    raw_subject = evidence_subject(item["value"])
    if raw_subject and raw_subject.get("digest") != request["subject"]["digest"]:
        return "BLOCKED", {
            "schema": f"bbk.{mapping('evidence-adapter-map.json')['schemaPrefix']}-evidence-adapter-result.v1",
            "subject": dict(request["subject"]),
            "blockers": ["native evidence subject digest does not match the dispatch subject"],
            "authority": {"genericEvidenceEligibilityRemainsAuthoritative": True, "mayInventMissingFacts": False},
        }, [], ["wrong-subject native evidence"]
    receipt, missing, stale, redacted = map_native_receipt(request, item)
    receipt_subject = receipt.get("subject") if isinstance(receipt.get("subject"), dict) else {}
    if receipt_subject.get("digest") != request["subject"]["digest"]:
        return "BLOCKED", {"blockers": ["EvidenceReceipt subject digest does not match the dispatch subject"]}, [], ["wrong-subject EvidenceReceipt"]
    payload = {
        "schema": f"bbk.{mapping('evidence-adapter-map.json')['schemaPrefix']}-evidence-adapter-result.v1",
        "subject": dict(request["subject"]),
        "receipt": receipt,
        "sourceEvidenceSha256": item["sha256"],
        "missingFields": missing,
        "redacted": redacted,
        "stale": stale,
        "recommendedGenericDisposition": "REVIEW_ELIGIBILITY" if not (missing or stale or redacted) else "INCOMPLETE_OR_CONDITIONAL_EVIDENCE",
        "authority": {"genericEvidenceEligibilityRemainsAuthoritative": True, "mayInventMissingFacts": False, "mayDeclareAssertionPass": False},
    }
    status = "PARTIAL" if missing or stale or redacted or PROFILE["capabilities"]["review_assurance"].get("status") == "partial" else "PASS"
    warnings: list[str] = []
    if missing: warnings.append("evidence was adapted with explicit not-recorded fields")
    if stale: warnings.append("evidence is stale for at least one declared dependency")
    if redacted: warnings.append("evidence contains declared redaction")
    return status, payload, warnings, []


HANDLERS = {
    "state-effect": op_state_effect,
    "state-effect-inventory": op_state_effect_inventory,
    "state-effect-review": op_state_effect_review,
    "review-context": op_review_context,
    "review-lens": op_review_lens,
    "evidence-adapter": op_evidence_adapter,
}


def error_result(operation: str, request: dict[str, Any] | None, message: str) -> dict[str, Any]:
    supplied = request.get("requestDigest") if isinstance(request, dict) else None
    digest = supplied if isinstance(supplied, str) and HEX64.fullmatch(supplied) else "0" * 64
    return operation_result(operation, "ERROR", digest, None, errors=[message])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("operation", choices=sorted(OPERATIONS))
    parser.add_argument("--request", required=True)
    args = parser.parse_args(argv)
    operation = args.operation
    request_path = Path(args.request).expanduser().resolve()
    request: dict[str, Any] | None = None
    try:
        request = read_json(request_path)
        request_digest, _identity, inputs, source_root = validate_request(request, operation, request_path)
        status, payload, warnings, errors = HANDLERS[operation](request, inputs, source_root)
        result = operation_result(operation, status, request_digest, payload, warnings=warnings, errors=errors)
    except Exception as exc:
        result = error_result(operation, request, str(exc))
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
