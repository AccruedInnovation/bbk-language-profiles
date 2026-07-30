#!/usr/bin/env python3
"""Deterministic alpha.4 implementation-structure support for BBK TS/JS.

The functions in this module project generic BBK objects into TypeScript and
JavaScript vocabulary. They do not mutate repositories, execute project tools,
grant authority, or declare verification success.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

TARGET_BBK_VERSION = "0.1.0-alpha.4"
PROFILE_ID = "typescript-javascript"
AUTHORITY_BOUNDARY = {
    "projection_is_authority": False,
    "may_declare_pass": False,
    "may_expand_work_scope": False,
    "may_grant_tools_or_effects": False,
    "may_reduce_assurance": False,
    "statement": (
        "This profile projection is a deterministic view over the generic BBK contract or slice. "
        "The generic object, repository authority, effect permissions, candidate identity, and BBK gate executor remain authoritative."
    ),
}
STRUCTURE_SCHEMA = "bbk.implementation-structure-contract.v1"
SLICE_SCHEMA = "bbk.execution-slice.v1"
INVENTORY_SCHEMA = "bbk.tsjs-actual-structure-inventory.v1"
TIERS = {"routine": 0, "material": 1, "consequential": 2, "critical": 3}
PUBLIC_ARTIFACT_KINDS = {
    "package", "entry-point", "public-entry-point", "declaration", "schema", "runtime-schema",
    "api", "public-api", "browser-bundle", "server-entry-point", "cli-entry-point", "plugin-entry-point",
    "extension-entry-point", "generated-declaration", "wire-schema", "migration",
}
SUPPORTED_TOUCHPOINTS = {
    "cli", "api", "ui", "report", "procedure", "simulation", "physical-observation",
    "document", "package", "protocol-trace", "other",
}


class StructureError(RuntimeError):
    """Expected profile structure error."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StructureError(f"missing JSON file: {path}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise StructureError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StructureError(f"expected a JSON object in {path}")
    return value


def _require_object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    return value


