#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tools" / "profile.py"
PROFILE = json.loads((ROOT / "PROFILE.json").read_text(encoding="utf-8"))
PREFIX = {"typescript-javascript": "tsjs"}.get(PROFILE["id"], PROFILE["id"].replace("-", "_"))
ENV_TOKEN = {"typescript-javascript": "TSJS"}.get(PROFILE["id"], PROFILE["id"].upper().replace("-", "_"))

spec = importlib.util.spec_from_file_location("profile_dispatch_under_test", CLI)
assert spec and spec.loader
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Alpha8ProfileDispatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.request_dir = self.work / "request"
        self.request_dir.mkdir()
        self.source = self.work / "subject-source"
        (self.source / "src").mkdir(parents=True)
        (self.source / "README.md").write_text("fixture subject\n", encoding="utf-8")
        suffix = {"rust": ".rs", "go": ".go", "python": ".py", "typescript-javascript": ".ts", "codesys": ".st"}[PROFILE["id"]]
        (self.source / "src" / ("sample" + suffix)).write_text(
            "enum State { Ready, Running }\ncanonical owner transition decide apply effect adapter write publish retry cancellation duplicate timeout acknowledgement recovery shadow ambient global test trace\n",
            encoding="utf-8",
        )
        self.fixtures = ROOT / "fixtures" / "profile-dispatch"
        self.identity = controller.package_identity()

    def copy_input(self, name, kind, *, target=None):
        source = self.fixtures / name
        destination = self.request_dir / (target or name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        value = json.loads(destination.read_text(encoding="utf-8"))
        return {
            "kind": kind,
            "path": destination.relative_to(self.request_dir).as_posix(),
            "sha256": file_digest(destination),
            "canonicalSha256": canonical_digest(value),
            "schema": value.get("schema"),
            "ref": value.get("designId") or value.get("assuranceContractId") or value.get("manifestId") or value.get("receiptId") or destination.name,
        }, value

    def write_input(self, value, kind, name):
        path = self.request_dir / name
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {
            "kind": kind, "path": path.relative_to(self.request_dir).as_posix(), "sha256": file_digest(path),
            "canonicalSha256": canonical_digest(value), "schema": value.get("schema"), "ref": value.get("inventoryId") or value.get("contextManifestId") or name,
        }

    def subject_for(self, operation, values):
        if operation.startswith("state-effect"):
            design = values["state-decision-effect"]
            return {"ref": design["designId"], "kind": "state-decision-effect-design", "revision": str(design["revision"]), "digest": canonical_digest(design)}
        if operation in {"review-context", "review-lens"}:
            return dict(values["review-manifest"]["subject"])
        evidence = values["evidence-input"]
        subject = evidence.get("subject") or {}
        return {"ref": subject.get("ref") or subject.get("id"), "kind": "evidence-subject", "revision": str(subject.get("revision") or "unknown"), "digest": subject["digest"]}

    def make_request(self, operation, bindings, values, *, context=None, subject=None, mutate=None):
        request = {
            "schema": "bbk.profile-capability-request.v1",
            "requestId": "PDR-TEST-" + operation.upper().replace("-", "_"),
            "operation": operation,
            "profile": dict(self.identity),
            "source": {"root": ".", "contentSha256": controller.source_content_digest(self.source)},
            "subject": subject or self.subject_for(operation, values),
            "inputs": bindings,
            "context": {
                "role": "profile-qualification", "taskProfile": "material", "assuranceTier": "material", "runTools": False,
                "paths": [], "hints": [], "changeClasses": [], "lensIds": [], "assignmentIds": [],
                **(context or {}),
            },
            "authority": {"readOnly": True, "mayMutateSubject": False, "mayGrantEffects": False, "runQualifiedReadOnlyTools": False},
        }
        if mutate:
            mutate(request)
        request["requestDigest"] = canonical_digest(request)
        path = self.request_dir / (operation + "-request.json")
        path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path, request

    def dispatch(self, operation, request_path, *, cwd=None, source=True):
        env = os.environ.copy()
        if source:
            env["BBK_PROFILE_SOURCE_ROOT"] = str(self.source)
        proc = subprocess.run([sys.executable, "-B", str(CLI), "--json", operation, "--request", str(request_path)], cwd=cwd or ROOT, env=env, text=True, capture_output=True, check=True, timeout=45)
        self.assertFalse(proc.stderr, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(set(result), {"schema", "profileId", "profileVersion", "capability", "operation", "status", "requestDigest", "payload", "warnings", "errors", "limitations"})
        self.assertEqual(result["schema"], "bbk.profile-capability-result.v1")
        self.assertEqual(result["profileId"], PROFILE["id"])
        self.assertEqual(result["profileVersion"], PROFILE["version"])
        self.assertEqual(result["operation"], operation)
        return result

    def state_inputs(self, fixture="design-contract.json"):
        binding, value = self.copy_input(fixture, "state-decision-effect")
        return [binding], {"state-decision-effect": value}

    def review_inputs(self, include_context=False):
        a_binding, assurance = self.copy_input("assurance-contract.json", "assurance-contract")
        m_binding, manifest = self.copy_input("review-manifest.json", "review-manifest")
        bindings = [a_binding, m_binding]
        values = {"assurance-contract": assurance, "review-manifest": manifest}
        if include_context:
            context_result = self.run_context()
            c_binding = self.write_input(context_result["payload"], "review-context", "review-context-generated.json")
            bindings.append(c_binding); values["review-context"] = context_result["payload"]
        return bindings, values

    def run_context(self, *, hints=None):
        bindings, values = self.review_inputs(False)
        path, _ = self.make_request("review-context", bindings, values, context={"hints": hints or []})
        return self.dispatch("review-context", path)

    def test_exact_profile_and_schema_contract(self):
        self.assertEqual(PROFILE["requires"]["bbk_minimum"], "0.1.0-alpha.8")
        for operation, capability in controller.OPERATIONS.items():
            self.assertIn(operation.replace("-", "_") if False else operation, controller.OPERATIONS)
            self.assertEqual(PROFILE["capabilities"][capability]["dispatch_protocol"], "bbk.profile-capability.v1")
        exact = Path(os.environ.get("BBK_ALPHA8_SCHEMA_ROOT", ROOT / "schemas"))
        for name in ["bbk-language-profile-v1.schema.json", "bbk-profile-capability-request-v1.schema.json", "bbk-profile-capability-result-v1.schema.json", "bbk-profile-dispatch-v1.schema.json", "bbk-review-context-manifest-v1.schema.json", "bbk-evidence-receipt-v2.schema.json"]:
            self.assertTrue((ROOT / "schemas" / name).is_file())

    def test_none_inline_contract_routing_is_proportional(self):
        counts = []
        for fixture, expected in [("design-none.json", "NONE"), ("design-inline.json", "INLINE"), ("design-contract.json", "CONTRACT")]:
            bindings, values = self.state_inputs(fixture)
            path, request = self.make_request("state-effect", bindings, values)
            result = self.dispatch("state-effect", path)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["requestDigest"], request["requestDigest"])
            self.assertEqual(result["payload"]["applicability"], expected)
            counts.append(len(result["payload"]["selectedProcedures"]))
        self.assertLessEqual(counts[0], counts[1])
        self.assertLessEqual(counts[1], counts[2])

    def test_inventory_and_review_surface_state_effect_hazards(self):
        bindings, values = self.state_inputs()
        inv_path, _ = self.make_request("state-effect-inventory", bindings, values)
        inventory = self.dispatch("state-effect-inventory", inv_path)
        self.assertIn(inventory["status"], {"PASS", "PARTIAL"})
        self.assertTrue(inventory["payload"]["derivedOrShadowState"])
        i_binding = self.write_input(inventory["payload"], "state-effect-inventory", "inventory-generated.json")
        review_path, _ = self.make_request("state-effect-review", [bindings[0], i_binding], {**values, "state-effect-inventory": inventory["payload"]})
        review = self.dispatch("state-effect-review", review_path)
        self.assertIn(review["status"], {"PASS_ADVISORY", "PASS"})
        self.assertIn(review["payload"]["classification"], {"MATERIAL_DIVERGENCE", "PRIVATE_DIVERGENCE_ACCEPTED", "CONFORMANT"})
        self.assertTrue(any(item["code"] == "SHADOW_OR_AMBIENT_STATE" for item in review["payload"]["findings"]))

    def test_review_context_is_exact_bounded_and_path_stable(self):
        result = self.run_context(hints=["targeted-finding:F-001"])
        self.assertIn(result["status"], {"PASS", "PARTIAL"})
        payload = result["payload"]
        self.assertEqual(payload["schema"], "bbk.review-context-manifest.v1")
        self.assertEqual(payload["root"], ".")
        canonical = [{"path": item["path"], "sha256": item["sha256"], "bytes": item["bytes"], "sourceClass": item["sourceClass"], "redaction": item["redaction"]} for item in payload["includedItems"]]
        self.assertEqual(payload["contentRoot"], canonical_digest(canonical))
        self.assertEqual(payload["compiler"]["targetedFindingIds"], ["F-001"])
        encoded = json.dumps(payload, sort_keys=True)
        self.assertNotIn(str(self.work), encoded)
        self.assertNotIn(str(self.source), encoded)

    def test_review_lens_maps_only_supported_procedures_and_does_not_pass_assertions(self):
        bindings, values = self.review_inputs(True)
        lens = PROFILE["capabilities"]["review_assurance"]["lens_ids"][0]
        path, _ = self.make_request("review-lens", bindings, values, context={"lensIds": [lens], "assignmentIds": ["LA-A-STATE-ONE"]})
        result = self.dispatch("review-lens", path)
        self.assertIn(result["status"], {"PASS", "PARTIAL"})
        self.assertEqual(result["payload"]["handledLensIds"], [lens])
        self.assertTrue(result["payload"]["selectedProcedures"])
        self.assertTrue(all(item["status"] == "NOT_EVALUATED" for item in result["payload"]["assertionEvaluations"]))
        generic = "intent-outcome"
        path2, _ = self.make_request("review-lens", bindings, values, context={"lensIds": [generic], "assignmentIds": ["LA-A-INTENT"]})
        unsupported = self.dispatch("review-lens", path2)
        self.assertEqual(unsupported["status"], "UNSUPPORTED")

    def test_evidence_adapter_valid_stale_wrong_subject_and_redacted(self):
        binding, receipt = self.copy_input("native-evidence.json", "evidence-input")
        path, _ = self.make_request("evidence-adapter", [binding], {"evidence-input": receipt})
        result = self.dispatch("evidence-adapter", path)
        expected = "PARTIAL" if PROFILE["capabilities"]["review_assurance"]["status"] == "partial" else "PASS"
        self.assertEqual(result["status"], expected)
        self.assertEqual(result["payload"]["receipt"]["schema"], "bbk.evidence-receipt.v2")
        self.assertIn(result["payload"]["receipt"]["trustClass"], controller.TRUST_CLASSES)

        stale = json.loads(json.dumps(receipt)); stale["freshness"]["stale"] = True
        stale_binding = self.write_input(stale, "evidence-input", "stale-evidence.json")
        stale_path, _ = self.make_request("evidence-adapter", [stale_binding], {"evidence-input": stale})
        self.assertEqual(self.dispatch("evidence-adapter", stale_path)["status"], "PARTIAL")

        wrong_subject = dict(self.subject_for("evidence-adapter", {"evidence-input": receipt})); wrong_subject["digest"] = "1" * 64
        wrong_path, _ = self.make_request("evidence-adapter", [binding], {"evidence-input": receipt}, subject=wrong_subject)
        self.assertEqual(self.dispatch("evidence-adapter", wrong_path)["status"], "BLOCKED")

        redacted = json.loads(json.dumps(receipt)); redacted["redaction"] = {"classification": "field-redacted", "redactedFields": ["environment.host"]}
        red_binding = self.write_input(redacted, "evidence-input", "redacted-evidence.json")
        red_path, _ = self.make_request("evidence-adapter", [red_binding], {"evidence-input": redacted})
        self.assertEqual(self.dispatch("evidence-adapter", red_path)["status"], "PARTIAL")

    def test_incomplete_native_evidence_is_legacy_or_unstructured_without_invented_pass(self):
        raw = {"schema": "profile.native-evidence.v1", "rawText": "historical result without command or environment", "subject": {"ref": "CANDIDATE-ORDER-001", "digest": "c43b10defceb4401dc11e37366e491015afb76986a0e6fd76e5022f1683197e0"}}
        binding = self.write_input(raw, "evidence-input", "legacy-evidence.json")
        path, _ = self.make_request("evidence-adapter", [binding], {"evidence-input": raw})
        result = self.dispatch("evidence-adapter", path)
        self.assertEqual(result["status"], "PARTIAL")
        receipt = result["payload"]["receipt"]
        self.assertIn(receipt["trustClass"], {"LEGACY_IMPORTED", "UNSTRUCTURED_OBSERVATION"})
        self.assertTrue(receipt["coverage"]["missingFields"])
        self.assertFalse(receipt["coverage"]["adapterEstablishesGenericEligibility"])

    def test_request_digest_profile_source_authority_and_relative_path_rejections(self):
        bindings, values = self.state_inputs("design-inline.json")
        path, request = self.make_request("state-effect", bindings, values)
        other_cwd = self.work / "other"; other_cwd.mkdir()
        self.assertEqual(self.dispatch("state-effect", path, cwd=other_cwd)["status"], "PASS")

        def assert_error(mutator, label):
            candidate = json.loads(json.dumps(request)); mutator(candidate); candidate["requestDigest"] = canonical_digest({k:v for k,v in candidate.items() if k != "requestDigest"})
            candidate_path = self.request_dir / (label + ".json"); candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            self.assertEqual(self.dispatch("state-effect", candidate_path)["status"], "ERROR")
        assert_error(lambda value: value["profile"].__setitem__("id", "wrong-profile"), "wrong-profile")
        assert_error(lambda value: value["profile"].__setitem__("version", "0.0.0"), "wrong-version")
        assert_error(lambda value: value["profile"].__setitem__("rootSha256", "1" * 64), "wrong-root")
        assert_error(lambda value: value["profile"].__setitem__("manifestSha256", "2" * 64), "wrong-manifest")
        assert_error(lambda value: value["authority"].__setitem__("mayGrantEffects", True), "wrong-authority")
        assert_error(lambda value: value["source"].__setitem__("contentSha256", "3" * 64), "wrong-source")
        bad = json.loads(json.dumps(request)); bad["requestDigest"] = "4" * 64
        bad_path = self.request_dir / "bad-request-digest.json"; bad_path.write_text(json.dumps(bad), encoding="utf-8")
        self.assertEqual(self.dispatch("state-effect", bad_path)["status"], "ERROR")

    def test_missing_source_root_and_stable_repeated_result(self):
        bindings, values = self.state_inputs("design-none.json")
        path, _ = self.make_request("state-effect", bindings, values)
        first = self.dispatch("state-effect", path)
        second = self.dispatch("state-effect", path)
        self.assertEqual(first, second)
        self.assertEqual(self.dispatch("state-effect", path, source=False)["status"], "ERROR")

    @unittest.skipUnless(shutil.which("node"), "node is required for OMP mock qualification")
    def test_omp_extension_registers_and_invokes_typed_surface(self):
        bindings, values = self.state_inputs("design-inline.json")
        path, _ = self.make_request("state-effect", bindings, values)
        probe = self.work / "probe.mjs"
        extension = (ROOT / "omp" / "extension" / "index.js").as_uri()
        tool_name = f"bbk_{PREFIX}_state_effect"
        probe.write_text(f"""import extension from {json.dumps(extension)};\nconst schema = () => ({{ optional() {{ return this; }} }});\nconst z = {{ string: schema, boolean: schema, number: schema, enum: schema, array: schema, object: value => value }};\nconst tools = [], commands = [];\nconst pi = {{ zod: {{ z }}, setLabel() {{}}, registerTool(value) {{ tools.push(value); }}, registerCommand(name, value) {{ commands.push([name, value]); }}, on() {{}}, sendMessage() {{}} }};\nextension(pi);\nconst tool = tools.find(value => value.name === {json.dumps(tool_name)});\nif (!tool) throw new Error('missing typed dispatch tool');\nconst result = await tool.execute('id', {{ request: {json.dumps(str(path))} }}, undefined, undefined, {{ cwd: {json.dumps(str(self.work))} }});\nconsole.log(JSON.stringify({{ tools: tools.map(value => value.name), commands: commands.map(value => value[0]), result: result.details }}));\n""", encoding="utf-8")
        env = os.environ.copy(); env[f"BBK_{ENV_TOKEN}_PROFILE_DISPATCH_CLI"] = str(CLI); env["BBK_PROFILE_SOURCE_ROOT"] = str(self.source)
        proc = subprocess.run(["node", str(probe)], env=env, text=True, capture_output=True, check=True, timeout=30)
        value = json.loads(proc.stdout)
        self.assertIn(tool_name, value["tools"])
        self.assertEqual(value["result"]["schema"], "bbk.profile-capability-result.v1")
        self.assertEqual(value["result"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
