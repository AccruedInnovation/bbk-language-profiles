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
CLI = ROOT / "tools" / "bbk_go.py"
INSTALL = ROOT / "tools" / "install.py"
FIXTURE = ROOT / "fixtures" / "go-workspace"
NEGATIVE = ROOT / "fixtures" / "negative"
ALPHA4 = ROOT / "fixtures" / "alpha4"
BBK_CORE = Path(os.environ.get("BBK_CORE_CLI", "/nonexistent/bbk-alpha4/tools/bbk.py"))


def run(command, *, cwd=None, env=None, check=True):
    completed = subprocess.run(
        [str(item) for item in command],
        cwd=str(cwd or ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )
    if check and completed.returncode != 0:
        raise AssertionError(
            f"command failed ({completed.returncode}): {command}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def run_json(command, **kwargs):
    result = run(command, **kwargs)
    try:
        return json.loads(result.stdout), result
    except json.JSONDecodeError as exc:
        raise AssertionError(f"invalid JSON from {command}: {exc}\n{result.stdout}\n{result.stderr}") from exc


def selected(value):
    return {item["id"] for item in value["selected_components"]}


def gates(value):
    return {item["id"] for item in value["gate_plan"]["selected"]}


class GoProfileTests(unittest.TestCase):
    def test_profile_manifest_and_skill_references(self):
        profile = json.loads((ROOT / "PROFILE.json").read_text())
        self.assertEqual(profile["schema"], "bbk.language-profile.v1")
        self.assertEqual(profile["id"], "go")
        self.assertEqual(profile["maturity"], "comprehensive-alpha")
        self.assertEqual(profile["requires"]["bbk_minimum"], "0.1.0-alpha.8")
        self.assertEqual(len(profile["skills"]), 14)
        for item in profile["skills"]:
            path = ROOT / item["path"]
            self.assertTrue(path.is_file(), item)
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), item["id"])
        for path in [profile["gates"], *profile["selection"].values(), *profile["references"]]:
            self.assertTrue((ROOT / path).is_file(), path)

    def test_uploaded_source_digest_is_preserved(self):
        record = json.loads((ROOT / "sources" / "original-digests.json").read_text())
        source = Path("/mnt/data/comprehensive-analysis-go.md")
        if source.is_file():
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(record["files"][0]["sha256"], digest)
        self.assertEqual(record["files"][0]["disposition"], "preserved-as-user-source")

    def test_schemas_cover_profile_and_runtime_outputs_without_third_party_dependencies(self):
        def validate_required_and_consts(value, schema):
            self.assertIsInstance(value, dict)
            for key in schema.get("required", []):
                self.assertIn(key, value)
            for key, definition in schema.get("properties", {}).items():
                if "const" in definition and key in value:
                    self.assertEqual(value[key], definition["const"])
                if definition.get("type") == "array" and key in value:
                    self.assertIsInstance(value[key], list)
                if definition.get("type") == "object" and key in value:
                    self.assertIsInstance(value[key], dict)
                if definition.get("type") == "string" and key in value:
                    self.assertIsInstance(value[key], str)

        profile = json.loads((ROOT / "PROFILE.json").read_text())
        profile_schema = json.loads((ROOT / "schemas" / "bbk-language-profile-v1.schema.json").read_text())
        validate_required_and_consts(profile, profile_schema)
        preflight, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", FIXTURE])
        preflight_schema = json.loads((ROOT / "schemas" / "bbk-go-preflight-v1.schema.json").read_text())
        validate_required_and_consts(preflight, preflight_schema)
        resolution, _ = run_json([sys.executable, CLI, "--json", "resolve", "--root", FIXTURE, "--path", "cmd/app/main.go"])
        resolution_schema = json.loads((ROOT / "schemas" / "bbk-go-resolution-v1.schema.json").read_text())
        validate_required_and_consts(resolution, resolution_schema)

    def test_gate_recipes_are_nonexecuting_and_have_no_shell_operators(self):
        value = json.loads((ROOT / "gates" / "go-gates.json").read_text())
        self.assertTrue(value["policy"]["no_silent_install"])
        self.assertTrue(value["policy"]["no_silent_toolchain_download"])
        for recipe in value["recipes"]:
            self.assertIsInstance(recipe.get("command"), list, recipe["id"])
            self.assertFalse({"&&", "||", ";", "|"} & set(recipe["command"]), recipe["id"])
            self.assertIn(recipe["minimum_tier"], {"routine", "material", "consequential", "critical"})

    def test_static_preflight_detects_workspace_modules_and_signals(self):
        value, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", FIXTURE])
        self.assertEqual(value["schema"], "bbk.go-preflight.v1")
        self.assertTrue(value["workspace"]["active"])
        self.assertEqual(value["workspace"]["module_paths"], ["example.com/bbk/api", "example.com/bbk/cmd"])
        self.assertEqual(value["toolchain"]["workspace_toolchain"], "go1.23.2")
        signals = value["support_signals"]
        for key in ["unsafe", "cgo", "generation", "concurrency", "http", "htmx"]:
            self.assertTrue(signals[key], key)
        self.assertIn("bbk_native", " ".join(value["modules"][0]["build_tags"]))

    @unittest.skipUnless(shutil.which("go"), "Go toolchain is required")
    def test_tool_preflight_is_offline_and_records_exact_toolchain(self):
        value, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", FIXTURE, "--run-tools"])
        observed = value["tool_observations"]
        self.assertEqual(observed["go_version"]["returncode"], 0)
        self.assertIn("go version", observed["go_version"]["stdout"])
        self.assertEqual(observed["go_env"]["returncode"], 0)
        self.assertIn("GOVERSION", observed["go_env"]["parsed"]["safe"])

    def test_routine_worker_receives_minimal_profile_and_gates(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "worker", "--task-profile", "implementation",
            "--assurance-tier", "routine", "--path", "cmd/app/main.go",
        ])
        self.assertEqual(selected(value), {"bbk-go", "go-skills"})
        self.assertEqual(gates(value), {"go-format-check", "go-focused-tests", "go-compile-affected", "go-vet-affected"})
        self.assertNotIn("comprehensive-analysis-go", selected(value))
        self.assertTrue(all(item["execution"] == "planned-only" for item in value["gate_plan"]["selected"]))

    def test_public_wire_change_selects_api_correctness_not_unrelated_packs(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "validator", "--task-profile", "interface-schema-migration",
            "--assurance-tier", "consequential", "--change-class", "interface",
            "--change-class", "schema", "--hint", "wire-format", "--path", "api/api.go",
        ])
        self.assertTrue({"go-api-module-boundary-review", "go-correctness-concurrency-review"}.issubset(selected(value)))
        self.assertNotIn("go-unsafe-cgo-assembly-review", selected(value))
        self.assertNotIn("go-web-htmx-review", selected(value))
        self.assertNotIn("comprehensive-analysis-go", selected(value))

    def test_concurrency_change_selects_correctness_and_test_methods(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "validator", "--task-profile", "implementation",
            "--assurance-tier", "consequential", "--hint", "concurrency", "--path", "api/api.go",
        ])
        self.assertTrue({"go-correctness-concurrency-review", "go-test-strategy-review"}.issubset(selected(value)))
        self.assertIn("go-race", gates(value))
        self.assertIn("go-synctest", gates(value))

    def test_unsafe_cgo_selects_native_boundary_assurance(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "validator", "--task-profile", "interface-schema-migration",
            "--assurance-tier", "consequential", "--hint", "cgo",
            "--path", "api/internal/native/native.go",
        ])
        self.assertTrue({
            "go-unsafe-cgo-assembly-review", "go-correctness-concurrency-review",
            "go-security-supply-chain-review",
        }.issubset(selected(value)))
        self.assertIn("go-checkptr", gates(value))
        self.assertNotIn("go-web-htmx-review", selected(value))

    def test_web_lens_is_optional_and_explicit(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--task-profile", "implementation",
            "--assurance-tier", "material", "--hint", "htmx", "--path", "api/web/handler.go",
        ])
        self.assertIn("go-web-htmx-review", selected(value))
        plain, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--task-profile", "implementation",
            "--assurance-tier", "material", "--path", "cmd/app/main.go",
        ])
        self.assertNotIn("go-web-htmx-review", selected(plain))

    def test_broad_survey_does_not_fan_out_all_reviewers(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--task-profile", "investigation-prototype",
            "--assurance-tier", "material", "--hint", "broad-analysis",
        ])
        self.assertEqual(selected(value), {"bbk-go", "comprehensive-analysis-go"})

    def test_module_release_selects_release_and_compatibility_packs(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", NEGATIVE / "local-replace",
            "--role", "validator", "--task-profile", "packaging-release",
            "--assurance-tier", "consequential", "--hint", "module-release",
            "--path", "go.mod",
        ])
        self.assertTrue({
            "go-api-module-boundary-review", "go-security-supply-chain-review",
            "go-package-release-gates", "go-operational-readiness-review",
        }.issubset(selected(value)))
        self.assertIn("go-standalone-module", gates(value))
        self.assertIn("go-module-release", gates(value))

    def test_hidden_parent_workspace_and_gowork_off_are_distinct(self):
        child = NEGATIVE / "hidden-parent-workspace" / "child"
        value, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", child])
        self.assertTrue(value["workspace"]["active"])
        self.assertEqual(Path(value["root"]), NEGATIVE / "hidden-parent-workspace")
        env = os.environ.copy(); env["GOWORK"] = "off"
        standalone, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", child], env=env)
        self.assertFalse(standalone["workspace"]["active"])
        self.assertEqual(Path(standalone["root"]), child)

    def test_local_replace_and_future_toolchain_are_visible_without_download(self):
        replace, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", NEGATIVE / "local-replace"])
        directives = replace["modules"][0]["go_mod"]["directives"]
        self.assertTrue(directives["replace"])
        future, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", NEGATIVE / "stale-toolchain"])
        self.assertEqual(future["toolchain"]["module_toolchain"]["example.com/future"], "go1.99.0")
        self.assertEqual(future["tool_observations"], {})

    def test_generated_drift_fixture_selects_generation_assurance(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", NEGATIVE / "generated-drift",
            "--role", "validator", "--task-profile", "test-fixture",
            "--assurance-tier", "material", "--hint", "generated-code", "--path", "generated.go",
        ])
        self.assertTrue({"go-test-strategy-review", "go-security-supply-chain-review"}.issubset(selected(value)))
        self.assertIn("go-generate-diff", gates(value))

    def test_negative_fixture_registry_covers_required_cases(self):
        value = json.loads((ROOT / "fixtures" / "negative-cases.json").read_text())
        ids = {item["id"] for item in value["cases"]}
        required = {
            "hidden-parent-go-work", "local-replace-masks-release", "cached-tests-not-fresh",
            "goroutine-leak-after-cancellation", "typed-nil-interface", "map-order-output",
            "generated-code-drift", "race-requires-representative-workload",
            "stale-or-unavailable-toolchain", "cgo-pointer-lifetime",
            "workspace-module-release", "breaking-error-http-contract",
        }
        self.assertEqual(ids, required)

    def test_effective_digest_is_deterministic(self):
        command = [
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "worker", "--task-profile", "implementation",
            "--assurance-tier", "routine", "--path", "cmd/app/main.go",
        ]
        env = os.environ.copy(); env["BBK_LOCK_TIMESTAMP"] = "2026-07-23T00:00:00Z"
        left, _ = run_json(command, env=env)
        right, _ = run_json(command, env=env)
        self.assertEqual(left["effective_sha256"], right["effective_sha256"])
        self.assertEqual(left["lock"], right["lock"])

    @unittest.skipUnless(shutil.which("go"), "Go toolchain is required")
    def test_fixture_build_test_vet_and_format(self):
        run(["go", "test", "./api/...", "./cmd/..."], cwd=FIXTURE)
        run(["go", "vet", "./api/...", "./cmd/..."], cwd=FIXTURE)
        value, result = run_json([sys.executable, CLI, "--json", "check-format", "--root", FIXTURE])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(value["status"], "PASS")

    @unittest.skipUnless(shutil.which("node"), "Node is required for OMP extension qualification")
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
            self.assertIn("bbk_go_resolve", value["tools"])
            self.assertIn("bbk:go:gates", value["commands"])

    @unittest.skipUnless(shutil.which("node"), "Node is required for installed OMP extension qualification")
    def test_installed_omp_extension_executes_profile_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); home = base / "home"; home.mkdir()
            env = os.environ.copy(); env.update({
                "HOME": str(home), "BBK_INSTALL_ROOT": str(base / "data"), "BBK_BIN_DIR": str(base / "bin"),
            })
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "user", "--omp"], env=env)
            self.assertTrue(installed["omp"])
            extension = home / ".omp" / "agent" / "extensions" / "bbk-profile-go" / "index.js"
            script = base / "installed-go-omp-mock.mjs"
            script.write_text(textwrap.dedent(f"""
                const chain = () => ({{ optional() {{ return this; }} }});
                const z = {{ object: value => value, string: chain, boolean: chain,
                  enum: values => chain(), array: value => chain() }};
                const tools = [], commands = [], handlers = [];
                const pi = {{ zod: {{ z }}, setLabel() {{}},
                  registerTool(value) {{ tools.push(value); }},
                  registerCommand(name, value) {{ commands.push([name, value]); }},
                  on(name, value) {{ handlers.push([name, value]); }}, sendMessage() {{}} }};
                const mod = await import({json.dumps(extension.as_uri())}); mod.default(pi);
                const tool = tools.find(value => value.name === 'bbk_go_preflight');
                if (!tool) throw new Error('missing bbk_go_preflight');
                const result = await tool.execute('call-1', {{root: {json.dumps(str(FIXTURE))}, runTools: false}}, undefined, undefined, {{cwd: {json.dumps(str(FIXTURE))}}});
                if (result.isError || result.details?.schema !== 'bbk.go-preflight.v1')
                  throw new Error(JSON.stringify(result.details));
                const structure = tools.find(value => value.name === 'bbk_go_structure');
                if (!structure) throw new Error('missing bbk_go_structure');
                const structureResult = await structure.execute('call-2', {{
                  root: {json.dumps(str(FIXTURE))},
                  contract: {json.dumps(str(ALPHA4 / 'structure' / 'go-service-contract.json'))},
                  assuranceTier: 'consequential',
                  runTools: false,
                }}, undefined, undefined, {{cwd: {json.dumps(str(FIXTURE))}}});
                if (structureResult.isError || structureResult.details?.schema !== 'bbk.go.implementation-structure-projection.v1')
                  throw new Error(JSON.stringify(structureResult.details));
                console.log(JSON.stringify({{schema: result.details.schema, structureSchema: structureResult.details.schema, tools: tools.length}}));
            """), encoding="utf-8")
            value = json.loads(run(["node", script], env=env).stdout)
            self.assertEqual(value["schema"], "bbk.go-preflight.v1")
            self.assertEqual(value["structureSchema"], "bbk.go.implementation-structure-projection.v1")
            run([sys.executable, INSTALL, "uninstall", "--scope", "user"], env=env)
            self.assertTrue(home.exists())

    def test_user_install_and_uninstall_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"; home.mkdir()
            env = os.environ.copy(); env.update({
                "HOME": str(home), "BBK_INSTALL_ROOT": str(home / "data"), "BBK_BIN_DIR": str(home / "bin"),
            })
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "user"], env=env)
            self.assertTrue(installed["codex"] and installed["omp"] and installed["claude"])
            self.assertEqual(len(list((home / ".agents" / "skills").glob("*/SKILL.md"))), 14)
            self.assertEqual(len(list((home / ".claude" / "skills").glob("*/SKILL.md"))), 14)
            self.assertTrue((home / ".omp" / "agent" / "extensions" / "bbk-profile-go" / "index.js").is_file())
            self.assertTrue((home / "bin" / ("bbk-go.cmd" if os.name == "nt" else "bbk-go")).is_file())
            current = json.loads((home / "data" / "profiles" / "go" / "current.json").read_text())
            self.assertEqual(current["version"], "0.1.0-alpha.3")
            status, _ = run_json([sys.executable, INSTALL, "--json", "status", "--scope", "user"], env=env)
            self.assertEqual(status["summary"].get("current"), len(status["files"]))
            run([sys.executable, INSTALL, "uninstall", "--scope", "user"], env=env)
            self.assertTrue(home.exists())
            self.assertFalse((home / "data" / "profile-install-manifests" / "go.json").exists())

    def test_project_install_roundtrip_preserves_project_root(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"; project.mkdir()
            installed, _ = run_json([
                sys.executable, INSTALL, "--json", "install", "--scope", "project", "--root", project, "--omp",
            ])
            self.assertFalse(installed["codex"]); self.assertTrue(installed["omp"]); self.assertFalse(installed["claude"])
            self.assertTrue((project / ".bbk-kit" / "profiles" / "go" / "0.1.0-alpha.3" / "PROFILE.json").is_file())
            self.assertTrue((project / ".omp" / "extensions" / "bbk-profile-go" / "index.js").is_file())
            run([sys.executable, INSTALL, "uninstall", "--scope", "project", "--root", project])
            self.assertTrue(project.exists())
            self.assertFalse((project / ".bbk-profile-go-install.json").exists())

    def test_alpha4_profile_capability_and_entrypoints(self):
        profile = json.loads((ROOT / "PROFILE.json").read_text())
        capability = profile["capabilities"]["implementation_structure"]
        self.assertEqual(capability["status"], "supported")
        self.assertIn("go-package", capability["artifact_kinds"])
        self.assertIn("goroutine-ownership", capability["type_concepts"])
        self.assertIn("downstream-consumer", capability["touchpoint_kinds"])
        for name in ["structure", "slice", "structure_review"]:
            self.assertIn(name, profile["entrypoints"])
        for key in ["may_declare_pass", "may_expand_work_scope", "may_grant_tools_or_effects", "may_reduce_assurance"]:
            self.assertFalse(profile["authority"][key])

    def test_generic_and_profile_schemas_parse_and_positive_fixtures_validate(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bbk_go_module", CLI)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        for path in sorted((ROOT / "schemas").glob("*.json")):
            json.loads(path.read_text())
        pairs = [
            (ALPHA4 / "structure" / "go-service-contract.json", ROOT / "schemas" / "bbk-implementation-structure-contract-v1.schema.json"),
            (ALPHA4 / "structure" / "routine-inline-contract.json", ROOT / "schemas" / "bbk-implementation-structure-contract-v1.schema.json"),
            (ALPHA4 / "structure" / "migration-contract.json", ROOT / "schemas" / "bbk-implementation-structure-contract-v1.schema.json"),
            (ALPHA4 / "structure" / "cgo-contract.json", ROOT / "schemas" / "bbk-implementation-structure-contract-v1.schema.json"),
            (ALPHA4 / "unsupported" / "procedure-contract.json", ROOT / "schemas" / "bbk-implementation-structure-contract-v1.schema.json"),
            (ALPHA4 / "slices" / "go-save-slice.json", ROOT / "schemas" / "bbk-execution-slice-v1.schema.json"),
            (ALPHA4 / "slices" / "go-stream-slice.json", ROOT / "schemas" / "bbk-execution-slice-v1.schema.json"),
            (ALPHA4 / "slices" / "module-downstream-slice.json", ROOT / "schemas" / "bbk-execution-slice-v1.schema.json"),
        ]
        for value_path, schema_path in pairs:
            value = json.loads(value_path.read_text())
            schema = json.loads(schema_path.read_text())
            self.assertEqual(module.schema_errors(value, schema), [], value_path)

    def test_profile_projection_and_review_outputs_validate_against_namespaced_schemas(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bbk_go_output_module", CLI)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        commands = [
            ([sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
              "--contract", ALPHA4 / "structure" / "go-service-contract.json"],
             "bbk-go-implementation-structure-projection-v1.schema.json"),
            ([sys.executable, CLI, "--json", "slice", "--root", FIXTURE,
              "--slice", ALPHA4 / "slices" / "go-save-slice.json"],
             "bbk-go-execution-slice-projection-v1.schema.json"),
            ([sys.executable, CLI, "--json", "structure-review", "--root", FIXTURE,
              "--contract", ALPHA4 / "structure" / "go-service-contract.json",
              "--candidate", ALPHA4 / "candidates" / "candidate.json",
              "--actual-inventory", ALPHA4 / "actual" / "conforms.json",
              "--assurance-tier", "consequential"],
             "bbk-go-structure-review-result-v1.schema.json"),
        ]
        for command, schema_name in commands:
            value, _ = run_json(command)
            schema = json.loads((ROOT / "schemas" / schema_name).read_text())
            self.assertEqual(module.schema_errors(value, schema), [], schema_name)
        review, _ = run_json(commands[-1][0])
        comparison_schema = json.loads((ROOT / "schemas" / "bbk-go-planned-actual-structure-comparison-v1.schema.json").read_text())
        self.assertEqual(module.schema_errors(review["comparison"], comparison_schema), [])

    def test_invalid_generic_contract_fails_closed(self):
        result = run([
            sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
            "--contract", ALPHA4 / "structure" / "invalid-contract.json",
        ], check=False)
        self.assertEqual(result.returncode, 2)
        value = json.loads(result.stdout)
        self.assertEqual(value["status"], "ERROR")
        self.assertIn("schema validation failed", value["error"])

    def test_routine_inline_structure_remains_minimal(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "worker", "--assurance-tier", "routine",
            "--contract", ALPHA4 / "structure" / "routine-inline-contract.json",
            "--path", "api/api.go",
        ])
        self.assertEqual(value["implementation_structure"]["support"], "supported")
        projection = value["implementation_structure"]["structure_projection"]
        self.assertEqual(projection["applicability"]["level"], "inline")
        self.assertFalse(projection["review_selection"]["selected"])
        self.assertNotIn("go-implementation-structure-review", selected(value))
        self.assertIn("go-implementation-structure", selected(value))

    def test_material_public_contract_selects_structure_and_focused_reviews(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--assurance-tier", "consequential",
            "--contract", ALPHA4 / "structure" / "go-service-contract.json",
            "--path", "api/api.go",
        ])
        self.assertTrue({"go-implementation-structure-review", "go-api-module-boundary-review", "go-correctness-concurrency-review"}.issubset(selected(value)))
        self.assertNotIn("go-web-htmx-review", selected(value))
        self.assertIn("go-structure-projection", gates(value))
        self.assertIn("go-planned-actual-structure", gates(value))
        self.assertEqual(value["lock"]["profiles"][0]["implementation_structure"]["contract_sha256"], value["inputs"]["structure_contract_sha256"])

    def test_execution_slice_projection_and_foundation_policy(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "slice", "--root", FIXTURE,
            "--slice", ALPHA4 / "slices" / "go-stream-slice.json",
            "--assurance-tier", "consequential",
        ])
        self.assertEqual(value["schema"], "bbk.go.execution-slice-projection.v1")
        self.assertEqual(value["foundation_assessment"]["status"], "ACCEPTABLE")
        self.assertEqual(value["projection"]["integration_owner"], "Worker Orchestrator: Go save path")
        valid, _ = run_json([
            sys.executable, CLI, "--json", "slice", "--root", FIXTURE,
            "--slice", ALPHA4 / "slices" / "foundation-valid-slice.json",
            "--assurance-tier", "consequential",
        ])
        self.assertTrue(valid["foundation_assessment"]["allowed_exception"])
        invalid, result = run_json([
            sys.executable, CLI, "--json", "slice", "--root", FIXTURE,
            "--slice", ALPHA4 / "slices" / "foundation-invalid-slice.json",
            "--assurance-tier", "consequential",
        ], check=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(invalid["foundation_assessment"]["status"], "BLOCKING")
        self.assertTrue(invalid["blockers"])

    def test_structure_review_tolerates_delegated_private_divergence(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURE,
            "--contract", ALPHA4 / "structure" / "go-service-contract.json",
            "--candidate", ALPHA4 / "candidates" / "candidate.json",
            "--actual-inventory", ALPHA4 / "actual" / "harmless-private-divergence.json",
            "--assurance-tier", "consequential",
        ])
        self.assertEqual(value["disposition"], "CONFORMS")
        self.assertEqual(value["comparison"]["summary"]["within-delegated-freedom"], 1)
        self.assertEqual(value["findings"], [])

    def test_structure_review_detects_fixed_decision_divergence(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURE,
            "--contract", ALPHA4 / "structure" / "go-service-contract.json",
            "--candidate", ALPHA4 / "candidates" / "candidate.json",
            "--actual-inventory", ALPHA4 / "actual" / "material-package-owner-divergence.json",
            "--assurance-tier", "consequential",
        ], check=False)
        self.assertEqual(value["disposition"], "MATERIAL_DIVERGENCE")
        self.assertEqual(value["findings"][0]["planned_ref"], "FD-PACKAGE-OWNER")

    def test_structure_review_blocks_unknown_fixed_evidence_at_consequential_tier(self):
        value, result = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURE,
            "--contract", ALPHA4 / "structure" / "go-service-contract.json",
            "--candidate", ALPHA4 / "candidates" / "candidate.json",
            "--actual-inventory", ALPHA4 / "actual" / "unknown-fixed-evidence.json",
            "--assurance-tier", "consequential",
        ], check=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(value["disposition"], "BLOCKED")
        self.assertEqual(value["comparison"]["summary"]["unknown"], 2)

    def test_unsupported_subject_returns_bounded_projection(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
            "--contract", ALPHA4 / "unsupported" / "procedure-contract.json",
        ])
        self.assertEqual(value["applicability"]["disposition"], "UNSUPPORTED")
        self.assertEqual(value["projection"], {})
        self.assertTrue(value["unsupported_or_uncertain"])

    def test_requested_missing_go_tool_is_blocked_not_skipped(self):
        env = os.environ.copy()
        env["PATH"] = "/definitely-missing"
        result = run([
            sys.executable, CLI, "--json", "structure", "--root", FIXTURE,
            "--contract", ALPHA4 / "structure" / "go-service-contract.json",
            "--run-tools",
        ], env=env, check=False)
        self.assertEqual(result.returncode, 1)
        value = json.loads(result.stdout)
        self.assertTrue(any(item["code"] == "REQUIRED_GO_TOOL_UNAVAILABLE" for item in value["blockers"]))

    def test_consequential_migration_selects_structure_migration_evidence_and_consumer_checks(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--task-profile", "interface-schema-migration",
            "--assurance-tier", "consequential", "--change-class", "migration",
            "--contract", ALPHA4 / "structure" / "migration-contract.json",
            "--slice", ALPHA4 / "slices" / "module-downstream-slice.json",
        ])
        self.assertTrue({
            "go-implementation-structure-review", "go-api-module-boundary-review",
            "go-correctness-concurrency-review", "go-test-strategy-review",
            "go-evidence-reproducer",
        }.issubset(selected(value)))
        self.assertIn("go-planned-actual-structure", gates(value))
        self.assertIn("go-slice-touchpoint-evidence", gates(value))
        self.assertIn("go-downstream-compat", gates(value))

    def test_actual_inventory_conforms_to_profile_schema(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bbk_go_inventory_module", CLI)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        value, _ = run_json([sys.executable, CLI, "--json", "inventory", "--root", FIXTURE])
        schema = json.loads((ROOT / "schemas" / "bbk-go-actual-structure-inventory-v1.schema.json").read_text())
        self.assertEqual(module.schema_errors(value, schema), [])

    def test_profile_lock_contains_contract_slice_and_projection_digests(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURE,
            "--role", "reviewer", "--assurance-tier", "consequential",
            "--contract", ALPHA4 / "structure" / "go-service-contract.json",
            "--slice", ALPHA4 / "slices" / "go-stream-slice.json",
        ])
        structure = value["implementation_structure"]
        lock = value["lock"]["profiles"][0]["implementation_structure"]
        self.assertEqual(lock["contract_sha256"], value["inputs"]["structure_contract_sha256"])
        self.assertEqual(lock["slice_sha256"], value["inputs"]["execution_slice_sha256"])
        self.assertEqual(lock["structure_projection_sha256"], structure["structure_projection"]["output_sha256"])
        self.assertEqual(lock["slice_projection_sha256"], structure["slice_projection"]["output_sha256"])

    def test_structure_and_slice_outputs_are_deterministic(self):
        commands = [
            [sys.executable, CLI, "--json", "structure", "--root", FIXTURE, "--contract", ALPHA4 / "structure" / "go-service-contract.json"],
            [sys.executable, CLI, "--json", "slice", "--root", FIXTURE, "--slice", ALPHA4 / "slices" / "go-save-slice.json"],
        ]
        for command in commands:
            left, _ = run_json(command)
            right, _ = run_json(command)
            self.assertEqual(left, right)
            self.assertEqual(left["output_sha256"], right["output_sha256"])

    def test_legacy_alpha3_profile_fixture_is_unprojected(self):
        legacy = json.loads((ROOT / "fixtures" / "alpha4" / "legacy" / "PROFILE-alpha3.json").read_text())
        support = legacy.get("capabilities", {}).get("implementation_structure", {}).get("status", "legacy-unprojected")
        self.assertEqual(support, "legacy-unprojected")

    def test_bbk_alpha4_discovers_and_resolves_manifested_profile(self):
        if not BBK_CORE.is_file() or not (ROOT / "PACKAGE-MANIFEST.json").is_file():
            self.skipTest("BBK alpha.4 core or package manifest unavailable")
        listed, _ = run_json([sys.executable, BBK_CORE, "--json", "profile", "list", "--profile-dir", ROOT])
        match = next(item for item in listed["profiles"] if item.get("id") == "go")
        self.assertEqual(match["package_verification"]["status"], "PASS")
        self.assertEqual(match["compatibility"]["status"], "PASS")
        resolved, _ = run_json([
            sys.executable, BBK_CORE, "--json", "profile", "resolve", "--profile-dir", ROOT,
            "--id", "go", "--source", FIXTURE, "--role", "worker",
            "--task-profile", "implementation", "--assurance-tier", "routine",
            "--path", "cmd/app/main.go",
        ])
        self.assertEqual(resolved["resolution"]["schema"], "bbk.go-profile-resolution.v1")
        self.assertEqual(resolved["profile"]["package_verification"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
