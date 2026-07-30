from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tools" / "bbk_python.py"
INSTALL = ROOT / "tools" / "install.py"
FIXTURE = ROOT / "fixtures" / "python-project"
A4 = ROOT / "fixtures" / "alpha4"
CORE_CLI_RAW = os.environ.get("BBK_CORE_CLI")
CORE_CLI = Path(CORE_CLI_RAW).expanduser().resolve() if CORE_CLI_RAW else None


def run(command, *, cwd=None, env=None, check=True):
    return subprocess.run(
        [str(item) for item in command], cwd=str(cwd or ROOT), env=env,
        check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
    )


def run_json(command, *, cwd=None, env=None, check=True):
    result = run(command, cwd=cwd, env=env, check=check)
    return json.loads(result.stdout), result


class PythonProfileTests(unittest.TestCase):
    def test_profile_manifest_and_internal_references(self):
        profile = json.loads((ROOT / "PROFILE.json").read_text())
        self.assertEqual(profile["schema"], "bbk.language-profile.v1")
        self.assertEqual(profile["id"], "python")
        self.assertEqual(profile["maturity"], "comprehensive-alpha")
        self.assertEqual(profile["requires"]["bbk_minimum"], "0.1.0-alpha.8")
        self.assertEqual(profile["capabilities"]["implementation_structure"]["status"], "supported")
        self.assertEqual(len(profile["skills"]), 15)
        for item in profile["skills"]:
            self.assertTrue((ROOT / item["path"]).is_file(), item)
        for path in profile["references"]:
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertTrue((ROOT / profile["gates"]).is_file())
        for path in profile["selection"].values():
            self.assertTrue((ROOT / path).is_file(), path)
        for path in [*sorted((ROOT / "schemas").glob("*.json")), *sorted((ROOT / "mappings").glob("*.json")), *sorted((ROOT / "gates").glob("*.json"))]:
            json.loads(path.read_text())

    def test_original_skill_is_preserved_and_corrections_are_present(self):
        provenance = json.loads((ROOT / "sources" / "original-digests.json").read_text())
        source = ROOT / provenance["sources"][0]["original_path"]
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), provenance["sources"][0]["sha256"])
        updated = (ROOT / "skills" / "comprehensive-analysis-python" / "SKILL.md").read_text()
        self.assertIn("Bare `raise` is the correct way", updated)
        self.assertIn("Generators are not an automatic improvement", updated)
        self.assertIn("Breaking Surfaces", updated)
        self.assertIn("Evidence:", updated)
        self.assertNotIn("one comprehensive list of findings per module", updated)
        self.assertNotIn("Flag missing `raise ... from` when re-raising", updated)

    def test_static_preflight_detects_project_package_and_support_signals(self):
        value, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", FIXTURE])
        self.assertEqual(value["schema"], "bbk.python-preflight.v1")
        self.assertEqual(value["project"]["name"], "fixture-pkg")
        self.assertEqual(value["project"]["requires_python"], ">=3.11")
        self.assertEqual(value["packaging"]["build_backend"], "setuptools.build_meta")
        self.assertEqual(value["project"]["source_roots"], ["src"])
        self.assertIn("fixture_pkg", value["packaging"]["packages"]["packages"])
        self.assertEqual(value["project"]["scripts"]["fixture-cli"], "fixture_pkg.api:main")
        self.assertIn("fixture.plugins", value["project"]["entry_point_groups"])
        self.assertTrue(value["packaging"]["locks"]["policy_detected"])
        self.assertTrue(value["support_signals"]["signals"]["native_extension"])
        self.assertTrue(value["support_signals"]["signals"]["asyncio"])
        self.assertRegex(value["digest"], r"^[0-9a-f]{64}$")

    def test_syntax_check_is_in_memory_and_reports_failures(self):
        value, _ = run_json([sys.executable, CLI, "--json", "syntax-check", "--root", FIXTURE, "--path", "src"])
        self.assertEqual(value["status"], "PASS")
        self.assertGreaterEqual(value["file_count"], 5)
        self.assertFalse(any(FIXTURE.rglob("*.pyc")))
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "pyproject.toml").write_text("[project]\nname='broken'\nversion='0.1'\n")
            (project / "bad.py").write_text("def broken(:\n")
            result = run([sys.executable, CLI, "--json", "syntax-check", "--root", project, "--path", "bad.py"], check=False)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["status"], "FAIL")

    def test_routine_worker_is_minimal_and_does_not_execute_project_tools(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "tool-executed"
            fakebin = Path(temp) / "bin"; fakebin.mkdir()
            for name in ["ruff", "pytest", "mypy", "build"]:
                path = fakebin / (f"{name}.cmd" if os.name == "nt" else name)
                if os.name == "nt":
                    path.write_text(f"@echo touched>{marker}\r\n")
                else:
                    path.write_text(f"#!/bin/sh\ntouch {marker!s}\nexit 91\n")
                    path.chmod(0o755)
            env = os.environ.copy(); env["PATH"] = str(fakebin) + os.pathsep + env.get("PATH", "")
            value, _ = run_json([
                sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
                "--role", "worker", "--task-profile", "implementation",
                "--assurance-tier", "routine", "--path", "src/fixture_pkg/api.py",
            ], env=env)
            self.assertFalse(marker.exists())
            self.assertEqual([item["id"] for item in value["selected_components"]], ["bbk-python"])
            self.assertEqual(
                [item["id"] for item in value["gate_plan"]["selected"]],
                ["python-syntax-check", "python-format-check", "python-lint-check", "python-focused-tests", "python-type-check-affected"],
            )
            self.assertTrue(value["recommended_validator_packs"])

    def test_public_distribution_validator_selects_api_and_package_only(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "validator", "--task-profile", "interface-schema-migration",
            "--assurance-tier", "consequential", "--hint", "public-api", "--hint", "distribution",
            "--path", "pyproject.toml", "--path", "src/fixture_pkg/__init__.py",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertEqual(selected, {"bbk-python", "python-api-package-boundary-review", "python-package-release-gates"})
        self.assertNotIn("comprehensive-analysis-python", selected)
        gates = {item["id"] for item in value["gate_plan"]["selected"]}
        self.assertTrue({"python-build-distributions", "python-installed-wheel-tests", "python-sdist-wheel-roundtrip"}.issubset(gates))
        self.assertNotIn("python-mutation", gates)
        self.assertNotIn("python-fuzz", gates)

    def test_async_and_process_scope_selects_runtime_and_test_packs(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "validator", "--task-profile", "integration-consumer-path",
            "--assurance-tier", "consequential", "--path", "src/fixture_pkg/async_service.py",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertTrue({"python-runtime-correctness-review", "python-test-strategy-review"}.issubset(selected))
        gates = {item["id"] for item in value["gate_plan"]["selected"]}
        self.assertIn("python-async-cancellation", gates)
        self.assertIn("python-process-start-methods", gates)
        self.assertNotIn("python-free-threaded", gates)

    def test_security_sensitive_scope_selects_security_and_runtime(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "validator", "--task-profile", "implementation",
            "--assurance-tier", "consequential", "--path", "src/fixture_pkg/security.py",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertTrue({"python-security-supply-chain-review", "python-runtime-correctness-review"}.issubset(selected))
        gates = {item["id"] for item in value["gate_plan"]["selected"]}
        self.assertIn("python-security-boundary", gates)

    def test_native_extension_selects_focused_assurance_without_free_thread_claim(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "validator", "--task-profile", "interface-schema-migration",
            "--assurance-tier", "consequential", "--path", "native/extension.c",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertTrue({"python-native-extension-review", "python-security-supply-chain-review", "python-runtime-correctness-review"}.issubset(selected))
        gates = {item["id"] for item in value["gate_plan"]["selected"]}
        self.assertIn("python-native-extension", gates)
        self.assertNotIn("python-free-threaded", gates)

    def test_broad_survey_does_not_fan_out_all_reviewers(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--task-profile", "investigation-prototype",
            "--assurance-tier", "material", "--hint", "broad-analysis",
        ])
        self.assertEqual({item["id"] for item in value["selected_components"]}, {"bbk-python", "comprehensive-analysis-python"})

    def test_explicit_mutation_hint_selects_test_evidence_and_gate(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "verification-designer", "--task-profile", "test-fixture",
            "--assurance-tier", "consequential", "--hint", "mutation-testing",
            "--path", "tests/test_api.py",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertTrue({"python-test-strategy-review", "python-evidence-reproducer"}.issubset(selected))
        gates = {item["id"] for item in value["gate_plan"]["selected"]}
        self.assertIn("python-mutation", gates)
        self.assertNotIn("python-fuzz", gates)

    def test_hypermedia_pack_is_optional_and_explicit(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--task-profile", "integration-consumer-path",
            "--assurance-tier", "material", "--hint", "hypermedia", "--path", "src/fixture_pkg/api.py",
        ])
        selected = {item["id"] for item in value["selected_components"]}
        self.assertIn("python-web-hypermedia-review", selected)
        routine, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--task-profile", "implementation",
            "--assurance-tier", "routine", "--path", "src/fixture_pkg/api.py",
        ])
        self.assertNotIn("python-web-hypermedia-review", {item["id"] for item in routine["selected_components"]})

    def test_effective_digest_is_deterministic(self):
        command = [
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "worker", "--task-profile", "implementation",
            "--assurance-tier", "routine", "--path", "src/fixture_pkg/api.py",
        ]
        left, _ = run_json(command)
        right, _ = run_json(command)
        self.assertEqual(left["effective_sha256"], right["effective_sha256"])
        self.assertRegex(left["effective_sha256"], r"^[0-9a-f]{64}$")

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
                console.log(JSON.stringify({{tools: tools.map(x => ({{name: x.name, parameterKeys: Object.keys(x.parameters || {{}})}})), commands: commands.map(x => x[0])}}));
            """), encoding="utf-8")
            value = json.loads(run(["node", script]).stdout)
            tool_names = {item["name"] for item in value["tools"]}
            self.assertIn("bbk_python_resolve", tool_names)
            self.assertIn("bbk_python_structure_review", tool_names)
            resolve_tool = next(item for item in value["tools"] if item["name"] == "bbk_python_resolve")
            self.assertTrue({"structureContract", "executionSlice", "workUnit"}.issubset(resolve_tool["parameterKeys"]))
            self.assertIn("bbk:python:gates", value["commands"])
            self.assertIn("bbk:python:structure-review", value["commands"])

    @unittest.skipUnless(shutil.which("node"), "node is required for installed OMP extension qualification")
    def test_installed_omp_extension_executes_profile_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            home = base / "home"; home.mkdir()
            env = os.environ.copy(); env.update({"HOME": str(home), "BBK_INSTALL_ROOT": str(base / "data"), "BBK_BIN_DIR": str(base / "bin")})
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "user", "--omp"], env=env)
            self.assertTrue(installed["omp"])
            extension = home / ".omp" / "agent" / "extensions" / "bbk-profile-python" / "index.js"
            script = base / "installed-python-omp-mock.mjs"
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
                const byName = name => {{
                  const value = tools.find(item => item.name === name);
                  if (!value) throw new Error(`missing ${{name}}`);
                  return value;
                }};
                const cwd = {json.dumps(str(FIXTURE))};
                const contract = {json.dumps(str(A4 / "contracts" / "package-consumer.json"))};
                const slice = {json.dumps(str(A4 / "slices" / "es-py-package.json"))};
                const reviewContract = {json.dumps(str(A4 / "contracts" / "public-typed-package.json"))};
                const candidate = {json.dumps(str(A4 / "candidates" / "conforming-candidate.json"))};
                const inventory = {json.dumps(str(A4 / "inventories" / "public-conforming.json"))};
                const invocations = [
                  ["bbk_python_preflight", {{root: cwd, runTools: false}}, "bbk.python-preflight.v1"],
                  ["bbk_python_resolve", {{root: cwd, role: "worker-designer", taskProfile: "execution-slicing", assuranceTier: "material", structureContract: contract, executionSlice: slice}}, "bbk.python-profile-resolution.v1"],
                  ["bbk_python_gate_plan", {{root: cwd, role: "worker-designer", taskProfile: "execution-slicing", assuranceTier: "material", structureContract: contract, executionSlice: slice}}, "bbk.python-gate-plan.v1"],
                  ["bbk_python_structure", {{root: cwd, contract, role: "architect", assuranceTier: "material"}}, "bbk.python.implementation-structure-projection.v1"],
                  ["bbk_python_slice", {{root: cwd, slice, contract, role: "worker-designer", assuranceTier: "material"}}, "bbk.python.execution-slice-projection.v1"],
                  ["bbk_python_structure_review", {{root: cwd, contract: reviewContract, candidate, actualInventory: inventory, assuranceTier: "material"}}, "bbk.python.structure-review-result.v1"],
                ];
                const schemas = [];
                let index = 0;
                for (const [name, params, schema] of invocations) {{
                  const result = await byName(name).execute(`call-${{++index}}`, params, undefined, undefined, {{cwd}});
                  if (result.isError || result.details?.schema !== schema) throw new Error(`${{name}}: ${{JSON.stringify(result.details)}}`);
                  schemas.push(schema);
                }}
                console.log(JSON.stringify({{schemas, tools: tools.length}}));
            """), encoding="utf-8")
            value = json.loads(run(["node", script], env=env).stdout)
            self.assertEqual(len(value["schemas"]), 6)
            self.assertIn("bbk.python.implementation-structure-projection.v1", value["schemas"])
            self.assertIn("bbk.python.structure-review-result.v1", value["schemas"])
            run([sys.executable, INSTALL, "uninstall", "--scope", "user"], env=env)
            self.assertTrue(home.exists())

    def test_user_install_and_uninstall_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"; home.mkdir()
            env = os.environ.copy(); env.update({"HOME": str(home), "BBK_INSTALL_ROOT": str(home / "data"), "BBK_BIN_DIR": str(home / "bin")})
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "user"], env=env)
            self.assertTrue(installed["codex"] and installed["omp"] and installed["claude"])
            self.assertEqual(len(list((home / ".agents" / "skills").glob("*/SKILL.md"))), 15)
            self.assertEqual(len(list((home / ".claude" / "skills").glob("*/SKILL.md"))), 15)
            self.assertTrue((home / ".omp" / "agent" / "extensions" / "bbk-profile-python" / "index.js").is_file())
            self.assertTrue((home / "bin" / ("bbk-python.cmd" if os.name == "nt" else "bbk-python")).is_file())
            current = json.loads((home / "data" / "profiles" / "python" / "current.json").read_text())
            self.assertEqual(current["version"], "0.1.0-alpha.3")
            status, _ = run_json([sys.executable, INSTALL, "--json", "status", "--scope", "user"], env=env)
            self.assertEqual(status["summary"].get("current"), len(status["files"]))
            modified = home / ".agents" / "skills" / "bbk-python" / "SKILL.md"
            modified.write_text(modified.read_text() + "\n<!-- local user modification -->\n")
            uninstalled, _ = run_json([sys.executable, INSTALL, "--json", "uninstall", "--scope", "user"], env=env)
            self.assertTrue(any(item["path"] == str(modified) and item["reason"] == "modified since install" for item in uninstalled["preserved"]))
            self.assertTrue(modified.exists())
            self.assertTrue(home.exists())
            self.assertFalse((home / "data" / "profile-install-manifests" / "python.json").exists())

    def test_force_activation_backs_up_replaced_selector_without_aliasing_live_path(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"; home.mkdir()
            data = home / "data"
            old_root = data / "profiles" / "python" / "0.1.0-alpha.1"
            old_root.mkdir(parents=True)
            (old_root / "PROFILE.json").write_text('{"id":"python","version":"0.1.0-alpha.1"}\n')
            current = data / "profiles" / "python" / "current.json"
            current.write_text(json.dumps({"schema":"bbk.current-profile.v1","id":"python","version":"0.1.0-alpha.1","path":str(old_root)}, indent=2) + "\n")
            env = os.environ.copy(); env.update({"HOME": str(home), "BBK_INSTALL_ROOT": str(data), "BBK_BIN_DIR": str(home / "bin")})
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "user", "--omp", "--force"], env=env)
            selector_records = [item for item in installed["files"] if item["path"] == str(current)]
            self.assertEqual(len(selector_records), 1)
            record = selector_records[0]
            self.assertEqual(record["action"], "replace")
            backup = Path(record["backup"])
            self.assertNotEqual(backup.resolve(), current.resolve())
            self.assertTrue(backup.is_file())
            self.assertEqual(json.loads(backup.read_text())["version"], "0.1.0-alpha.1")
            self.assertEqual(json.loads(current.read_text())["version"], "0.1.0-alpha.3")
            self.assertTrue((old_root / "PROFILE.json").is_file())

    def test_project_install_roundtrip_preserves_project_root(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"; project.mkdir()
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "project", "--root", project, "--omp"])
            self.assertFalse(installed["codex"]); self.assertTrue(installed["omp"]); self.assertFalse(installed["claude"])
            self.assertTrue((project / ".bbk-kit" / "profiles" / "python" / "0.1.0-alpha.3" / "PROFILE.json").is_file())
            self.assertTrue((project / ".omp" / "extensions" / "bbk-profile-python" / "index.js").is_file())
            modified = project / ".omp" / "extensions" / "bbk-profile-python" / "index.js"
            modified.write_text(modified.read_text() + "\n// local project modification\n")
            uninstalled, _ = run_json([sys.executable, INSTALL, "--json", "uninstall", "--scope", "project", "--root", project])
            self.assertTrue(any(item["path"] == str(modified) and item["reason"] == "modified since install" for item in uninstalled["preserved"]))
            self.assertTrue(modified.exists())
            self.assertTrue(project.exists())
            self.assertFalse((project / ".bbk-profile-python-install.json").exists())

    @unittest.skipUnless(CORE_CLI is not None and CORE_CLI.is_file(), "BBK alpha3 core reference is required")
    def test_bbk_alpha3_discovers_successor_but_rejects_alpha4_requirement(self):
        if not (ROOT / "PACKAGE-MANIFEST.json").is_file():
            self.skipTest("package manifest is written by the release builder")
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"; home.mkdir()
            env = os.environ.copy(); env.update({"HOME": str(home), "BBK_INSTALL_ROOT": str(home / "data"), "BBK_BIN_DIR": str(home / "bin")})
            run([sys.executable, INSTALL, "install", "--scope", "user", "--omp"], env=env)
            listing, _ = run_json([sys.executable, CORE_CLI, "--json", "profile", "list"], env=env, cwd=FIXTURE)
            python_profiles = [item for item in listing["profiles"] if item.get("id") == "python"]
            self.assertEqual(len(python_profiles), 1)
            self.assertEqual(python_profiles[0]["package_verification"]["status"], "PASS")
            self.assertEqual(python_profiles[0]["compatibility"]["status"], "FAIL")
            self.assertFalse(python_profiles[0]["compatibility"]["bbk_compatible"])
            result = run([
                sys.executable, CORE_CLI, "--json", "profile", "resolve", "--id", "python",
                "--root", FIXTURE, "--role", "worker", "--task-profile", "implementation",
                "--assurance-tier", "routine", "--path", "src/fixture_pkg/api.py",
            ], env=env, cwd=FIXTURE, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("incompatible", json.loads(result.stdout)["error"].lower())
            run([sys.executable, INSTALL, "uninstall", "--scope", "user"], env=env)



if __name__ == "__main__":
    unittest.main()