def _require_array(value: Any, path: str, errors: list[str], *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return []
    if nonempty and not value:
        errors.append(f"{path} must not be empty")
    return value


def validate_contract(value: Mapping[str, Any]) -> list[str]:
    """Bounded deterministic validation of fields consumed by this profile.

    BBK alpha.4 performs canonical schema validation. The profile repeats the
    minimum structural checks required to avoid projecting malformed input when
    invoked outside a full BBK host.
    """
    errors: list[str] = []
    if value.get("schema") != STRUCTURE_SCHEMA:
        errors.append(f"schema must be {STRUCTURE_SCHEMA!r}")
    for key in ["contractId", "revision", "title", "status", "subject", "applicability", "structure", "decisions", "review"]:
        if key not in value:
            errors.append(f"missing required field: {key}")
    for key in ["contractId", "revision", "title", "status"]:
        if key in value and not str(value.get(key) or "").strip():
            errors.append(f"{key} must be non-empty")
    applicability = _require_object(value.get("applicability"), "applicability", errors)
    if applicability.get("level") not in {"none", "inline", "contract"}:
        errors.append("applicability.level must be none, inline, or contract")
    _require_array(applicability.get("triggers"), "applicability.triggers", errors)
    if not str(applicability.get("rationale") or "").strip():
        errors.append("applicability.rationale must be non-empty")
    structure = _require_object(value.get("structure"), "structure", errors)
    for key in ["artifactTopology", "keyContracts", "behaviorPaths", "stateOwnership", "effectBoundaries", "testSeams", "observabilityPoints", "migrationTouchpoints"]:
        _require_array(structure.get(key), f"structure.{key}", errors)
    decisions = _require_object(value.get("decisions"), "decisions", errors)
    for key in ["fixed", "delegated", "prohibited"]:
        _require_array(decisions.get(key), f"decisions.{key}", errors)
    review = _require_object(value.get("review"), "review", errors)
    if review.get("assuranceTier") not in TIERS:
        errors.append("review.assuranceTier must be routine, material, consequential, or critical")
    _require_array(review.get("requiredReviewers"), "review.requiredReviewers", errors)
    _require_array(review.get("acceptanceCriteria"), "review.acceptanceCriteria", errors, nonempty=True)
    return errors


def validate_slice(value: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if value.get("schema") != SLICE_SCHEMA:
        errors.append(f"schema must be {SLICE_SCHEMA!r}")
    for key in [
        "sliceId", "title", "status", "parentCapabilityRefs", "structureContractRefs", "objective",
        "touchpoint", "flow", "workUnitRefs", "integrationOwner", "assertions", "entryConditions",
        "exitConditions", "atomicity", "scaffolding",
    ]:
        if key not in value:
            errors.append(f"missing required field: {key}")
    touchpoint = _require_object(value.get("touchpoint"), "touchpoint", errors)
    if touchpoint.get("kind") not in SUPPORTED_TOUCHPOINTS:
        errors.append("touchpoint.kind is unsupported")
    for key in ["actor", "interaction", "expectedObservation", "environment"]:
        if not str(touchpoint.get(key) or "").strip():
            errors.append(f"touchpoint.{key} must be non-empty")
    flow = _require_object(value.get("flow"), "flow", errors)
    _require_array(flow.get("participants"), "flow.participants", errors, nonempty=True)
    _require_array(flow.get("steps"), "flow.steps", errors, nonempty=True)
    _require_array(flow.get("interfaceRefs"), "flow.interfaceRefs", errors)
    _require_array(value.get("workUnitRefs"), "workUnitRefs", errors, nonempty=True)
    _require_array(value.get("assertions"), "assertions", errors, nonempty=True)
    atomicity = _require_object(value.get("atomicity"), "atomicity", errors)
    for key in ["coherent", "reviewable", "independentlyVerifiable", "containedOrReversible"]:
        if not isinstance(atomicity.get(key), bool):
            errors.append(f"atomicity.{key} must be boolean")
    if not str(atomicity.get("rationale") or "").strip():
        errors.append("atomicity.rationale must be non-empty")
    _require_array(value.get("scaffolding"), "scaffolding", errors)
    return errors


def validate_inventory(value: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if value.get("schema") != INVENTORY_SCHEMA:
        errors.append(f"schema must be {INVENTORY_SCHEMA!r}")
    for key in ["artifacts", "contracts", "fixedDecisions", "stateOwnership", "effectBoundaries", "packageSurfaces"]:
        if key not in value:
            errors.append(f"missing required inventory field: {key}")
        elif not isinstance(value.get(key), list):
            errors.append(f"inventory.{key} must be an array")
    return errors


def _with_output_digest(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result["output_digest"] = digest(result)
    return result


def _profile_record(profile: Mapping[str, Any]) -> dict[str, str]:
    return {"id": str(profile["id"]), "package": str(profile.get("package") or ""), "version": str(profile["version"])}


def _input_record(value: Mapping[str, Any], *, kind: str) -> dict[str, Any]:
    if kind == "contract":
        return {
            "kind": "ImplementationStructureContract",
            "id": value.get("contractId"),
            "revision": value.get("revision"),
            "digest": digest(value),
        }
    if kind == "slice":
        return {
            "kind": "ExecutionSlice",
            "id": value.get("sliceId"),
            "revision": None,
            "digest": digest(value),
        }
    raise StructureError(f"unsupported input kind: {kind}")


def _text_tokens(*values: Any) -> set[str]:
    text = " ".join(str(value) for value in values if value is not None).lower()
    return {token for token in re.split(r"[^a-z0-9_+-]+", text) if token}


def project_artifact_kind(kind: str, logical_path: str) -> str:
    raw = kind.strip().lower().replace("_", "-")
    path = logical_path.lower()
    name = Path(path).name
    if name == "package.json":
        return "package-manifest"
    if name.startswith("tsconfig") or name.startswith("jsconfig"):
        return "compiler-config"
    if name in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"}:
        return "dependency-lock"
    if ".d." in name or name.endswith(".d.ts"):
        return "declaration"
    if "schema" in name or "/schemas/" in path:
        return "runtime-schema" if path.endswith(('.ts', '.js', '.mts', '.mjs')) else "schema"
    if "/test" in path or "/__tests__/" in path or re.search(r"\.(test|spec)\.[cm]?[jt]sx?$", path):
        return "test"
    if "fixture" in path:
        return "fixture"
    if name in {"index.ts", "index.js", "index.mts", "index.mjs", "index.cts", "index.cjs"} and raw in {"adapter", "module", "entry-point"}:
        return "entry-point"
    aliases = {
        "request-type": "type-contract", "result-type": "type-contract", "message": "message-contract",
        "event": "event-contract", "component": "ui-component", "adapter": "adapter", "module": "module",
        "package": "package", "test": "test", "declaration": "declaration", "schema": "schema",
        "runtime-schema": "runtime-schema", "entry-point": "entry-point", "generated": "generated-artifact",
        "worker": "worker", "service": "service", "hook": "hook", "plugin": "plugin", "extension": "extension",
    }
    return aliases.get(raw, raw or "artifact")


def _contract_representation(item: Mapping[str, Any]) -> dict[str, Any]:
    kind = str(item.get("kind") or "contract")
    name = str(item.get("name") or item.get("id") or "contract")
    visibility = str(item.get("visibility") or "internal")
    tokens = _text_tokens(kind, name, item.get("shape"), item.get("responsibility"), *(item.get("invariants") or []), *(item.get("failureSemantics") or []))
    untrusted = bool(tokens & {"json", "http", "rpc", "message", "event", "webhook", "config", "environment", "database", "storage", "cookie", "header", "cli", "ipc", "postmessage", "wire", "schema"})
    closed = bool(tokens & {"closed", "enum", "state", "status", "outcome", "result", "discriminated", "variant"})
    identity = bool(tokens & {"identity", "identifier", "id", "path", "url", "scope", "key"})
    ownership = bool(tokens & {"owner", "ownership", "resource", "subscription", "timer", "worker", "stream", "abort", "cleanup"})
    suggestions: list[str] = []
    if closed:
        suggestions.append("Use a discriminated union or closed literal/enum representation with exhaustive handling where the state space is genuinely closed.")
    if identity:
        suggestions.append("Use a branded or opaque identity only when interchangeability would violate a real invariant; otherwise retain a documented primitive.")
    if untrusted:
        suggestions.append("Define one runtime parser/schema at the trust boundary and derive or verify static types from the same authoritative shape.")
    if ownership:
        suggestions.append("Make resource creation, cancellation, cleanup, and mutation ownership explicit in the public or shared contract.")
    if not suggestions:
        suggestions.append("Use the narrowest explicit TypeScript/JSDoc shape that localizes the listed invariants without introducing ceremonial wrappers.")
    return {
        "id": item.get("id"),
        "kind": kind,
        "name": name,
        "visibility": visibility,
        "planned_shape": item.get("shape"),
        "responsibility": item.get("responsibility"),
        "invariants": list(item.get("invariants") or []),
        "failure_semantics": list(item.get("failureSemantics") or []),
        "static_representation_guidance": suggestions,
        "runtime_validation_required": untrusted,
        "consumer_evidence_required": visibility in {"shared", "public", "external"},
        "static_notation_limit": (
            "TypeScript and JSDoc shapes are erased or advisory at runtime; external values, package resolution, emitted output, and host behavior require runtime or consumer evidence."
        ),
    }


def structure_projection(
    root: Path,
    contract: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    role: str,
    task_profile: str,
    assurance_tier: str,
    preflight: Mapping[str, Any] | None,
) -> dict[str, Any]:
    errors = validate_contract(contract)
    level = str((contract.get("applicability") or {}).get("level") or "none")
    blockers = [f"generic contract validation: {error}" for error in errors]
    disposition = "BLOCKED" if errors else ("NOT_APPLICABLE" if level == "none" else "SUPPORTED")
    structure = contract.get("structure") if isinstance(contract.get("structure"), dict) else {}
    artifacts = []
    for item in structure.get("artifactTopology", []) if isinstance(structure, dict) else []:
        if not isinstance(item, dict):
            continue
        path = str(item.get("logicalPath") or "")
        artifact_kind = project_artifact_kind(str(item.get("kind") or "artifact"), path)
        artifacts.append({
            "id": item.get("id"), "action": item.get("action"), "generic_kind": item.get("kind"),
            "tsjs_kind": artifact_kind, "logical_path": path, "owner": item.get("owner"),
            "responsibility": item.get("responsibility"), "source_refs": list(item.get("sourceRefs") or []),
            "material_surface": artifact_kind in PUBLIC_ARTIFACT_KINDS or Path(path).name in {"package.json", "tsconfig.json", "jsconfig.json"},
        })
    contracts = [_contract_representation(item) for item in structure.get("keyContracts", []) if isinstance(item, dict)] if isinstance(structure, dict) else []
    state_projection = []
    for item in structure.get("stateOwnership", []) if isinstance(structure, dict) else []:
        if not isinstance(item, dict):
            continue
        tokens = _text_tokens(item.get("state"), item.get("concurrency"), item.get("recovery"), item.get("lifetime"))
        state_projection.append({
            "state": item.get("state"), "owner": item.get("owner"), "lifetime": item.get("lifetime"),
            "mutation_authority": item.get("mutationAuthority"), "consistency": item.get("consistency"),
            "concurrency": item.get("concurrency"), "recovery": item.get("recovery"),
            "tsjs_guidance": [
                "Represent closed lifecycle states as a discriminated union or explicit state machine when illegal transitions are material.",
                "Do not hide mutable singleton, subscription, timer, worker, stream, cache, or process ownership behind module import side effects.",
                "Propagate AbortSignal or an equivalent explicit cancellation contract when work may outlive its caller.",
            ] if tokens & {"async", "concurrency", "timer", "stream", "worker", "subscription", "process", "cancellation", "abort"} else [
                "Keep the source of truth and mutation authority in one named package/module boundary; static types do not enforce runtime ownership."
            ],
        })
    behavior = []
    for item in structure.get("behaviorPaths", []) if isinstance(structure, dict) else []:
        if not isinstance(item, dict):
            continue
        behavior.append({
            "id": item.get("id"), "name": item.get("name"), "trigger": item.get("trigger"),
            "steps": list(item.get("steps") or []), "success": item.get("success"),
            "failure_and_recovery": list(item.get("failureAndRecovery") or []),
            "tsjs_review_focus": [
                "Check static type flow separately from runtime parsing and emitted artifact behavior.",
                "Check promise rejection, cancellation, cleanup, stream/backpressure, timer, worker, and process ownership where present.",
                "Check package/export-map and host resolution at every public or plugin boundary.",
            ],
        })
    effects = []
    for item in structure.get("effectBoundaries", []) if isinstance(structure, dict) else []:
        if not isinstance(item, dict):
            continue
        effects.append({
            **{key: item.get(key) for key in ["effect", "owner", "authorization", "idempotency", "failure", "recovery"]},
            "tsjs_review_focus": [
                "Treat package installation, lifecycle scripts, code generation, child processes, network, filesystem, browser storage, and host APIs as explicit effects.",
                "A type declaration or lint rule does not grant or contain an effect.",
            ],
        })
    fixed = [
        {"id": item.get("id"), "statement": item.get("statement"), "rationale": item.get("rationale"), "change_route": item.get("changeRoute"), "source_refs": list(item.get("sourceRefs") or [])}
        for item in ((contract.get("decisions") or {}).get("fixed") or []) if isinstance(item, dict)
    ]
    delegated = [
        {"area": item.get("area"), "bounds": item.get("bounds")}
        for item in ((contract.get("decisions") or {}).get("delegated") or []) if isinstance(item, dict)
    ]
    type_concepts = {
        "identity": "Branded/opaque identities are appropriate only when exchanging two structurally identical values would violate a material invariant.",
        "state": "Use discriminated unions, closed literals/enums, or an explicit state machine for consequential closed states and transitions.",
        "boundary": "Keep exported static types, runtime schemas/parsers, emitted declarations, package exports, and consumer behavior synchronized but evidence-distinct.",
        "ownership": "Name the package/module that owns mutation plus timer, subscription, worker, stream, process, cache, and AbortSignal lifetime.",
        "failure": "Represent caller-relevant failure classes explicitly; do not rely on broad thrown Error text where handling, retry, or recovery differs.",
        "evidence": "Use distinct statuses for not-run, blocked, error, inconclusive, pass, and fail in gate and validator results.",
        "type_depth_test": "Add a type or abstraction only when it prevents a material invalid combination, localizes an invariant, clarifies ownership, stabilizes a boundary, improves change locality, creates a real test seam, or hides consequential complexity.",
        "runtime_limit": "TypeScript types are erased and JavaScript annotations are not runtime validators; runtime, package-consumer, browser, host, and operational evidence remain required where applicable.",
    }
    projection = {
        "subject_kind": (contract.get("subject") or {}).get("kind"),
        "artifact_topology": artifacts,
        "key_contracts": contracts,
        "type_concepts": type_concepts,
        "behavior_paths": behavior,
        "state_ownership": state_projection,
        "effect_boundaries": effects,
        "test_seams": list(structure.get("testSeams") or []) if isinstance(structure, dict) else [],
        "observability_points": list(structure.get("observabilityPoints") or []) if isinstance(structure, dict) else [],
        "migration_touchpoints": list(structure.get("migrationTouchpoints") or []) if isinstance(structure, dict) else [],
        "fixed_decisions": fixed,
        "delegated_freedom": delegated,
        "prohibited_shortcuts": list((contract.get("decisions") or {}).get("prohibited") or []),
        "review_policy": contract.get("review"),
        "planned_actual_materiality": {
            "material": [
                "public or shared export/declaration/package surface",
                "runtime schema or serialized-data contract",
                "state/effect/resource owner",
                "async cancellation and cleanup ownership",
                "fixed decision or prohibited shortcut",
                "entry-point, host/plugin, migration, or package-consumer shape",
            ],
            "normally_delegated": [
                "private helper names and placement",
                "local iteration style",
                "private test utility placement",
                "equivalent internal refactors within the stated ownership and behavioral bounds",
            ],
        },
    }
    unsupported: list[str] = []
    subject_kind = str((contract.get("subject") or {}).get("kind") or "")
    if subject_kind and subject_kind not in {"software", "typescript", "javascript", "mixed", "package", "application", "extension"}:
        unsupported.append(f"The subject kind {subject_kind!r} is only partially covered; adjacent non-TS/JS obligations remain outside this profile.")
    if unsupported and disposition == "SUPPORTED":
        disposition = "PARTIAL"
    advisories: list[str] = []
    if level == "inline":
        advisories.append("Keep the projection compact in the work unit; do not create a separate profile-owned source of truth.")
    if level == "contract" and not fixed:
        advisories.append("The contract has no fixed decisions; confirm that consequential ownership and boundary choices are not accidentally left implicit.")
    if not contracts and level == "contract":
        advisories.append("No key contracts are declared; independent work may still need an explicit shared type, runtime schema, export, event, or resource contract.")
    return _with_output_digest({
        "schema": "bbk.tsjs-implementation-structure-projection.v1",
        "profile": _profile_record(profile),
        "bbk_version": TARGET_BBK_VERSION,
        "input": _input_record(contract, kind="contract"),
        "preflight_digest": preflight.get("digest") if isinstance(preflight, Mapping) else None,
        "invocation": {"role": role, "task_profile": task_profile, "assurance_tier": assurance_tier},
        "applicability": {"generic_level": level, "disposition": disposition, "rationale": (contract.get("applicability") or {}).get("rationale")},
        "projection": projection,
        "unsupported_or_uncertain": unsupported + [str(item.get("statement") or item) for item in contract.get("uncertainties", []) if isinstance(item, (dict, str))],
        "advisories": advisories,
        "blockers": blockers,
        "authority": AUTHORITY_BOUNDARY,
    })


def _touchpoint_evidence(touchpoint: Mapping[str, Any]) -> list[str]:
    kind = str(touchpoint.get("kind") or "other")
    mapping = {
        "cli": ["Run the built CLI artifact, assert exit status/stdout/stderr, and bind the receipt to the exact candidate."],
        "api": ["Exercise an actual request/response or callable consumer with runtime validation and failure fixtures."],
        "ui": ["Exercise the production bundle in a qualified real browser or host, including accessibility and failure behavior where applicable."],
        "package": ["Pack the distributable artifact, install it in a clean consumer, resolve declarations, and load every claimed module condition."],
        "protocol-trace": ["Capture the exact host/runtime protocol exchange, cancellation/failure behavior, and correlation identifiers."],
        "report": ["Generate and inspect the exact report artifact with a deterministic fixture and declared comparison policy."],
        "document": ["Review the exact document package against acceptance criteria and consumer/handoff needs."],
        "simulation": ["Run the qualified simulator or deterministic model and preserve the input, environment, and trace."],
        "procedure": ["Conduct a structured walkthrough or rehearsal with named participants and evidence capture."],
        "physical-observation": ["Use qualified physical measurement and preserve calibration/environment identity."],
        "other": ["Define a concrete inspectable observation and the exact evidence that proves it occurred."],
    }
    return mapping.get(kind, mapping["other"])


def slice_projection(
    root: Path,
    slice_value: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    role: str,
    task_profile: str,
    assurance_tier: str,
    preflight: Mapping[str, Any] | None,
) -> dict[str, Any]:
    errors = validate_slice(slice_value)
    touchpoint = slice_value.get("touchpoint") if isinstance(slice_value.get("touchpoint"), dict) else {}
    blockers = [f"generic execution slice validation: {error}" for error in errors]
    disposition = "BLOCKED" if errors else "SUPPORTED"
    text = " ".join([str(slice_value.get("title") or ""), str(slice_value.get("objective") or ""), *[str(step) for step in ((slice_value.get("flow") or {}).get("steps") or [])]]).lower()
    foundation_tokens = {"foundation", "infrastructure", "scaffold", "tooling", "types-only", "schema-only", "framework"}
    looks_foundational = any(token in text for token in foundation_tokens)
    metadata = slice_value.get("metadata") if isinstance(slice_value.get("metadata"), dict) else {}
    foundation_exception = metadata.get("foundationException") or metadata.get("foundation_exception")
    atomicity = slice_value.get("atomicity") if isinstance(slice_value.get("atomicity"), dict) else {}
    if looks_foundational and not foundation_exception:
        sequencing = "HORIZONTAL_RISK"
    elif looks_foundational:
        sequencing = "FOUNDATION_EXCEPTION"
    else:
        sequencing = "INTEGRATED_TOUCHPOINT"
    advisories: list[str] = []
    if sequencing == "HORIZONTAL_RISK":
        advisories.append("The slice appears foundation-first. Name the feasibility/safety risk retired, its own touchpoint, and the next integrated slice it enables.")
    if not all(bool(atomicity.get(key)) for key in ["coherent", "reviewable", "independentlyVerifiable", "containedOrReversible"]):
        blockers.append("slice atomicity does not establish coherence, reviewability, independent verification, and containment/reversibility")
        disposition = "BLOCKED"
    assertions = []
    for item in slice_value.get("assertions", []) if isinstance(slice_value.get("assertions"), list) else []:
        if isinstance(item, dict):
            assertions.append({
                "id": item.get("id"), "statement": item.get("statement"), "method": item.get("method"),
                "planned_evidence": item.get("evidence"), "tsjs_evidence_class": (
                    "static" if item.get("method") in {"analysis", "inspection", "review"} else "runtime-or-consumer"
                ),
            })
    scaffolding = []
    for item in slice_value.get("scaffolding", []) if isinstance(slice_value.get("scaffolding"), list) else []:
        if isinstance(item, dict):
            risk = "bounded" if item.get("disposition") in {"remove-in-slice", "remove-by-slice", "retain-as-fixture", "review-for-promotion", "none"} else "unknown"
            scaffolding.append({**item, "risk": risk, "tsjs_examples": ["path alias", "fixture adapter", "mock server", "generated declaration", "temporary package export", "test-only runtime shim"]})
    flow = slice_value.get("flow") if isinstance(slice_value.get("flow"), dict) else {}
    dependency_closure = sorted(set(
        [str(item) for item in slice_value.get("dependencies", [])]
        + [str(item) for item in slice_value.get("structureContractRefs", [])]
        + [str(item) for item in slice_value.get("workUnitRefs", [])]
        + [str(item) for item in flow.get("architectureRefs", [])]
        + [str(item) for item in flow.get("interfaceRefs", [])]
    ))
    touchpoint_kind = str(touchpoint.get("kind") or "other")
    review_packs = ["tsjs-implementation-structure-review", "tsjs-evidence-reproducer"]
    if touchpoint_kind in {"package", "protocol-trace"}:
        review_packs.append("tsjs-api-module-package-review")
    if touchpoint_kind == "ui":
        review_packs.append("tsjs-browser-ui-review")
    if _text_tokens(text) & {"async", "abort", "stream", "timer", "worker", "subscription", "process", "cancellation"}:
        review_packs.append("tsjs-async-resource-failure-review")
    projection = {
        "touchpoint": {**touchpoint, "required_evidence": _touchpoint_evidence(touchpoint)},
        "dependency_closure": dependency_closure,
        "participants": list(flow.get("participants") or []),
        "steps": list(flow.get("steps") or []),
        "work_units": list(slice_value.get("workUnitRefs") or []),
        "integration_owner": slice_value.get("integrationOwner"),
        "assertions": assertions,
        "scaffolding": scaffolding,
        "sequencing_assessment": {
            "classification": sequencing,
            "looks_foundational": looks_foundational,
            "foundation_exception": foundation_exception,
            "next_integrated_slice_ref": metadata.get("nextIntegratedSliceRef") or metadata.get("next_integrated_slice_ref"),
        },
        "candidate_boundary": {
            "recommendation": "Freeze one exact candidate or tightly coupled validation cohort after all work units needed for this touchpoint are integrated.",
            "work_unit_refs": list(slice_value.get("workUnitRefs") or []),
            "do_not_split_by": ["one file", "one function", "one agent", "arbitrary line count"],
        },
        "validation_boundary": {
            "assertion_ids": [item.get("id") for item in assertions],
            "focused_review_packs": list(dict.fromkeys(review_packs)),
            "mechanical_then_semantic": True,
        },
    }
    return _with_output_digest({
        "schema": "bbk.tsjs-execution-slice-projection.v1",
        "profile": _profile_record(profile),
        "bbk_version": TARGET_BBK_VERSION,
        "input": _input_record(slice_value, kind="slice"),
        "preflight_digest": preflight.get("digest") if isinstance(preflight, Mapping) else None,
        "invocation": {"role": role, "task_profile": task_profile, "assurance_tier": assurance_tier},
        "applicability": {"disposition": disposition},
        "projection": projection,
        "unsupported_or_uncertain": [],
        "advisories": advisories,
        "blockers": blockers,
        "authority": AUTHORITY_BOUNDARY,
    })


def _candidate_paths(candidate: Mapping[str, Any]) -> set[str]:
    paths: set[str] = set()
    files = candidate.get("files")
    if isinstance(files, list):
        for item in files:
            if isinstance(item, dict) and item.get("path"):
                paths.add(str(item["path"]).lstrip("./"))
            elif isinstance(item, str):
                paths.add(item.lstrip("./"))
    manifest = candidate.get("manifest")
    if isinstance(manifest, dict):
        paths |= _candidate_paths(manifest)
    return paths


def _package_surfaces(root: Path) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for path in sorted(root.rglob("package.json")):
        if any(part in {"node_modules", ".git", ".jj", ".bbk", "dist", "build", "out"} for part in path.relative_to(root).parts):
            continue
        try:
            package = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(package, dict):
            continue
        values.append({
            "path": path.relative_to(root).as_posix(),
            "name": package.get("name"),
            "type": package.get("type"),
            "exports": package.get("exports"),
            "imports": package.get("imports"),
            "types": package.get("types") or package.get("typings"),
            "main": package.get("main"),
            "module": package.get("module"),
            "browser": package.get("browser"),
            "bin": package.get("bin"),
            "files": package.get("files"),
        })
    return values


def build_actual_inventory(root: Path, contract: Mapping[str, Any], candidate: Mapping[str, Any], explicit: Mapping[str, Any] | None = None) -> dict[str, Any]:
    candidate_paths = _candidate_paths(candidate)
    artifacts: list[dict[str, Any]] = []
    structure = contract.get("structure") if isinstance(contract.get("structure"), dict) else {}
    for item in structure.get("artifactTopology", []) if isinstance(structure, dict) else []:
        if not isinstance(item, dict):
            continue
        rel = str(item.get("logicalPath") or "").lstrip("./")
        path = root / rel
        exists = rel in candidate_paths if candidate_paths else path.is_file()
        record: dict[str, Any] = {
            "planned_id": item.get("id"), "path": rel, "exists": exists,
            "observed_kind": project_artifact_kind(str(item.get("kind") or "artifact"), rel),
            "visibility": "unknown",
        }
        if path.is_file():
            record.update({"bytes": path.stat().st_size, "sha256": sha256_file(path)})
        artifacts.append(record)
    inventory: dict[str, Any] = {
        "schema": INVENTORY_SCHEMA,
        "root": str(root),
        "candidate_digest": digest(candidate),
        "artifacts": artifacts,
        "contracts": [],
        "fixedDecisions": [],
        "stateOwnership": [],
        "effectBoundaries": [],
        "packageSurfaces": _package_surfaces(root),
        "notes": ["Automatically derived inventory proves file/package observations only; semantic conformance may require an agent, consumer fixture, or tool-authoritative inventory."],
    }
    if explicit:
        errors = validate_inventory(explicit)
        if errors:
            raise StructureError("invalid actual inventory: " + "; ".join(errors))
        for key in ["artifacts", "contracts", "fixedDecisions", "stateOwnership", "effectBoundaries", "packageSurfaces"]:
            if explicit.get(key):
                inventory[key] = explicit[key]
        inventory["notes"] = list(inventory.get("notes") or []) + list(explicit.get("notes") or [])
        inventory["explicit_inventory_digest"] = digest(explicit)
    inventory["digest"] = digest({key: value for key, value in inventory.items() if key != "digest"})
    return inventory


def _inventory_index(items: Iterable[Mapping[str, Any]], keys: Sequence[str]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in items:
        for key in keys:
            value = item.get(key)
            if value:
                result[str(value)] = item
                break
    return result


def compare_planned_actual(
    contract: Mapping[str, Any],
    inventory: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    preflight_digest: str | None,
    assurance_tier: str,
) -> dict[str, Any]:
    level = str((contract.get("applicability") or {}).get("level") or "none")
    if level == "none":
        return _with_output_digest({
            "schema": "bbk.tsjs-planned-actual-structure-comparison.v1",
            "profile": _profile_record(profile), "bbk_version": TARGET_BBK_VERSION,
            "input": _input_record(contract, kind="contract"), "preflight_digest": preflight_digest,
            "inventory_digest": inventory.get("digest"), "applicability": "NOT_APPLICABLE",
            "disposition": "NOT_APPLICABLE", "differences": [], "unknowns": [], "within_delegated_freedom": [],
            "summary": {"material": 0, "advisory": 0, "unknown": 0, "delegated": 0},
            "authority": AUTHORITY_BOUNDARY,
        })
    artifact_index = _inventory_index([item for item in inventory.get("artifacts", []) if isinstance(item, Mapping)], ["planned_id", "path"])
    contract_index = _inventory_index([item for item in inventory.get("contracts", []) if isinstance(item, Mapping)], ["id", "name"])
    decision_index = _inventory_index([item for item in inventory.get("fixedDecisions", []) if isinstance(item, Mapping)], ["id"])
    state_index = _inventory_index([item for item in inventory.get("stateOwnership", []) if isinstance(item, Mapping)], ["state", "id"])
    effect_index = _inventory_index([item for item in inventory.get("effectBoundaries", []) if isinstance(item, Mapping)], ["effect", "id"])
    differences: list[dict[str, Any]] = []
    unknowns: list[dict[str, Any]] = []
    delegated: list[dict[str, Any]] = []
    structure = contract.get("structure") if isinstance(contract.get("structure"), dict) else {}
    for item in structure.get("artifactTopology", []) if isinstance(structure, dict) else []:
        if not isinstance(item, dict):
            continue
        key = str(item.get("id") or item.get("logicalPath"))
        actual = artifact_index.get(key) or artifact_index.get(str(item.get("logicalPath") or ""))
        action = str(item.get("action") or "inspect")
        should_exist = action not in {"remove"}
        exists = bool(actual and actual.get("exists"))
        projected_kind = project_artifact_kind(str(item.get("kind") or "artifact"), str(item.get("logicalPath") or ""))
        material = projected_kind in PUBLIC_ARTIFACT_KINDS or Path(str(item.get("logicalPath") or "")).name in {"package.json", "tsconfig.json", "jsconfig.json"}
        if should_exist != exists:
            differences.append({
                "class": "MATERIAL" if material else "ADVISORY",
                "kind": "artifact-presence",
                "planned_ref": item.get("id"), "path": item.get("logicalPath"),
                "expected": "present" if should_exist else "absent", "observed": "present" if exists else "absent",
                "reason": "Public/shared/package/configuration artifact" if material else "Private/internal topology is normally delegated unless a fixed decision says otherwise.",
            })
    for item in structure.get("keyContracts", []) if isinstance(structure, dict) else []:
        if not isinstance(item, dict):
            continue
        actual = contract_index.get(str(item.get("id")))
        visibility = str(item.get("visibility") or "internal")
        if actual and str(actual.get("status") or "").upper() in {"CONFORMS", "PASS", "MATCH"}:
            continue
        if actual and str(actual.get("status") or "").upper() in {"DIVERGES", "FAIL", "MISMATCH"}:
            differences.append({
                "class": "MATERIAL" if visibility in {"shared", "public", "external"} else "ADVISORY",
                "kind": "key-contract",
                "planned_ref": item.get("id"), "name": item.get("name"),
                "expected": item.get("shape"), "observed": actual.get("observedShape") or actual.get("observed_shape"),
                "reason": actual.get("reason") or "actual contract inventory reports divergence",
            })
        else:
            unknowns.append({
                "kind": "key-contract", "planned_ref": item.get("id"), "name": item.get("name"),
                "required": visibility in {"shared", "public", "external"},
                "reason": "No tool-, consumer-, or reviewer-backed actual contract observation was supplied.",
            })
    for item in ((contract.get("decisions") or {}).get("fixed") or []):
        if not isinstance(item, dict):
            continue
        actual = decision_index.get(str(item.get("id")))
        if actual and str(actual.get("status") or "").upper() in {"CONFORMS", "PASS", "MATCH"}:
            continue
        if actual and str(actual.get("status") or "").upper() in {"DIVERGES", "FAIL", "MISMATCH"}:
            differences.append({
                "class": "MATERIAL", "kind": "fixed-decision", "planned_ref": item.get("id"),
                "expected": item.get("statement"), "observed": actual.get("observed"),
                "reason": actual.get("reason") or "actual inventory reports a fixed-decision divergence",
                "change_route": item.get("changeRoute"),
            })
        else:
            unknowns.append({
                "kind": "fixed-decision", "planned_ref": item.get("id"), "required": True,
                "reason": "No actual conformance observation was supplied for this fixed decision.",
            })
    for item in structure.get("stateOwnership", []) if isinstance(structure, dict) else []:
        if not isinstance(item, dict):
            continue
        actual = state_index.get(str(item.get("state")))
        if actual and str(actual.get("status") or "").upper() in {"DIVERGES", "FAIL", "MISMATCH"}:
            differences.append({
                "class": "MATERIAL", "kind": "state-ownership", "planned_ref": item.get("state"),
                "expected": item.get("owner"), "observed": actual.get("observedOwner") or actual.get("observed_owner"),
                "reason": actual.get("reason") or "state owner differs from the planned owner",
            })
        elif not actual:
            unknowns.append({"kind": "state-ownership", "planned_ref": item.get("state"), "required": TIERS.get(assurance_tier, 0) >= TIERS["material"], "reason": "No state-ownership observation supplied."})
    for item in structure.get("effectBoundaries", []) if isinstance(structure, dict) else []:
        if not isinstance(item, dict):
            continue
        actual = effect_index.get(str(item.get("effect")))
        if actual and str(actual.get("status") or "").upper() in {"DIVERGES", "FAIL", "MISMATCH"}:
            differences.append({
                "class": "MATERIAL", "kind": "effect-boundary", "planned_ref": item.get("effect"),
                "expected": item.get("owner"), "observed": actual.get("observedOwner") or actual.get("observed_owner"),
                "reason": actual.get("reason") or "effect owner or policy differs from the planned boundary",
            })
        elif not actual:
            unknowns.append({"kind": "effect-boundary", "planned_ref": item.get("effect"), "required": TIERS.get(assurance_tier, 0) >= TIERS["consequential"], "reason": "No effect-boundary observation supplied."})
    # Extra artifacts are explicitly delegated unless another independent quality finding applies.
    planned_paths = {str(item.get("logicalPath") or "") for item in structure.get("artifactTopology", []) if isinstance(item, dict)} if isinstance(structure, dict) else set()
    for item in inventory.get("artifacts", []):
        if isinstance(item, Mapping) and item.get("path") and str(item.get("path")) not in planned_paths and item.get("exists"):
            delegated.append({"kind": "additional-private-artifact", "path": item.get("path"), "reason": "Extra private implementation detail is within delegated freedom unless it changes a fixed/public boundary."})
    material_count = sum(1 for item in differences if item["class"] == "MATERIAL")
    advisory_count = sum(1 for item in differences if item["class"] == "ADVISORY")
    blocking_unknowns = [item for item in unknowns if item.get("required")]
    if material_count:
        disposition = "MATERIAL_DIVERGENCE"
    elif blocking_unknowns:
        disposition = "BLOCKED"
    elif advisory_count:
        disposition = "ADVISORY_DIVERGENCE"
    else:
        disposition = "CONFORMS"
    return _with_output_digest({
        "schema": "bbk.tsjs-planned-actual-structure-comparison.v1",
        "profile": _profile_record(profile), "bbk_version": TARGET_BBK_VERSION,
        "input": _input_record(contract, kind="contract"), "preflight_digest": preflight_digest,
        "inventory_digest": inventory.get("digest"), "applicability": "APPLICABLE",
        "disposition": disposition, "differences": differences, "unknowns": unknowns,
        "within_delegated_freedom": delegated,
        "summary": {"material": material_count, "advisory": advisory_count, "unknown": len(unknowns), "blocking_unknown": len(blocking_unknowns), "delegated": len(delegated)},
        "authority": AUTHORITY_BOUNDARY,
    })


def structure_review(
    root: Path,
    contract: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    assurance_tier: str,
    preflight: Mapping[str, Any] | None,
    actual_inventory: Mapping[str, Any] | None,
) -> dict[str, Any]:
    contract_errors = validate_contract(contract)
    if contract_errors:
        comparison = _with_output_digest({
            "schema": "bbk.tsjs-planned-actual-structure-comparison.v1",
            "profile": _profile_record(profile), "bbk_version": TARGET_BBK_VERSION,
            "input": _input_record(contract, kind="contract"),
            "preflight_digest": preflight.get("digest") if isinstance(preflight, Mapping) else None,
            "inventory_digest": None, "applicability": "BLOCKED", "disposition": "BLOCKED",
            "differences": [], "unknowns": [{"kind": "invalid-contract", "reason": error, "required": True} for error in contract_errors],
            "within_delegated_freedom": [], "summary": {"material": 0, "advisory": 0, "unknown": len(contract_errors), "blocking_unknown": len(contract_errors), "delegated": 0},
            "authority": AUTHORITY_BOUNDARY,
        })
        inventory = None
    else:
        inventory = build_actual_inventory(root, contract, candidate, actual_inventory)
        comparison = compare_planned_actual(contract, inventory, profile=profile, preflight_digest=preflight.get("digest") if isinstance(preflight, Mapping) else None, assurance_tier=assurance_tier)
    findings = []
    for item in comparison.get("differences", []):
        findings.append({
            "class": item.get("class"), "kind": item.get("kind"), "affected_reference": item.get("planned_ref"),
            "expected": item.get("expected"), "observed": item.get("observed"), "reason": item.get("reason"),
            "smallest_valid_route": item.get("change_route") or ("contract/impact review" if item.get("class") == "MATERIAL" else "update at the next safe point or accept as delegated"),
        })
    blockers = [item.get("reason") for item in comparison.get("unknowns", []) if item.get("required")]
    result = {
        "schema": "bbk.tsjs-structure-review-result.v1",
        "profile": _profile_record(profile), "bbk_version": TARGET_BBK_VERSION,
        "input": _input_record(contract, kind="contract"),
        "candidate": {"digest": digest(candidate), "declared_id": candidate.get("candidate_id") or candidate.get("id")},
        "preflight_digest": preflight.get("digest") if isinstance(preflight, Mapping) else None,
        "actual_inventory_digest": inventory.get("digest") if inventory else None,
        "applicability": comparison.get("applicability"),
        "disposition": comparison.get("disposition"),
        "comparison": comparison,
        "findings": findings,
        "advisories": [item.get("reason") for item in comparison.get("differences", []) if item.get("class") == "ADVISORY"],
        "blockers": blockers,
        "unsupported_or_uncertain": [item for item in comparison.get("unknowns", []) if not item.get("required")],
        "authority": AUTHORITY_BOUNDARY,
    }
    return _with_output_digest(result)
