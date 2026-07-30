from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tools" / "bbk_rust.py"
INSTALL = ROOT / "tools" / "install.py"
INDEX = ROOT / "tools" / "build_rules_index.py"
FIXTURE = ROOT / "fixtures" / "rust-workspace"
ALPHA4 = ROOT / "fixtures" / "alpha4"
sys.path.insert(0, str(ROOT / "tools"))
import rust_structure


def run(command, *, cwd=None, env=None, check=True):
    return subprocess.run(
        [str(item) for item in command], cwd=str(cwd or ROOT), env=env,
        check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
    )


def run_json(command, *, cwd=None, env=None, check=True):
    result = run(command, cwd=cwd, env=env, check=check)
    return json.loads(result.stdout), result


class RustProfileTests(unittest.TestCase):
    def test_profile_manifest_and_internal_references(self):
        profile = json.loads((ROOT / "PROFILE.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["schema"], "bbk.language-profile.v1")
        self.assertEqual(profile["id"], "rust")
        self.assertEqual(profile["maturity"], "comprehensive-alpha")
        self.assertEqual(profile["version"], "0.1.0-alpha.3")
        self.assertEqual(profile["requires"]["bbk_minimum"], "0.1.0-alpha.8")
        self.assertEqual(profile["capabilities"]["implementation_structure"]["status"], "supported")
        self.assertTrue({"structure", "slice", "structure_review"}.issubset(profile["entrypoints"]))
        self.assertFalse(profile["authority"]["may_declare_pass"])
        self.assertFalse(profile["authority"]["may_expand_work_scope"])
        self.assertFalse(profile["authority"]["may_grant_tools_or_effects"])
        self.assertFalse(profile["authority"]["may_reduce_assurance"])
        self.assertEqual(profile["mutation_testing"]["selected_tool"], "mutest-rs")
        self.assertEqual(profile["mutation_testing"]["cargo_subcommand"], ["cargo", "mutest", "run"])
        for item in profile["skills"]:
            self.assertTrue((ROOT / item["path"]).is_file(), item)
        for path in profile["references"]:
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertTrue((ROOT / profile["gates"]).is_file())
        for path in profile["selection"].values():
            self.assertTrue((ROOT / path).is_file(), path)
        for path in (ROOT / "schemas").glob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))

    def test_rule_index_is_current_and_complete(self):
        run([sys.executable, INDEX, "--check"])
        index = json.loads((ROOT / "skills" / "rust-skills" / "rules-index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["rule_count"], 265)
        self.assertEqual(len(index["rules"]), 265)
        self.assertEqual(len({item["id"] for item in index["rules"]}), 265)
        for item in index["rules"]:
            self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(item["default_applicability"])

    def test_mutest_rs_is_the_only_operational_mutation_recipe(self):
        operative = []
        for root in [ROOT / "PROFILE.json", ROOT / "gates", ROOT / "skills", ROOT / "references", ROOT / "docs"]:
            paths = [root] if root.is_file() else list(root.rglob("*"))
            for path in paths:
                if path.is_file() and path.suffix in {".md", ".json"}:
                    operative.append(path.read_text(encoding="utf-8", errors="replace"))
        text = "\n".join(operative).lower()
        self.assertIn("cargo mutest run", text)
        self.assertIn("mutest-rs", text)
        self.assertNotIn("cargo-mutants", text)
        self.assertNotIn("cargo mutants", text)

    def test_static_preflight_detects_workspace_and_toolchain(self):
        value, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", FIXTURE])
        self.assertEqual(value["schema"], "bbk.rust-preflight.v1")
        self.assertEqual(value["workspace"]["members"], ["fixture-core", "fixture-native"])
        self.assertEqual(value["workspace"]["default_members"], ["crates/core"])
        self.assertEqual(value["toolchain"]["channel"], "stable")
        native = next(item for item in value["workspace"]["packages"] if item["name"] == "fixture-native")
        self.assertIn("cdylib", native["crate_types"])
        self.assertTrue(native["build_script"])
        self.assertRegex(value["digest"], r"^[0-9a-f]{64}$")

    def test_routine_worker_is_minimal_and_does_not_execute_cargo(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "cargo-executed"
            fakebin = Path(temp) / "bin"; fakebin.mkdir()
            fake = fakebin / ("cargo.cmd" if os.name == "nt" else "cargo")
            if os.name == "nt":
                fake.write_text(f"@echo touched>{marker}\r\n", encoding="utf-8")
            else:
                fake.write_text(f"#!/bin/sh\ntouch {marker!s}\nexit 91\n", encoding="utf-8")
                fake.chmod(0o755)
            env = os.environ.copy(); env["PATH"] = str(fakebin) + os.pathsep + env.get("PATH", "")
            value, _ = run_json([
                sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
                "--role", "worker", "--task-profile", "implementation",
                "--assurance-tier", "routine", "--path", "crates/core/src/lib.rs",
            ], env=env)
            self.assertFalse(marker.exists())
            self.assertEqual([item["id"] for item in value["selected_components"]], ["bbk-rust", "rust-skills"])
            self.assertEqual(
                [item["id"] for item in value["gate_plan"]["selected"]],
                ["rustfmt-check", "rust-focused-tests", "rust-check-affected", "rust-clippy-affected"],
            )
            self.assertTrue(value["recommended_validator_packs"])

    def test_public_wire_validator_selects_api_and_correctness(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "validator", "--task-profile", "interface-schema-migration",
            "--assurance-tier", "consequential", "--change-class", "interface",
            "--change-class", "schema", "--hint", "serde-wire-format",
            "--path", "crates/core/src/lib.rs",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertIn("rust-api-crate-boundary-review", selected)
        self.assertIn("rust-correctness-failure-review", selected)
        self.assertNotIn("comprehensive-analysis-rust", selected)

    def test_unsafe_ffi_selects_focused_assurance(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "validator", "--task-profile", "interface-schema-migration",
            "--assurance-tier", "consequential", "--hint", "ffi",
            "--path", "crates/native/src/lib.rs",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertTrue({"rust-unsafe-ffi-assurance", "rust-correctness-failure-review", "rust-security-supply-chain-review"}.issubset(selected))
        gates = {item["id"] for item in value["gate_plan"]["selected"]}
        self.assertIn("rust-miri", gates)
        self.assertNotIn("rust-mutest-rs", gates)

    def test_broad_survey_does_not_fan_out_all_reviewers(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--task-profile", "investigation-prototype",
            "--assurance-tier", "material", "--hint", "broad-analysis",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertEqual(selected, {"bbk-rust", "comprehensive-analysis-rust"})

    def test_mutation_hint_selects_mutest_gate_and_evidence(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "verification-designer", "--task-profile", "test-fixture",
            "--assurance-tier", "consequential", "--hint", "mutest-rs",
            "--path", "crates/core/src/lib.rs",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertIn("rust-test-strategy-review", selected)
        self.assertIn("rust-evidence-reproducer", selected)
        gates = {item["id"] for item in value["gate_plan"]["selected"]}
        self.assertIn("rust-mutest-rs", gates)
        gate = next(item for item in value["gate_plan"]["selected"] if item["id"] == "rust-mutest-rs")
        self.assertEqual(gate["preferred_command"], ["just", "mutest"])

    def test_effective_digest_is_deterministic(self):
        command = [
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "worker", "--task-profile", "implementation",
            "--assurance-tier", "routine", "--path", "crates/core/src/lib.rs",
        ]
        left, _ = run_json(command)
        right, _ = run_json(command)
        self.assertEqual(left["effective_sha256"], right["effective_sha256"])
        self.assertNotEqual(left["lock"]["generated_at"], "")

    @unittest.skipUnless(shutil.which("node"), "node is required for OMP extension qualification")
    def test_omp_extension_parses_and_registers(self):
        extension = ROOT / "omp" / "extension" / "index.js"
        run(["node", "--check", extension])
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "mock.mjs"
            script.write_text(textwrap.dedent(f"""
                const chain = () => ({{ optional() {{ return this; }} }});
                const z = {{ object: value => value, string: chain, boolean: chain,
                  enum: values => chain(), array: value => chain() }};
                const tools = [], commands = [], handlers = [];
                const pi = {{ zod: {{ z }}, setLabel() {{}},
                  registerTool(value) {{ tools.push(value); }},
                  registerCommand(name, value) {{ commands.push([name, value]); }},
                  on(name, value) {{ handlers.push([name, value]); }}, sendMessage() {{}} }};
                const mod = await import({json.dumps(extension.as_uri())});
                mod.default(pi);
                if (tools.length !== 12) throw new Error(`tools=${{tools.length}}`);
                if (commands.length !== 12) throw new Error(`commands=${{commands.length}}`);
                if (!handlers.some(([name]) => name === 'session_start')) throw new Error('missing session_start');
                console.log(JSON.stringify({{tools: tools.map(x => x.name), commands: commands.map(x => x[0])}}));
            """), encoding="utf-8")
            value = json.loads(run(["node", script]).stdout)
            self.assertIn("bbk_rust_resolve", value["tools"])
            self.assertIn("bbk:rust:gates", value["commands"])

    @unittest.skipUnless(shutil.which("node"), "node is required for installed OMP extension qualification")
    def test_installed_omp_extension_executes_profile_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            home = base / "home"; home.mkdir()
            env = os.environ.copy(); env.update({
                "HOME": str(home),
                "BBK_INSTALL_ROOT": str(base / "data"),
                "BBK_BIN_DIR": str(base / "bin"),
            })
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "user", "--omp"], env=env)
            self.assertTrue(installed["omp"])
            extension = home / ".omp" / "agent" / "extensions" / "bbk-profile-rust" / "index.js"
            script = base / "installed-rust-omp-mock.mjs"
            script.write_text(textwrap.dedent(f"""
                const chain = () => ({{ optional() {{ return this; }} }});
                const z = {{ object: value => value, string: chain, boolean: chain,
                  enum: values => chain(), array: value => chain() }};
                const tools = [], commands = [], handlers = [];
                const pi = {{ zod: {{ z }}, setLabel() {{}},
                  registerTool(value) {{ tools.push(value); }},
                  registerCommand(name, value) {{ commands.push([name, value]); }},
                  on(name, value) {{ handlers.push([name, value]); }}, sendMessage() {{}} }};
                const mod = await import({json.dumps(extension.as_uri())});
                mod.default(pi);
                const tool = tools.find(value => value.name === 'bbk_rust_preflight');
                if (!tool) throw new Error('missing bbk_rust_preflight');
                const result = await tool.execute('call-1', {{root: {json.dumps(str(FIXTURE))}, runTools: false}}, undefined, undefined, {{cwd: {json.dumps(str(FIXTURE))}}});
                if (result.isError || result.details?.schema !== 'bbk.rust-preflight.v1')
                  throw new Error(JSON.stringify(result.details));
                console.log(JSON.stringify({{schema: result.details.schema, tools: tools.length}}));
            """), encoding="utf-8")
            value = json.loads(run(["node", script], env=env).stdout)
            self.assertEqual(value["schema"], "bbk.rust-preflight.v1")
            self.assertEqual(value["tools"], 12)
            run([sys.executable, INSTALL, "uninstall", "--scope", "user"], env=env)
            self.assertTrue(home.exists())

    def test_user_install_and_uninstall_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"; home.mkdir()
            env = os.environ.copy(); env.update({"HOME": str(home), "BBK_INSTALL_ROOT": str(home / "data"), "BBK_BIN_DIR": str(home / "bin")})
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "user"], env=env)
            self.assertTrue(installed["codex"] and installed["omp"] and installed["claude"])
            self.assertEqual(len(list((home / ".agents" / "skills").glob("*/SKILL.md"))), 14)
            self.assertEqual(len(list((home / ".claude" / "skills").glob("*/SKILL.md"))), 14)
            self.assertTrue((home / ".omp" / "agent" / "extensions" / "bbk-profile-rust" / "index.js").is_file())
            self.assertTrue((home / "bin" / ("bbk-rust.cmd" if os.name == "nt" else "bbk-rust")).is_file())
            current = json.loads((home / "data" / "profiles" / "rust" / "current.json").read_text(encoding="utf-8"))
            self.assertEqual(current["version"], "0.1.0-alpha.3")
            status, _ = run_json([sys.executable, INSTALL, "--json", "status", "--scope", "user"], env=env)
            self.assertEqual(status["summary"].get("current"), len(status["files"]))
            run([sys.executable, INSTALL, "uninstall", "--scope", "user"], env=env)
            self.assertTrue(home.exists())
            self.assertFalse((home / "data" / "profile-install-manifests" / "rust.json").exists())

    def test_project_install_roundtrip_preserves_project_root(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"; project.mkdir()
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "project", "--root", project, "--omp"])
            self.assertFalse(installed["codex"]); self.assertTrue(installed["omp"]); self.assertFalse(installed["claude"])
            self.assertTrue((project / ".bbk-kit" / "profiles" / "rust" / "0.1.0-alpha.3" / "PROFILE.json").is_file())
            self.assertTrue((project / ".omp" / "extensions" / "bbk-profile-rust" / "index.js").is_file())
            run([sys.executable, INSTALL, "uninstall", "--scope", "project", "--root", project])
            self.assertTrue(project.exists())
            self.assertFalse((project / ".bbk-profile-rust-install.json").exists())


    def test_alpha4_generic_and_profile_schemas_accept_positive_fixtures(self):
        contract_schema = json.loads((ROOT / "schemas" / "bbk-implementation-structure-contract-v1.schema.json").read_text(encoding="utf-8"))
        slice_schema = json.loads((ROOT / "schemas" / "bbk-execution-slice-v1.schema.json").read_text(encoding="utf-8"))
        for path in sorted((ALPHA4 / "contracts").glob("*.json")):
            Draft202012Validator(contract_schema).validate(json.loads(path.read_text(encoding="utf-8")))
        for path in sorted((ALPHA4 / "slices").glob("*.json")):
            Draft202012Validator(slice_schema).validate(json.loads(path.read_text(encoding="utf-8")))
        invalid = json.loads((ALPHA4 / "invalid-contract.json").read_text(encoding="utf-8"))
        self.assertTrue(list(Draft202012Validator(contract_schema).iter_errors(invalid)))

    def test_alpha4_structure_projection_is_deterministic_and_schema_valid(self):
        command = [sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
                   "--contract", ALPHA4 / "contracts" / "public-crate-api.json"]
        left, _ = run_json(command); right, _ = run_json(command)
        self.assertEqual(left, right)
        self.assertEqual(left["applicability"]["disposition"], "SUPPORTED")
        schema = json.loads((ROOT / "schemas" / "bbk-rust-implementation-structure-projection-v1.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(left)
        self.assertFalse(left["authority"]["projection_is_authoritative_state"])

    def test_alpha4_execution_slice_projection_and_lock_carry_exact_digests(self):
        contract = ALPHA4 / "contracts" / "public-crate-api.json"
        slice_path = ALPHA4 / "slices" / "public-consumer.json"
        value, _ = run_json([sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "worker-designer", "--task-profile", "execution-slicing",
            "--assurance-tier", "material", "--structure-contract", contract,
            "--execution-slice", slice_path])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertIn("rust-execution-slicing", selected)
        self.assertEqual(len(value["inputs"]["implementation_structure_contracts"]), 1)
        self.assertEqual(len(value["inputs"]["execution_slices"]), 1)
        self.assertRegex(value["inputs"]["implementation_structure_contracts"][0]["projection_digest"], r"^[0-9a-f]{64}$")
        self.assertRegex(value["inputs"]["execution_slices"][0]["projection_digest"], r"^[0-9a-f]{64}$")
        self.assertEqual(value["structure_support"], "supported")
        schema = json.loads((ROOT / "schemas" / "bbk-rust-execution-slice-projection-v1.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(value["slice_projections"][0])

    def test_alpha4_routine_change_does_not_fan_out_structure_review(self):
        value, _ = run_json([sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "worker", "--task-profile", "implementation", "--assurance-tier", "routine",
            "--path", "crates/core/src/lib.rs"])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertNotIn("rust-implementation-structure", selected)
        self.assertNotIn("rust-implementation-structure-review", selected)
        self.assertEqual(value["structure_projections"], [])

    def test_alpha4_material_contract_selects_only_focused_structure_review(self):
        value, _ = run_json([sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--task-profile", "implementation-structure",
            "--assurance-tier", "material", "--structure-contract", ALPHA4 / "contracts" / "public-crate-api.json"])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertIn("rust-implementation-structure-review", selected)
        self.assertNotIn("comprehensive-analysis-rust", selected)
        self.assertNotIn("rust-security-supply-chain-review", selected)

    def test_alpha4_planned_actual_comparison_preserves_delegated_freedom(self):
        common = [sys.executable, CLI, "--json", "structure-review", "--root", FIXTURE,
                  "--contract", ALPHA4 / "contracts" / "public-crate-api.json",
                  "--candidate", ALPHA4 / "candidate-manifest.json"]
        harmless, _ = run_json(common + ["--actual-inventory", ALPHA4 / "inventories" / "harmless-private-divergence.json"])
        material, _ = run_json(common + ["--actual-inventory", ALPHA4 / "inventories" / "material-public-divergence.json"])
        self.assertEqual(harmless["disposition"], "CONFORMS")
        self.assertTrue(harmless["comparison"]["within_delegated_freedom"])
        self.assertEqual(material["disposition"], "MATERIAL_DIVERGENCE")
        self.assertTrue(any(item.get("fixed_decision_ref") == "FD-RUST-PUBLIC" for item in material["findings"]))
        schema = json.loads((ROOT / "schemas" / "bbk-rust-structure-review-result-v1.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(harmless); Draft202012Validator(schema).validate(material)

    def test_alpha4_legacy_profile_is_reported_unprojected(self):
        profile = json.loads((ROOT / "PROFILE.json").read_text(encoding="utf-8"))
        profile.pop("capabilities", None)
        self.assertEqual(rust_structure.structure_support_status(profile), "legacy-unprojected")

    def test_alpha4_invalid_contract_blocks_instead_of_inventing_projection(self):
        value, result = run_json([sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
            "--contract", ALPHA4 / "invalid-contract.json"], check=False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(value["applicability"]["disposition"], "BLOCKED")
        self.assertTrue(value["blockers"])

class CurrentMetadataContractTests(unittest.TestCase):
    def test_current_release_metadata_is_consistent(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        profile = json.loads((ROOT / "PROFILE.json").read_text(encoding="utf-8"))
        self.assertEqual(version, '0.1.0-alpha.3')
        self.assertEqual(profile["version"], version)
        self.assertEqual(profile["requires"]["bbk_minimum"], '0.1.0-alpha.8')
        self.assertEqual(profile["contract_dialects"]["implementation_structure"]["legacy_output_value"], '0.1.0-alpha.4')
        self.assertEqual(profile["contract_dialects"]["execution_slice"]["legacy_output_value"], '0.1.0-alpha.4')
        self.assertEqual(profile["contract_dialects"]["typed_profile_dispatch"]["id"], "bbk.profile-capability.v1")

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        install = (ROOT / "docs" / "INSTALL.md").read_text(encoding="utf-8")
        metadata = (ROOT / "docs" / "METADATA-CONTRACT.md").read_text(encoding="utf-8")
        omp_readme = (ROOT / "omp" / "extension" / "README.md").read_text(encoding="utf-8")
        omp_package = json.loads((ROOT / "omp" / "extension" / "package.json").read_text(encoding="utf-8"))
        for current in (readme, install, metadata, omp_readme):
            self.assertIn(version, current)
        for current in (readme, install, metadata):
            self.assertIn('0.1.0-alpha.8', current)
        self.assertEqual(omp_package["version"], version)
        self.assertNotIn("for BBK alpha.4 across", profile.get("description", ""))

        current_guidance = "\n".join((readme, install, omp_readme)).lower().replace("`", "")
        for stale_claim in (
            "install bbk core alpha.4",
            "install bbk core 0.1.0-alpha.4",
            "requires bbk 0.1.0-alpha.4",
            "requires bbk core 0.1.0-alpha.4",
            "minimum compatible bbk core is 0.1.0-alpha.4",
        ):
            self.assertNotIn(stale_claim, current_guidance)

    def test_python_tools_and_tests_use_explicit_text_encoding(self):
        violations = []
        for source in [*sorted((ROOT / "tools").glob("*.py")), *sorted((ROOT / "tests").glob("*.py"))]:
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if node.func.attr not in {"read_text", "write_text"}:
                    continue
                if any(keyword.arg == "encoding" for keyword in node.keywords):
                    continue
                violations.append(f"{source.relative_to(ROOT).as_posix()}:{node.lineno} {node.func.attr}")
        self.assertEqual(violations, [])



if __name__ == "__main__":
    unittest.main()
