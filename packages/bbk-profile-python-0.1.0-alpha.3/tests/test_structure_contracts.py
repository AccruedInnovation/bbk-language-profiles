from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tools" / "bbk_python.py"
FIXTURE = ROOT / "fixtures" / "python-project"
A4 = ROOT / "fixtures" / "alpha4"
CONTRACT_SCHEMA = json.loads((ROOT / "schemas" / "bbk-implementation-structure-contract-v1.schema.json").read_text(encoding="utf-8"))
SLICE_SCHEMA = json.loads((ROOT / "schemas" / "bbk-execution-slice-v1.schema.json").read_text(encoding="utf-8"))


def run(command, *, env=None, check=True):
    return subprocess.run(
        [str(item) for item in command], cwd=ROOT, env=env, check=check,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
    )


def run_json(command, *, env=None, check=True):
    result = run(command, env=env, check=check)
    return json.loads(result.stdout), result


def contract(name: str) -> Path:
    return A4 / "contracts" / name


def slice_path(name: str) -> Path:
    return A4 / "slices" / name


def inventory(name: str) -> Path:
    return A4 / "inventories" / name


class PythonStructureContractTests(unittest.TestCase):
    def test_generic_positive_and_negative_fixtures(self):
        cvalidator = Draft202012Validator(CONTRACT_SCHEMA)
        svalidator = Draft202012Validator(SLICE_SCHEMA)
        for path in sorted((A4 / "contracts").glob("*.json")):
            errors = list(cvalidator.iter_errors(json.loads(path.read_text(encoding="utf-8"))))
            self.assertFalse(errors, f"{path}: {[item.message for item in errors]}")
        for path in sorted((A4 / "slices").glob("*.json")):
            errors = list(svalidator.iter_errors(json.loads(path.read_text(encoding="utf-8"))))
            self.assertFalse(errors, f"{path}: {[item.message for item in errors]}")
        invalid = json.loads((A4 / "negative" / "invalid-contract.json").read_text(encoding="utf-8"))
        self.assertTrue(list(cvalidator.iter_errors(invalid)))
        invalid_slice = json.loads((A4 / "negative" / "invalid-slice.json").read_text(encoding="utf-8"))
        self.assertTrue(list(svalidator.iter_errors(invalid_slice)))
        invalid_contract_result = run([sys.executable, CLI, "--json", "structure", "--root", FIXTURE, "--contract", A4 / "negative" / "invalid-contract.json"], check=False)
        self.assertNotEqual(invalid_contract_result.returncode, 0)
        self.assertIn("contractId", json.loads(invalid_contract_result.stdout)["error"])
        invalid_slice_result = run([sys.executable, CLI, "--json", "slice", "--root", FIXTURE, "--slice", A4 / "negative" / "invalid-slice.json"], check=False)
        self.assertNotEqual(invalid_slice_result.returncode, 0)
        self.assertIn("sliceId", json.loads(invalid_slice_result.stdout)["error"])

    def test_alpha3_predecessor_remains_schema_valid_and_legacy_unprojected(self):
        profile_schema = json.loads((ROOT / "schemas" / "bbk-language-profile-v1.schema.json").read_text(encoding="utf-8"))
        predecessor = json.loads((ROOT / "sources" / "predecessor-PROFILE.json").read_text(encoding="utf-8"))
        expectation = json.loads((A4 / "legacy" / "alpha3-profile-expected.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(profile_schema).iter_errors(predecessor))
        self.assertFalse(errors, [item.message for item in errors])
        support = predecessor.get("capabilities", {}).get("implementation_structure", {}).get("status", "legacy-unprojected")
        self.assertEqual(support, expectation["implementation_structure_support"])
        self.assertFalse(expectation["structure_projection_claims_permitted"])

    def test_profile_namespaced_schemas_parse_and_required_outputs_validate(self):
        for name in [
            "bbk-python-implementation-structure-projection-v1.schema.json",
            "bbk-python-execution-slice-projection-v1.schema.json",
            "bbk-python-planned-actual-structure-comparison-v1.schema.json",
            "bbk-python-structure-review-result-v1.schema.json",
            "bbk-python-actual-structure-inventory-v1.schema.json",
        ]:
            schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)

        structure, _ = run_json([
            sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
            "--contract", contract("public-typed-package.json"), "--role", "architect",
        ])
        Draft202012Validator(json.loads((ROOT / "schemas" / "bbk-python-implementation-structure-projection-v1.schema.json").read_text(encoding="utf-8"))).validate(structure)

        projected_slice, _ = run_json([
            sys.executable, CLI, "--json", "slice", "--root", FIXTURE,
            "--slice", slice_path("es-py-package.json"), "--contract", contract("package-consumer.json"),
        ])
        Draft202012Validator(json.loads((ROOT / "schemas" / "bbk-python-execution-slice-projection-v1.schema.json").read_text(encoding="utf-8"))).validate(projected_slice)

        reviewed, _ = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURE,
            "--contract", contract("public-typed-package.json"),
            "--candidate", A4 / "candidates" / "conforming-candidate.json",
            "--actual-inventory", inventory("public-conforming.json"),
        ])
        comparison_schema = json.loads((ROOT / "schemas" / "bbk-python-planned-actual-structure-comparison-v1.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(comparison_schema).validate(reviewed["comparison"])
        review_schema = json.loads((ROOT / "schemas" / "bbk-python-structure-review-result-v1.schema.json").read_text(encoding="utf-8"))
        registry = Registry()
        for schema_path in sorted((ROOT / "schemas").glob("*.schema.json")):
            schema_value = json.loads(schema_path.read_text(encoding="utf-8"))
            if schema_value.get("$id"):
                registry = registry.with_resource(schema_value["$id"], Resource.from_contents(schema_value))
        Draft202012Validator(review_schema, registry=registry).validate(reviewed)

    def test_structure_projection_is_deterministic_and_preserves_generic_identity(self):
        command = [
            sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
            "--contract", contract("public-typed-package.json"), "--role", "architect",
            "--assurance-tier", "material",
        ]
        left, _ = run_json(command)
        right, _ = run_json(command)
        self.assertEqual(left, right)
        self.assertEqual(left["input"]["id"], "ISC-PY-PUBLIC")
        self.assertEqual(left["input"]["revision"], "1")
        self.assertEqual(left["applicability"]["disposition"], "PROJECTED")
        self.assertIn("python-implementation-structure-authoring", left["projection"]["selected_skills"])
        self.assertIn("python-public-shared-contract-drift", left["projection"]["planned_gates"])
        self.assertFalse(left["no_authority"]["may_declare_pass"])

    def test_routine_none_contract_does_not_select_structure_reviewer(self):
        projected, _ = run_json([
            sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
            "--contract", contract("routine-private-none.json"), "--role", "reviewer",
        ])
        self.assertEqual(projected["applicability"]["disposition"], "NOT_APPLICABLE")
        self.assertNotIn("python-implementation-structure-review", projected["projection"]["selected_skills"])
        resolved, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--assurance-tier", "routine",
            "--structure-contract", contract("routine-private-none.json"),
            "--path", "src/fixture_pkg/api.py",
        ])
        self.assertNotIn("python-implementation-structure-review", {item["id"] for item in resolved["selected_components"]})

    def test_material_public_contract_routes_focused_structure_review_and_lock_digests(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--assurance-tier", "material",
            "--structure-contract", contract("public-typed-package.json"),
            "--path", "src/fixture_pkg/__init__.py",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertIn("python-implementation-structure-review", selected)
        self.assertIn("python-api-package-boundary-review", selected)
        structure = value["implementation_structure"]
        self.assertEqual(structure["support_status"], "supported")
        self.assertRegex(structure["contract_digest"], r"^[0-9a-f]{64}$")
        self.assertRegex(structure["contract_projection_digest"], r"^[0-9a-f]{64}$")
        lock_record = value["lock"]["profiles"][0]["implementation_structure"]
        self.assertEqual(lock_record["contract_digest"], structure["contract_digest"])
        self.assertEqual(lock_record["contract_projection_digest"], structure["contract_projection_digest"])

    def test_projection_carries_effect_observability_migration_and_review_facets(self):
        migration, _ = run_json([
            sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
            "--contract", contract("migration.json"), "--role", "architect",
            "--assurance-tier", "consequential",
        ])
        migration_projection = migration["projection"]
        self.assertTrue(migration_projection["observability_points"])
        self.assertTrue(migration_projection["migration_touchpoints"])
        self.assertTrue(migration_projection["review_policy"]["acceptance_criteria"])
        self.assertIn("python-migration-rollback", migration_projection["planned_gates"])

        boundary, _ = run_json([
            sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
            "--contract", contract("external-json-validation.json"), "--role", "architect",
            "--assurance-tier", "consequential",
        ])
        boundary_projection = boundary["projection"]
        self.assertTrue(boundary_projection["effect_boundaries"])
        self.assertIn("python-security-boundary", boundary_projection["planned_gates"])

    def test_state_and_recovery_contract_routes_ownership_and_failure_review(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "validator", "--assurance-tier", "consequential",
            "--structure-contract", contract("async-cancellation.json"),
            "--path", "src/fixture_pkg/async_service.py",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertIn("python-implementation-structure-review", selected)
        self.assertIn("python-runtime-correctness-review", selected)
        gates = {item["id"] for item in value["gate_plan"]["selected"]}
        self.assertIn("python-state-ownership-drift", gates)
        self.assertIn("python-async-cancellation", gates)

    def test_execution_slice_projection_is_integrated_and_foundation_exception_is_explicit(self):
        package, _ = run_json([
            sys.executable, CLI, "--json", "slice", "--root", FIXTURE,
            "--slice", slice_path("es-py-package.json"), "--contract", contract("package-consumer.json"),
        ])
        self.assertEqual(package["projection"]["touchpoint"]["python_kind"], "wheel-consumer")
        self.assertTrue(package["projection"]["objective"])
        self.assertTrue(package["projection"]["flow"]["steps"])
        self.assertTrue(package["projection"]["atomicity"]["containedOrReversible"])
        self.assertTrue(package["projection"]["integration_owner"])
        self.assertTrue(package["projection"]["assertions"])
        self.assertEqual(package["projection"]["horizontal_sequence_assessment"]["status"], "INTEGRATED")
        self.assertIn("python-installed-wheel-tests", package["projection"]["planned_gates"])

        foundation, _ = run_json([
            sys.executable, CLI, "--json", "slice", "--root", FIXTURE,
            "--slice", slice_path("es-py-foundation.json"), "--contract", contract("package-consumer.json"),
        ])
        self.assertEqual(foundation["projection"]["horizontal_sequence_assessment"]["status"], "FOUNDATION_EXCEPTION")
        self.assertTrue(foundation["projection"]["horizontal_sequence_assessment"]["next_slice_required"])

    def test_unsupported_subject_returns_bounded_result(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
            "--contract", contract("unsupported-procedure.json"),
        ])
        self.assertEqual(value["applicability"]["disposition"], "UNSUPPORTED")
        self.assertTrue(value["unsupported_or_uncertain"])
        self.assertEqual(value["projection"]["selected_skills"], ["bbk-python"])

    def test_static_inventory_does_not_false_conform_when_fixed_evidence_is_missing(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURE,
            "--contract", contract("public-typed-package.json"),
            "--candidate", A4 / "candidates" / "conforming-candidate.json",
        ])
        self.assertEqual(value["disposition"], "BLOCKED")
        self.assertTrue(value["comparison"]["blocking_unknowns"])
        self.assertTrue(any(item["class"] == "blocker" for item in value["findings"]))

    def test_structure_review_conforms_for_matching_public_shape(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURE,
            "--contract", contract("public-typed-package.json"),
            "--candidate", A4 / "candidates" / "conforming-candidate.json",
            "--actual-inventory", inventory("public-conforming.json"),
        ])
        self.assertEqual(value["disposition"], "CONFORMS")
        self.assertEqual(value["comparison"]["material_difference_count"], 0)
        self.assertFalse(value["no_authority"]["may_declare_pass"])

    def test_harmless_private_divergence_is_not_material(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURE,
            "--contract", contract("public-typed-package.json"),
            "--candidate", A4 / "candidates" / "conforming-candidate.json",
            "--actual-inventory", inventory("private-harmless-divergence.json"),
        ])
        self.assertEqual(value["disposition"], "ADVISORY_DIVERGENCE")
        self.assertEqual(value["comparison"]["material_difference_count"], 0)
        self.assertGreater(value["comparison"]["advisory_difference_count"], 0)

    def test_public_import_fixed_decision_divergence_is_material(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURE,
            "--contract", contract("public-typed-package.json"),
            "--candidate", A4 / "candidates" / "conforming-candidate.json",
            "--actual-inventory", inventory("public-import-drift.json"),
        ])
        self.assertEqual(value["disposition"], "MATERIAL_DIVERGENCE")
        self.assertTrue(any(item["planned_ref"] == "FD-PUBLIC-IMPORT" for item in value["findings"]))

    def test_async_owner_fixed_decision_divergence_is_material(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURE,
            "--contract", contract("async-cancellation.json"),
            "--candidate", A4 / "candidates" / "conforming-candidate.json",
            "--actual-inventory", inventory("async-ownership-drift.json"),
        ])
        self.assertEqual(value["disposition"], "MATERIAL_DIVERGENCE")
        refs = {item["planned_ref"] for item in value["findings"]}
        self.assertIn("FD-ASYNC-OWNER", refs)
        self.assertIn("child tasks and async resources", refs)

    def test_broad_survey_does_not_fan_out_structure_specialists(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--assurance-tier", "material",
            "--hint", "broad-analysis", "--structure-contract", contract("public-typed-package.json"),
        ])
        self.assertEqual({item["id"] for item in value["selected_components"]}, {"bbk-python", "comprehensive-analysis-python"})
        self.assertIsNotNone(value["implementation_structure"]["contract_projection"])

    def test_structure_contract_validator_defaults_to_declared_profile_minimum(self):
        command = [
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "architect", "--assurance-tier", "material",
            "--structure-contract", contract("public-typed-package.json"),
        ]
        env = os.environ.copy()
        for name in ("BBK_CORE_VERSION", "BBK_CORE_ROOT", "BBK_CORE_CLI"):
            env.pop(name, None)
        value, _ = run_json(command, env=env)
        gate = next(item for item in value["gate_plan"]["selected"] if item["id"] == "python-generic-structure-contract-validate")
        availability = next(item for item in gate["availability"] if item["requirement"] == "bbk-structure-contract-validator")
        self.assertEqual(availability["status"], "AVAILABLE")
        self.assertIn("0.1.0-alpha.8", availability["detail"])

    def test_structure_contract_validator_compatibility_is_capability_aware(self):
        command = [
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "architect", "--assurance-tier", "material",
            "--structure-contract", contract("public-typed-package.json"),
        ]
        cases = {
            "0.1.0-alpha.3": "MISSING",
            "0.1.0-alpha.4": "AVAILABLE",
            "0.1.0-alpha.8": "AVAILABLE",
            "0.1.0-alpha.11.8": "AVAILABLE",
            "0.1.0": "AVAILABLE",
            "0.2.0-alpha.1": "AVAILABLE",
        }
        for version, expected in cases.items():
            with self.subTest(version=version):
                env = os.environ.copy()
                env.pop("BBK_CORE_ROOT", None)
                env.pop("BBK_CORE_CLI", None)
                env["BBK_CORE_VERSION"] = version
                value, _ = run_json(command, env=env)
                gate = next(item for item in value["gate_plan"]["selected"] if item["id"] == "python-generic-structure-contract-validate")
                availability = next(item for item in gate["availability"] if item["requirement"] == "bbk-structure-contract-validator")
                self.assertEqual(availability["status"], expected)
                self.assertEqual(gate["planning_status"], "BLOCKED_INPUT" if expected == "MISSING" else "PLANNED")

        with tempfile.TemporaryDirectory() as temp:
            core = Path(temp)
            (core / "schemas").mkdir()
            (core / "tools").mkdir()
            (core / "schemas" / "bbk-implementation-structure-contract-v1.schema.json").write_text("{}\n", encoding="utf-8")
            (core / "tools" / "bbk.py").write_text("# capability fixture\n", encoding="utf-8")
            env = os.environ.copy()
            env["BBK_CORE_VERSION"] = "0.1.0-alpha.3"
            env["BBK_CORE_ROOT"] = str(core)
            value, _ = run_json(command, env=env)
            gate = next(item for item in value["gate_plan"]["selected"] if item["id"] == "python-generic-structure-contract-validate")
            availability = next(item for item in gate["availability"] if item["requirement"] == "bbk-structure-contract-validator")
            self.assertEqual(availability["status"], "AVAILABLE")
            self.assertIn("capability detected", availability["detail"])

    def test_resolution_with_contract_and_slice_is_deterministic_and_locks_both_digests(self):
        command = [
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "worker-designer", "--assurance-tier", "material",
            "--structure-contract", contract("package-consumer.json"),
            "--execution-slice", slice_path("es-py-package.json"),
        ]
        left, _ = run_json(command)
        right, _ = run_json(command)
        self.assertEqual(left["effective_sha256"], right["effective_sha256"])
        values = left["implementation_structure"]
        self.assertRegex(values["contract_digest"], r"^[0-9a-f]{64}$")
        self.assertRegex(values["slice_digest"], r"^[0-9a-f]{64}$")
        self.assertRegex(values["contract_projection_digest"], r"^[0-9a-f]{64}$")
        self.assertRegex(values["slice_projection_digest"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
