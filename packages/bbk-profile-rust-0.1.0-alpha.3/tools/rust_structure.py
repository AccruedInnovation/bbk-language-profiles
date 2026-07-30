#!/usr/bin/env python3
"""Alpha.4 implementation-structure and execution-slice support for BBK Rust.

This module projects generic BBK planning objects into Rust vocabulary.  It is
non-authoritative: it does not mutate the repository, run planned gates, grant
an effect, expand scope, reduce assurance, or declare a candidate passed.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Sequence

BBK_VERSION = "0.1.0-alpha.4"
PROFILE_ID = "rust"
TIER_RANK = {"routine": 0, "material": 1, "consequential": 2, "critical": 3}


class StructureInputError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


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
        raise StructureInputError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StructureInputError(f"invalid JSON in {path}: {exc}") from exc


def _require_string(value: dict[str, Any], key: str, errors: list[str], prefix: str = "") -> None:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        errors.append(f"{prefix}{key} must be a non-empty string")


def validate_contract(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["contract must be an object"]
    if value.get("schema") != "bbk.implementation-structure-contract.v1":
        errors.append("schema must be bbk.implementation-structure-contract.v1")
    for key in ("contractId", "revision", "title", "status"):
        _require_string(value, key, errors)
    for key in ("subject", "applicability", "structure", "decisions", "review"):
        if not isinstance(value.get(key), dict):
            errors.append(f"{key} must be an object")
    applicability = value.get("applicability") if isinstance(value.get("applicability"), dict) else {}
    if applicability.get("level") not in {"none", "inline", "contract"}:
        errors.append("applicability.level must be none, inline, or contract")
    if not isinstance(applicability.get("triggers"), list):
        errors.append("applicability.triggers must be an array")
    _require_string(applicability, "rationale", errors, "applicability.")
    structure = value.get("structure") if isinstance(value.get("structure"), dict) else {}
    for key in ("artifactTopology", "keyContracts", "behaviorPaths", "stateOwnership", "effectBoundaries", "testSeams", "observabilityPoints", "migrationTouchpoints"):
        if not isinstance(structure.get(key), list):
            errors.append(f"structure.{key} must be an array")
    decisions = value.get("decisions") if isinstance(value.get("decisions"), dict) else {}
    for key in ("fixed", "delegated", "prohibited"):
        if not isinstance(decisions.get(key), list):
            errors.append(f"decisions.{key} must be an array")
    review = value.get("review") if isinstance(value.get("review"), dict) else {}
    if review.get("assuranceTier") not in TIER_RANK:
        errors.append("review.assuranceTier must be a BBK assurance tier")
    if not isinstance(review.get("requiredReviewers"), list):
        errors.append("review.requiredReviewers must be an array")
    if not isinstance(review.get("acceptanceCriteria"), list) or not review.get("acceptanceCriteria"):
        errors.append("review.acceptanceCriteria must be a non-empty array")
    return errors


def validate_slice(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["slice must be an object"]
    if value.get("schema") != "bbk.execution-slice.v1":
        errors.append("schema must be bbk.execution-slice.v1")
    for key in ("sliceId", "title", "status", "objective", "integrationOwner"):
        _require_string(value, key, errors)
    for key in ("parentCapabilityRefs", "structureContractRefs", "workUnitRefs", "assertions", "entryConditions", "exitConditions", "scaffolding"):
        if not isinstance(value.get(key), list):
            errors.append(f"{key} must be an array")
    for key in ("touchpoint", "flow", "atomicity"):
        if not isinstance(value.get(key), dict):
            errors.append(f"{key} must be an object")
    touchpoint = value.get("touchpoint") if isinstance(value.get("touchpoint"), dict) else {}
    for key in ("kind", "actor", "interaction", "expectedObservation", "environment"):
        _require_string(touchpoint, key, errors, "touchpoint.")
    atomicity = value.get("atomicity") if isinstance(value.get("atomicity"), dict) else {}
    for key in ("coherent", "reviewable", "independentlyVerifiable", "containedOrReversible"):
        if not isinstance(atomicity.get(key), bool):
            errors.append(f"atomicity.{key} must be boolean")
    _require_string(atomicity, "rationale", errors, "atomicity.")
    return errors


def load_contract(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    value = read_json(path)
    errors = validate_contract(value)
    record = {
        "kind": "ImplementationStructureContract",
        "id": value.get("contractId") if isinstance(value, dict) else None,
        "revision": value.get("revision") if isinstance(value, dict) else None,
        "digest": digest_value(value),
        "source_sha256": sha256_file(path),
        "path": str(path.resolve()),
        "validation_errors": errors,
    }
    return value, record


def load_slice(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    value = read_json(path)
    errors = validate_slice(value)
    record = {
        "kind": "ExecutionSlice",
        "id": value.get("sliceId") if isinstance(value, dict) else None,
        "revision": None,
        "digest": digest_value(value),
        "source_sha256": sha256_file(path),
        "path": str(path.resolve()),
        "validation_errors": errors,
    }
    return value, record


def structure_support_status(profile: dict[str, Any]) -> str:
    capability = profile.get("capabilities", {}).get("implementation_structure") if isinstance(profile.get("capabilities"), dict) else None
    if not isinstance(capability, dict):
        return "legacy-unprojected"
    status = capability.get("status")
    return status if status in {"supported", "partial", "unsupported"} else "unsupported"


def _all_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def _rust_artifact_kind(item: dict[str, Any]) -> str:
    text = f"{item.get('kind','')} {item.get('logicalPath','')} {item.get('responsibility','')}".lower()
    if "workspace" in text:
        return "workspace"
    if "crate" in text or "package" in text:
        return "crate"
    if "feature" in text:
        return "feature"
    if "target" in text or "binary" in text:
        return "target"
    if "migration" in text or text.endswith(".sql"):
        return "migration"
    if "generated" in text or "binding" in text or "schema" in text:
        return "generated-artifact"
    if "test" in text or "fixture" in text or "bench" in text:
        return "test"
    return "module"


def _rust_contract_kind(item: dict[str, Any]) -> str:
    text = f"{item.get('kind','')} {item.get('name','')} {item.get('shape','')} {item.get('responsibility','')}".lower()
    if any(token in text for token in ("ffi", "abi", "extern", "repr(")):
        return "unsafe-ffi-abi"
    if any(token in text for token in ("wire", "schema", "serde", "protocol", "message")):
        return "wire-schema"
    if any(token in text for token in ("trait", "interface", "port")):
        return "trait-boundary"
    if any(token in text for token in ("error", "failure", "result")):
        return "failure-contract"
    if any(token in text for token in ("task", "future", "channel", "cancel", "shutdown")):
        return "async-lifecycle"
    if any(token in text for token in ("migration", "transaction", "persistence", "replay")):
        return "persistence-contract"
    return "public-api" if item.get("visibility") in {"public", "external", "shared"} else "internal-contract"


def _contains_any(text: str, values: Iterable[str]) -> bool:
    return any(value in text for value in values)


def _base_envelope(schema: str, profile: dict[str, Any], input_record: dict[str, Any], preflight_digest: str | None) -> dict[str, Any]:
    return {
        "schema": schema,
        "profile": {"id": PROFILE_ID, "package": profile.get("package"), "version": profile.get("version"), "maturity": profile.get("maturity")},
        "bbk_version": BBK_VERSION,
        "input": input_record,
        "preflight_digest": preflight_digest,
        "unsupported_or_uncertain": [],
        "advisories": [],
        "blockers": [],
        "authority": {
            "projection_is_authoritative_state": False,
            "may_declare_pass": False,
            "may_expand_work_scope": False,
            "may_grant_tools_or_effects": False,
            "may_reduce_assurance": False,
            "statement": "This profile output is a deterministic view over the generic BBK object. The generic object remains authoritative.",
        },
    }


def _finish(value: dict[str, Any]) -> dict[str, Any]:
    value["output_digest"] = digest_value(value)
    return value


def structure_projection(
    *,
    root: Path,
    contract_path: Path,
    profile: dict[str, Any],
    preflight: dict[str, Any] | None,
    role: str,
    task_profile: str,
    assurance_tier: str,
) -> dict[str, Any]:
    contract, record = load_contract(contract_path)
    output = _base_envelope("rust.implementation-structure-projection.v1", profile, record, preflight.get("digest") if preflight else None)
    errors = record["validation_errors"]
    level = contract.get("applicability", {}).get("level") if isinstance(contract, dict) else None
    if errors:
        output["applicability"] = {"level": level or "unknown", "disposition": "BLOCKED", "rationale": "The generic contract is invalid."}
        output["blockers"] = errors
        output["projection"] = {}
        return _finish(output)
    if level == "none":
        output["applicability"] = {"level": "none", "disposition": "NOT_APPLICABLE", "rationale": contract["applicability"]["rationale"]}
        output["projection"] = {}
        return _finish(output)

    structure = contract["structure"]
    text = _all_text(contract)
    artifacts = []
    for item in structure["artifactTopology"]:
        if not isinstance(item, dict):
            continue
        artifacts.append({
            "id": item.get("id"),
            "planned_action": item.get("action"),
            "generic_kind": item.get("kind"),
            "rust_kind": _rust_artifact_kind(item),
            "logical_path": item.get("logicalPath"),
            "responsibility": item.get("responsibility"),
            "owner": item.get("owner"),
            "source_refs": item.get("sourceRefs", []),
        })
    contracts = []
    for item in structure["keyContracts"]:
        if not isinstance(item, dict):
            continue
        contracts.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "generic_kind": item.get("kind"),
            "rust_kind": _rust_contract_kind(item),
            "shape": item.get("shape"),
            "visibility": item.get("visibility"),
            "responsibility": item.get("responsibility"),
            "invariants": item.get("invariants", []),
            "failure_semantics": item.get("failureSemantics", []),
        })

    identity_candidates = [item["name"] for item in contracts if item.get("name") and _contains_any(str(item.get("rust_kind")), ("public", "wire"))]
    state_entries = [item for item in structure["stateOwnership"] if isinstance(item, dict)]
    effect_entries = [item for item in structure["effectBoundaries"] if isinstance(item, dict)]
    async_relevant = _contains_any(text, ("async", "future", "task", "channel", "cancel", "shutdown", "lock", "concurrency"))
    persistence_relevant = _contains_any(text, ("persist", "migration", "transaction", "replay", "durab", "idempot"))
    unsafe_relevant = _contains_any(text, ("unsafe", "ffi", "abi", "extern", "allocator", "unwind", "repr("))

    type_strategy = {
        "identity_types": {
            "guidance": "Use newtypes only for materially distinct identities, units, or authority-bearing references.",
            "candidates": identity_candidates,
        },
        "state_types": {
            "guidance": "Use enums and exhaustive transition handling for closed lifecycle, outcome, and protocol states.",
            "planned_state": [{"state": item.get("state"), "owner": item.get("owner"), "lifetime": item.get("lifetime")} for item in state_entries],
        },
        "boundary_types": {
            "guidance": "Define public request/result, wire, persistence, and package-consumer shapes before independent work begins.",
            "contracts": [item["id"] for item in contracts if item.get("visibility") in {"shared", "public", "external"}],
        },
        "ownership_types": {
            "guidance": "Make mutation authority, lifetimes, async task ownership, cancellation, and shutdown ownership explicit; static notation does not prove runtime liveness.",
            "state_owners": [{"state": item.get("state"), "owner": item.get("owner"), "mutation_authority": item.get("mutationAuthority"), "concurrency": item.get("concurrency")} for item in state_entries],
        },
        "failure_types": {
            "guidance": "Use stable error enums or classified results where callers need retry, rejection, timeout, partial-completion, stale-data, or recovery semantics.",
            "failure_boundaries": [{"effect": item.get("effect"), "owner": item.get("owner"), "failure": item.get("failure"), "recovery": item.get("recovery")} for item in effect_entries],
        },
        "evidence_types": {
            "guidance": "Keep NOT_RUN, BLOCKED, ERROR, INCONCLUSIVE, PASS, and FAIL distinct in receipts and validator results.",
            "dispositions": ["NOT_RUN", "BLOCKED", "ERROR", "INCONCLUSIVE", "PASS", "FAIL"],
        },
        "type_depth_test": [
            "prevents a material invalid combination",
            "localizes an invariant",
            "makes ownership or authority unambiguous",
            "stabilizes a boundary",
            "improves change locality",
            "creates a meaningful test seam",
            "hides consequential complexity behind a smaller contract",
        ],
        "anti_patterns": [
            "speculative generic abstraction",
            "a trait for every concrete type",
            "typestate that worsens ordinary evolution or diagnostics",
            "wrapper types with no protected invariant",
            "compiler success treated as proof of runtime protocol, persistence, or unsafe correctness",
        ],
    }

    workspace = preflight.get("workspace", {}) if preflight else {}
    support = {
        "workspace_members": workspace.get("members", []),
        "declared_targets": preflight.get("toolchain", {}).get("targets", []) if preflight else [],
        "features_and_targets_require_repository_policy": True,
    }
    output["applicability"] = {
        "level": level,
        "disposition": "SUPPORTED",
        "rationale": contract["applicability"]["rationale"],
        "trigger_hints": contract["applicability"].get("triggers", []),
    }
    output["projection"] = {
        "subject": contract["subject"],
        "role": role,
        "task_profile": task_profile,
        "assurance_tier": assurance_tier,
        "artifact_topology": artifacts,
        "key_contracts": contracts,
        "type_strategy": type_strategy,
        "behavior_paths": structure["behaviorPaths"],
        "state_and_information_ownership": state_entries,
        "effect_boundaries": effect_entries,
        "async_and_concurrency": {
            "applicable": async_relevant,
            "required_questions": [
                "Who owns each spawned task/future?",
                "How is cancellation signalled and observed?",
                "Who closes channels and releases locks/resources?",
                "What is the shutdown join/timeout policy?",
            ] if async_relevant else [],
        },
        "persistence_and_migration": {
            "applicable": persistence_relevant,
            "required_questions": [
                "What is durable before and after interruption?",
                "Which operation is idempotent or replay-safe?",
                "Who owns migration, rollback, and mixed-version behavior?",
            ] if persistence_relevant else [],
        },
        "unsafe_ffi_abi": {
            "applicable": unsafe_relevant,
            "required_questions": [
                "What invariant makes each unsafe operation sound?",
                "What allocation, ownership, panic, unwinding, and ABI contract crosses the boundary?",
                "Which runtime or tool evidence complements review?",
            ] if unsafe_relevant else [],
        },
        "test_seams": structure["testSeams"],
        "observability_points": structure["observabilityPoints"],
        "migration_touchpoints": structure["migrationTouchpoints"],
        "fixed_decisions": contract["decisions"]["fixed"],
        "delegated_freedom": contract["decisions"]["delegated"],
        "prohibited_shortcuts": contract["decisions"]["prohibited"],
        "review_acceptance": contract["review"],
        "repository_observations": support,
    }
    if contract.get("status") not in {"accepted", "approved"} and level == "contract":
        output["advisories"].append("The contract-level projection is usable for review, but coordinated production work should not treat an unaccepted contract as fixed authority.")
    if contract.get("subject", {}).get("kind") not in {"software", "rust", "mixed", "library", "service", "tool"}:
        output["unsupported_or_uncertain"].append("The subject is not primarily software; the Rust projection covers only the Rust-owned portion and adjacent obligations remain outside this profile.")
    return _finish(output)


def _slice_touchpoint(kind: str) -> tuple[str, bool]:
    value = kind.strip().lower()
    mapping = {
        "cli": "cli-operation",
        "api": "api-exchange",
        "protocol": "protocol-trace",
        "test": "executable-test",
        "component-test": "component-test",
        "integration-test": "integration-test",
        "consumer": "downstream-consumer",
        "consumer-test": "downstream-consumer",
        "package": "package-artifact",
        "migration": "migration-rehearsal",
        "benchmark": "measured-benchmark",
        "service": "service-scenario",
    }
    return mapping.get(value, value), value in mapping


def slice_projection(
    *,
    root: Path,
    slice_path: Path,
    profile: dict[str, Any],
    preflight: dict[str, Any] | None,
    role: str,
    task_profile: str,
    assurance_tier: str,
) -> dict[str, Any]:
    item, record = load_slice(slice_path)
    output = _base_envelope("rust.execution-slice-projection.v1", profile, record, preflight.get("digest") if preflight else None)
    errors = record["validation_errors"]
    if errors:
        output["applicability"] = {"disposition": "BLOCKED", "rationale": "The generic execution slice is invalid."}
        output["blockers"] = errors
        output["projection"] = {}
        return _finish(output)
    touchpoint_kind, native = _slice_touchpoint(item["touchpoint"]["kind"])
    objective_text = str(item.get("objective", "")).lower()
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    foundation = bool(metadata.get("foundationException")) or "foundation" in objective_text
    if not native:
        output["unsupported_or_uncertain"].append("The touchpoint is not Rust-native. This projection covers only Rust-owned work and must be composed with the adjacent domain profile.")
    horizontal_risk = False
    if len(item.get("flow", {}).get("participants", [])) <= 1 and not native:
        horizontal_risk = True
    if foundation and not metadata.get("enablesNextSlice"):
        output["advisories"].append("Foundation-first work should name the integrated slice it enables next.")
    assertions = item.get("assertions", [])
    evidence = []
    for assertion in assertions:
        if not isinstance(assertion, dict):
            continue
        evidence.append({
            "assertion_id": assertion.get("id"),
            "method": assertion.get("method"),
            "expected_evidence": assertion.get("evidence"),
            "rust_evidence": _rust_evidence_for_touchpoint(touchpoint_kind, assertion.get("method")),
        })
    scaffolding = []
    for scaffold in item.get("scaffolding", []):
        if isinstance(scaffold, dict):
            scaffolding.append({**scaffold, "risk": "Temporary adapters, fixtures, feature flags, mocks, or generated bindings must not become an undeclared production dependency."})
    output["applicability"] = {
        "disposition": "SUPPORTED" if native else "PARTIAL",
        "rationale": "The slice has a Rust-relevant integrated touchpoint." if native else "Only the Rust-owned portion can be projected.",
    }
    output["projection"] = {
        "role": role,
        "task_profile": task_profile,
        "assurance_tier": assurance_tier,
        "touchpoint": {**item["touchpoint"], "rust_kind": touchpoint_kind},
        "dependency_closure": {
            "structure_contract_refs": item.get("structureContractRefs", []),
            "work_unit_refs": item.get("workUnitRefs", []),
            "interface_refs": item.get("flow", {}).get("interfaceRefs", []),
            "architecture_refs": item.get("flow", {}).get("architectureRefs", []),
            "participants": item.get("flow", {}).get("participants", []),
        },
        "candidate_boundary": {
            "recommended": "one exact candidate or tightly coupled validation cohort for the listed work units",
            "work_units": item.get("workUnitRefs", []),
            "integration_owner": item.get("integrationOwner"),
        },
        "validation_boundary": {
            "assertions": evidence,
            "candidate_bound": True,
            "compile_or_test_success_is_not_operational_truth": True,
        },
        "atomicity_assessment": {
            **item["atomicity"],
            "horizontal_sequencing_risk": horizontal_risk,
            "foundation_exception": {
                "claimed": foundation,
                "named_risk_retired": metadata.get("foundationRiskRetired"),
                "enables_next_slice": metadata.get("enablesNextSlice"),
                "acceptable": (not foundation) or bool(metadata.get("foundationRiskRetired") and metadata.get("enablesNextSlice")),
            },
        },
        "scaffolding": scaffolding,
        "entry_conditions": item.get("entryConditions", []),
        "exit_conditions": item.get("exitConditions", []),
        "flow": item.get("flow", {}),
    }
    if horizontal_risk and not foundation:
        output["advisories"].append("The slice appears horizontally framed and may delay integrated feedback; either add a real touchpoint or document a bounded foundation exception.")
    return _finish(output)


def _rust_evidence_for_touchpoint(touchpoint_kind: str, method: Any) -> list[str]:
    evidence = ["exact candidate manifest", "effective Rust profile and toolchain identity"]
    if touchpoint_kind in {"cli-operation", "api-exchange", "service-scenario", "protocol-trace", "downstream-consumer"}:
        evidence.extend(["focused behavioral test", "consumer or integration observation"])
    if touchpoint_kind == "package-artifact":
        evidence.extend(["clean package contents", "build/test from packaged artifact"])
    if touchpoint_kind == "migration-rehearsal":
        evidence.extend(["pre/post state", "rollback or complete-forward evidence"])
    if touchpoint_kind == "measured-benchmark":
        evidence.extend(["workload and environment", "sample distribution and baseline"])
    if str(method).lower() in {"review", "inspection"}:
        evidence.append("review findings tied to fixed decisions and delegated freedom")
    return evidence


def rust_actual_inventory(root: Path, preflight: dict[str, Any] | None = None) -> dict[str, Any]:
    root = root.resolve()
    artifacts: list[dict[str, Any]] = []
    contracts: list[dict[str, Any]] = []
    signals: dict[str, int] = {"unsafe": 0, "extern": 0, "async": 0, "spawn": 0, "channel": 0, "lock": 0, "migration": 0}
    excludes = {"target", ".git", ".jj", ".bbk", ".bbk-worktrees", "vendor"}
    count = 0
    for path in sorted(root.rglob("*")):
        if count >= 5000:
            break
        if not path.is_file() or path.suffix not in {".rs", ".toml", ".sql", ".proto", ".wit"}:
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in excludes for part in rel_parts):
            continue
        count += 1
        rel = path.relative_to(root).as_posix()
        kind = "test" if "tests" in rel_parts or "benches" in rel_parts or "fuzz" in rel_parts else ("migration" if path.suffix == ".sql" or "migrations" in rel_parts else "module")
        artifacts.append({"id": rel, "logicalPath": rel, "kind": kind, "visibility": "private"})
        if path.suffix != ".rs" or path.stat().st_size > 1024 * 1024:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for key, pattern in {
            "unsafe": r"\bunsafe\b", "extern": r"\bextern\s+\"", "async": r"\basync\s+fn\b|\.await\b",
            "spawn": r"\bspawn(?:_blocking)?\s*\(", "channel": r"\b(?:mpsc|oneshot|broadcast|watch)::",
            "lock": r"\b(?:Mutex|RwLock)\b", "migration": r"\b(?:transaction|migrat|replay|idempot)\w*\b",
        }.items():
            signals[key] += len(re.findall(pattern, text))
        for match in re.finditer(r"(?m)^\s*pub(?:\([^)]*\))?\s+(?:unsafe\s+)?(?:async\s+)?(struct|enum|trait|type|fn|mod|const|static)\s+([A-Za-z_][A-Za-z0-9_]*)", text):
            contracts.append({"id": f"{rel}::{match.group(2)}", "name": match.group(2), "kind": match.group(1), "visibility": "public", "path": rel})
    packages = []
    if preflight:
        for package in preflight.get("workspace", {}).get("packages", []):
            packages.append({"name": package.get("name"), "root": package.get("root"), "crate_types": package.get("crate_types", [])})
    value = {
        "schema": "rust.actual-structure-inventory.v1",
        "root": str(root),
        "packages": packages,
        "artifacts": artifacts,
        "contracts": contracts,
        "stateOwnership": [],
        "fixedDecisionRefs": [],
        "declaredDivergences": [],
        "signals": signals,
        "bounded_scan": {"files": count, "max_files": 5000},
    }
    value["digest"] = digest_value(value)
    return value


def _normalized(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def planned_actual_comparison(contract: dict[str, Any], actual: dict[str, Any], *, contract_digest: str, actual_digest: str) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    expected_artifacts = [item for item in contract["structure"]["artifactTopology"] if isinstance(item, dict) and item.get("action") != "remove"]
    actual_artifacts = [item for item in actual.get("artifacts", []) if isinstance(item, dict)]
    artifact_keys = {_normalized(item.get("id")) for item in actual_artifacts} | {_normalized(item.get("logicalPath") or item.get("path")) for item in actual_artifacts}
    for item in expected_artifacts:
        keys = {_normalized(item.get("id")), _normalized(item.get("logicalPath"))}
        if not any(key and key in artifact_keys for key in keys):
            kind = _rust_artifact_kind(item)
            severity = "material" if kind in {"workspace", "crate", "feature", "target", "migration", "generated-artifact"} else "advisory"
            findings.append({"classification": severity, "kind": "artifact-missing", "planned_ref": item.get("id"), "message": f"Planned {kind} artifact was not found in the actual inventory.", "fixed_decision_ref": None})

    actual_contracts = [item for item in actual.get("contracts", []) if isinstance(item, dict)]
    contract_keys = {_normalized(item.get("id")) for item in actual_contracts} | {_normalized(item.get("name")) for item in actual_contracts}
    for item in contract["structure"]["keyContracts"]:
        if not isinstance(item, dict) or item.get("visibility") not in {"shared", "public", "external"}:
            continue
        keys = {_normalized(item.get("id")), _normalized(item.get("name"))}
        if not any(key and key in contract_keys for key in keys):
            findings.append({"classification": "material", "kind": "public-contract-missing", "planned_ref": item.get("id"), "message": "A planned public/shared contract is absent or renamed without evidence of an accepted change.", "fixed_decision_ref": _fixed_ref_for_text(contract, f"{item.get('id')} {item.get('name')}")})

    if "stateOwnership" in actual:
        actual_state = {(_normalized(item.get("state")), _normalized(item.get("owner"))) for item in actual.get("stateOwnership", []) if isinstance(item, dict)}
        for item in contract["structure"]["stateOwnership"]:
            if not isinstance(item, dict):
                continue
            expected = (_normalized(item.get("state")), _normalized(item.get("owner")))
            if expected not in actual_state:
                findings.append({"classification": "material", "kind": "state-owner-divergence", "planned_ref": item.get("state"), "message": f"Planned state owner {item.get('owner')} is not represented in the actual inventory.", "fixed_decision_ref": _fixed_ref_for_text(contract, f"{item.get('state')} {item.get('owner')}")})

    if "fixedDecisionRefs" in actual and actual.get("fixedDecisionRefs"):
        actual_fixed = {str(item) for item in actual.get("fixedDecisionRefs", [])}
        for decision in contract["decisions"]["fixed"]:
            if isinstance(decision, dict) and decision.get("id") not in actual_fixed:
                findings.append({"classification": "material", "kind": "fixed-decision-unconfirmed", "planned_ref": decision.get("id"), "message": "The actual inventory does not confirm this fixed decision.", "fixed_decision_ref": decision.get("id")})

    for item in actual.get("declaredDivergences", []):
        if not isinstance(item, dict):
            continue
        classification = item.get("classification", "unknown")
        if classification == "within-delegated":
            continue
        findings.append({
            "classification": "material" if classification == "material" else "advisory",
            "kind": item.get("kind", "declared-divergence"),
            "planned_ref": item.get("plannedRef"),
            "message": item.get("message", "Declared planned/actual divergence."),
            "fixed_decision_ref": item.get("fixedDecisionRef"),
        })

    material = [item for item in findings if item["classification"] == "material"]
    advisory = [item for item in findings if item["classification"] == "advisory"]
    if material:
        disposition = "MATERIAL_DIVERGENCE"
    elif advisory:
        disposition = "ADVISORY_DIVERGENCE"
    else:
        disposition = "CONFORMS"
    result = {
        "schema": "rust.planned-actual-structure-comparison.v1",
        "contract_digest": contract_digest,
        "actual_inventory_digest": actual_digest,
        "disposition": disposition,
        "material_findings": material,
        "advisory_findings": advisory,
        "within_delegated_freedom": [item for item in actual.get("declaredDivergences", []) if isinstance(item, dict) and item.get("classification") == "within-delegated"],
        "comparison_policy": "Compare fixed decisions and consequential public/shared shape; do not require exact private file-tree equality.",
    }
    result["output_digest"] = digest_value(result)
    return result


def _fixed_ref_for_text(contract: dict[str, Any], text: str) -> str | None:
    needle = _normalized(text)
    for item in contract.get("decisions", {}).get("fixed", []):
        if isinstance(item, dict) and needle and any(part and part in _normalized(item.get("statement")) for part in [needle, _normalized(text.split()[0] if text.split() else "")]):
            return item.get("id")
    return None


def structure_review(
    *,
    root: Path,
    contract_path: Path,
    candidate_path: Path,
    actual_inventory_path: Path | None,
    profile: dict[str, Any],
    preflight: dict[str, Any] | None,
    assurance_tier: str,
) -> dict[str, Any]:
    contract, contract_record = load_contract(contract_path)
    candidate = read_json(candidate_path)
    candidate_record = {"path": str(candidate_path.resolve()), "source_sha256": sha256_file(candidate_path), "digest": digest_value(candidate)}
    output = _base_envelope("rust.structure-review-result.v1", profile, contract_record, preflight.get("digest") if preflight else None)
    level = contract.get("applicability", {}).get("level") if isinstance(contract, dict) else None
    output["applicability"] = {"level": level or "unknown", "disposition": "PENDING", "rationale": "Focused planned-versus-actual structure review."}
    output["projection"] = {}
    if contract_record["validation_errors"]:
        output["applicability"] = {"level": level or "unknown", "disposition": "BLOCKED", "rationale": "The generic contract is invalid."}
        output.update({"review_id": digest_value({"contract": contract_record["digest"], "candidate": candidate_record["digest"]})[:24], "candidate": candidate_record, "reviewer": {"kind": "focused-profile-review", "profile": PROFILE_ID}, "coverage": [], "findings": [], "disposition": "BLOCKED", "blockers": contract_record["validation_errors"], "comparison": None, "limitations": []})
        return _finish(output)
    if contract.get("applicability", {}).get("level") == "none":
        output["applicability"] = {"level": "none", "disposition": "NOT_APPLICABLE", "rationale": contract.get("applicability", {}).get("rationale", "No profile-specific review applies.")}
        output.update({"review_id": digest_value({"contract": contract_record["digest"], "candidate": candidate_record["digest"]})[:24], "candidate": candidate_record, "reviewer": {"kind": "focused-profile-review", "profile": PROFILE_ID}, "coverage": [], "findings": [], "disposition": "NOT_APPLICABLE", "comparison": None, "limitations": []})
        return _finish(output)
    if actual_inventory_path:
        actual = read_json(actual_inventory_path)
        actual_digest = digest_value(actual)
        actual_source = sha256_file(actual_inventory_path)
    else:
        actual = rust_actual_inventory(root, preflight)
        actual_digest = actual["digest"]
        actual_source = None
    comparison = planned_actual_comparison(contract, actual, contract_digest=contract_record["digest"], actual_digest=actual_digest)
    disposition = comparison["disposition"]
    output["applicability"] = {"level": level, "disposition": "SUPPORTED", "rationale": contract.get("applicability", {}).get("rationale", "Profile-specific structure review applies.")}
    output["projection"] = {
        "fixed_decisions": contract.get("decisions", {}).get("fixed", []),
        "delegated_freedom": contract.get("decisions", {}).get("delegated", []),
        "comparison_policy": comparison.get("comparison_policy"),
    }
    coverage = [
        "artifact topology",
        "public/shared contracts",
        "state and ownership when represented",
        "fixed decisions when represented",
        "delegated private variation",
    ]
    output.update({
        "review_id": digest_value({"contract": contract_record["digest"], "candidate": candidate_record["digest"], "actual": actual_digest, "tier": assurance_tier})[:24],
        "candidate": candidate_record,
        "actual_inventory": {"digest": actual_digest, "source_sha256": actual_source, "schema": actual.get("schema")},
        "reviewer": {"kind": "focused-profile-review", "profile": PROFILE_ID},
        "assurance_tier": assurance_tier,
        "coverage": coverage,
        "findings": comparison["material_findings"] + comparison["advisory_findings"],
        "disposition": disposition,
        "comparison": comparison,
        "limitations": [
            "Filesystem and regex inventory cannot prove runtime protocol, persistence, unsafe, cancellation, or operational correctness.",
            "Compiler, tests, Miri, Loom, fuzzing, packaging, consumer, and operational evidence remain separate gates when applicable.",
        ],
    })
    return _finish(output)


def input_records(contract_paths: Sequence[Path], slice_paths: Sequence[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contracts = [load_contract(path)[1] for path in contract_paths]
    slices = [load_slice(path)[1] for path in slice_paths]
    return contracts, slices
