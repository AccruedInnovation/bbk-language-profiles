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
CLI = ROOT / "tools" / "bbk_tsjs.py"
INSTALL = ROOT / "tools" / "install.py"
FIXTURES = ROOT / "fixtures"
BBK_CORE_ROOT = Path(os.environ.get("BBK_CORE_ROOT", "")) if os.environ.get("BBK_CORE_ROOT") else None


def run(command, *, cwd=None, env=None, check=True):
    return subprocess.run(
        [str(item) for item in command],
        cwd=str(cwd or ROOT),
        env=env,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def run_json(command, *, cwd=None, env=None, check=True):
    result = run(command, cwd=cwd, env=env, check=check)
    return json.loads(result.stdout), result


def selected_ids(value):
    return [item["id"] for item in value["selected_components"]]


def gate_ids(value):
    return [item["id"] for item in value["gate_plan"]["selected"]]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TypeScriptJavaScriptProfileTests(unittest.TestCase):
    def test_profile_manifest_and_internal_references(self):
        profile = json.loads((ROOT / "PROFILE.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["schema"], "bbk.language-profile.v1")
        self.assertEqual(profile["id"], "typescript-javascript")
        self.assertEqual(profile["package"], "bbk-profile-typescript-javascript")
        self.assertEqual(profile["version"], "0.1.0-alpha.3")
        self.assertEqual(profile["maturity"], "comprehensive-alpha")
        self.assertEqual(profile["requires"]["bbk_minimum"], "0.1.0-alpha.8")
        self.assertFalse(profile["authority"]["may_grant_tools_or_effects"])
        self.assertFalse(profile["authority"]["may_reduce_assurance"])
        self.assertFalse(profile["authority"]["may_declare_pass"])
        self.assertEqual(profile["capabilities"]["implementation_structure"]["status"], "supported")
        self.assertEqual(set(profile["entrypoints"]), {"preflight", "resolve", "gate_plan", "structure", "slice", "structure_review", "state_effect", "state_effect_inventory", "state_effect_review", "review_context", "review_lens", "evidence_adapter"})
        self.assertEqual(len(profile["skills"]), 13)
        self.assertEqual(len({item["id"] for item in profile["skills"]}), 13)
        for item in profile["skills"]:
            skill = ROOT / item["path"]
            self.assertTrue(skill.is_file(), item)
            frontmatter = skill.read_text(encoding="utf-8").split("---", 2)[1]
            self.assertIn(f"name: {item['id']}", frontmatter)
        for path in profile["references"]:
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertTrue((ROOT / profile["gates"]).is_file())
        for path in profile["selection"].values():
            self.assertTrue((ROOT / path).is_file(), path)
        for path in [ROOT / "PROFILE.json", *sorted((ROOT / "schemas").glob("*.json")), *sorted((ROOT / "mappings").glob("*.json")), *sorted((ROOT / "gates").glob("*.json"))]:
            json.loads(path.read_text(encoding="utf-8"))

    def test_source_provenance_and_comprehensive_analysis_changes(self):
        provenance = json.loads((ROOT / "sources" / "original-digests.json").read_text(encoding="utf-8"))
        record = provenance["sources"][0]
        self.assertEqual(record["name"], "comprehensive-analysis.md")
        self.assertEqual(record["bytes"], 7737)
        self.assertEqual(record["sha256"], "aabf5069145bb1e047d95d43c5052bf76c810eb3076283997121c84d4b47305d")
        source = Path(os.environ.get("BBK_SOURCE_COMPREHENSIVE_ANALYSIS", "/mnt/data/comprehensive-analysis.md"))
        if source.is_file():
            self.assertEqual(source.stat().st_size, record["bytes"])
            self.assertEqual(sha256(source), record["sha256"])
        changed = (ROOT / "skills" / "comprehensive-analysis-tsjs" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("material correctness, security, compatibility, operability, testability, and maintainability findings", changed)
        self.assertIn("Compatibility impact", changed)
        self.assertIn("Coverage summary", changed)
        self.assertIn("non-overlapping assertion families", changed)
        self.assertNotIn("bloated JS where HTMX/Alpine", changed)
        self.assertNotIn("Breaking:** yes/no", changed)


    def test_preflight_does_not_enumerate_or_hash_secret_environment_values(self):
        env = os.environ.copy()
        env["BBK_TEST_SUPER_SECRET_TOKEN"] = "low-entropy-secret"
        value, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", FIXTURES / "strict-node-esm"], env=env)
        self.assertNotIn("BBK_TEST_SUPER_SECRET_TOKEN", value["environment"])
        self.assertTrue(all(not item.get("redacted") or "sha256" not in item for item in value["environment"].values()))

    def test_static_preflight_detects_strict_node_toolchain(self):
        value, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", FIXTURES / "strict-node-esm"])
        self.assertEqual(value["schema"], "bbk.tsjs-preflight.v1")
        self.assertEqual(value["workspace"]["members"], ["fixture-strict-node-esm"])
        self.assertEqual(value["language"]["project_modes"], ["typescript-strict"])
        self.assertEqual(value["runtime"]["targets"], ["node"])
        package = value["packages"][0]
        self.assertEqual(package["module"]["declared"], "esm")
        self.assertEqual(package["module"]["typescript_module_resolution"], "NodeNext")
        self.assertEqual(package["language"]["exact_optional_property_types"], True)
        self.assertIn("^6.0.0", value["toolchain"]["declared_typescript_specs"])
        self.assertRegex(value["digest"], r"^[0-9a-f]{64}$")

    def test_checked_javascript_and_transpile_only_are_distinct(self):
        checked, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", FIXTURES / "checked-javascript"])
        transpile, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", FIXTURES / "transpile-only-typescript"])
        self.assertEqual(checked["language"]["project_modes"], ["javascript-checked"])
        self.assertEqual(checked["packages"][0]["language"]["semantic_check_signal"], True)
        self.assertEqual(transpile["language"]["project_modes"], ["typescript-transpile-only"])
        self.assertEqual(transpile["packages"][0]["language"]["semantic_check_signal"], False)
        resolved, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "transpile-only-typescript",
            "--role", "worker", "--task-profile", "implementation", "--assurance-tier", "routine",
        ])
        self.assertNotIn("tsjs-typecheck-affected", gate_ids(resolved))
        self.assertIn("tsjs-focused-tests", gate_ids(resolved))

    def test_mixed_monorepo_preserves_per_package_language_and_runtime(self):
        value, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", FIXTURES / "mixed-monorepo"])
        self.assertEqual(value["package_manager"]["name"], "pnpm")
        self.assertEqual(value["workspace"]["members"], ["fixture-mixed-monorepo", "@fixture/core", "@fixture/legacy", "@fixture/web"])
        self.assertEqual(value["language"]["project_modes"], ["javascript-unchecked", "typescript-strict"])
        by_name = {item["name"]: item for item in value["packages"]}
        self.assertEqual(by_name["@fixture/core"]["module"]["declared"], "esm")
        self.assertEqual(by_name["@fixture/legacy"]["module"]["declared"], "commonjs")
        self.assertEqual(by_name["@fixture/legacy"]["language"]["primary"], "javascript-unchecked")
        self.assertIn("browser", value["runtime"]["targets"])
        self.assertIn("browser-application-or-library", by_name["@fixture/web"]["package_kinds"])

    def test_routine_worker_is_minimal_and_does_not_execute_package_manager(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "npm-executed"
            fakebin = Path(temp) / "bin"
            fakebin.mkdir()
            fake = fakebin / ("npm.cmd" if os.name == "nt" else "npm")
            if os.name == "nt":
                fake.write_text(f"@echo touched>{marker}\r\n", encoding="utf-8")
            else:
                fake.write_text(f"#!/bin/sh\ntouch {marker!s}\nexit 91\n", encoding="utf-8")
                fake.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(fakebin) + os.pathsep + env.get("PATH", "")
            value, _ = run_json([
                sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "strict-node-esm",
                "--role", "worker", "--task-profile", "implementation", "--assurance-tier", "routine",
                "--path", "src/index.ts",
            ], env=env)
            self.assertFalse(marker.exists())
            self.assertEqual(selected_ids(value), ["bbk-tsjs", "tsjs-development-practices"])
            self.assertEqual(value["recommended_validator_packs"], [])
            self.assertEqual(gate_ids(value), ["tsjs-lint-affected", "tsjs-typecheck-affected", "tsjs-focused-tests"])
            self.assertTrue(all(item["execution"] == "planned-only" for item in value["gate_plan"]["selected"]))

    def test_public_package_validator_selects_contract_and_consumer_assurance(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "public-esm-package",
            "--role", "validator", "--task-profile", "interface-schema-migration",
            "--assurance-tier", "consequential", "--change-class", "interface", "--change-class", "schema",
            "--hint", "public-api", "--hint", "package-exports", "--path", "src/index.ts",
        ])
        selected = set(selected_ids(value))
        self.assertTrue({"tsjs-type-contract-review", "tsjs-runtime-data-contract-review", "tsjs-api-module-package-review"}.issubset(selected))
        self.assertNotIn("comprehensive-analysis-tsjs", selected)
        gates = set(gate_ids(value))
        self.assertTrue({"tsjs-declaration-emit", "tsjs-pack-dry-run", "tsjs-packed-consumer-matrix", "tsjs-module-condition-matrix", "tsjs-runtime-contract-fixtures"}.issubset(gates))
        self.assertNotIn("tsjs-host-load", gates)

    def test_async_runtime_contract_selects_focused_failure_review(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "strict-node-esm",
            "--role", "validator", "--task-profile", "integration-consumer-path",
            "--assurance-tier", "consequential", "--change-class", "integration",
            "--hint", "async", "--hint", "cancellation", "--hint", "runtime-validation",
            "--path", "src/index.ts",
        ])
        selected = set(selected_ids(value))
        self.assertIn("tsjs-async-resource-failure-review", selected)
        self.assertIn("tsjs-runtime-data-contract-review", selected)
        gates = set(gate_ids(value))
        self.assertIn("tsjs-async-resource-faults", gates)
        self.assertIn("tsjs-runtime-contract-fixtures", gates)

    def test_browser_fixture_selects_browser_review_and_real_browser_gates(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "browser-application",
            "--role", "validator", "--task-profile", "integration-consumer-path",
            "--assurance-tier", "consequential", "--change-class", "ui", "--hint", "browser",
            "--path", "src/App.tsx",
        ])
        selected = set(selected_ids(value))
        self.assertIn("tsjs-browser-ui-review", selected)
        gates = set(gate_ids(value))
        self.assertIn("tsjs-real-browser", gates)
        self.assertIn("tsjs-accessibility", gates)


    def test_dual_package_detects_conditional_exports_and_consumer_matrix(self):
        preflight, _ = run_json([sys.executable, CLI, "--json", "preflight", "--root", FIXTURES / "dual-package"])
        package = preflight["packages"][0]
        self.assertEqual(package["module"]["declared"], "dual")
        self.assertEqual(package["module"]["conditions"], ["import", "require", "types"])
        self.assertIn("dual-package", package["package_kinds"])
        resolved, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "dual-package",
            "--role", "validator", "--task-profile", "packaging-release",
            "--assurance-tier", "consequential", "--hint", "dual-package", "--path", "package.json",
        ])
        self.assertIn("tsjs-api-module-package-review", selected_ids(resolved))
        self.assertIn("tsjs-packed-consumer-matrix", gate_ids(resolved))
        self.assertIn("tsjs-module-condition-matrix", gate_ids(resolved))

    def test_omp_extension_selects_host_specific_assurance(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "omp-extension",
            "--role", "validator", "--task-profile", "integration-consumer-path",
            "--assurance-tier", "consequential", "--change-class", "host-integration",
            "--hint", "omp-extension", "--path", "src/index.ts",
        ])
        selected = set(selected_ids(value))
        self.assertTrue({"tsjs-operational-release-review", "tsjs-security-supply-chain-review", "tsjs-evidence-reproducer"}.issubset(selected))
        gates = set(gate_ids(value))
        self.assertIn("tsjs-host-load", gates)
        self.assertIn("tsjs-security-policy", gates)

    def test_broad_survey_does_not_fan_out_focused_reviewers(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "mixed-monorepo",
            "--role", "reviewer", "--task-profile", "investigation-prototype",
            "--assurance-tier", "material", "--hint", "broad-analysis",
        ])
        self.assertEqual(set(selected_ids(value)), {"bbk-tsjs", "comprehensive-analysis-tsjs"})

    def test_test_strategy_selects_evidence_without_running_tests(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "strict-node-esm",
            "--role", "verification-designer", "--task-profile", "test-fixture",
            "--assurance-tier", "consequential", "--change-class", "test",
            "--hint", "property-test", "--hint", "mutation-testing", "--path", "test/index.test.ts",
        ])
        selected = set(selected_ids(value))
        self.assertIn("tsjs-test-strategy-review", selected)
        self.assertIn("tsjs-evidence-reproducer", selected)
        gates = set(gate_ids(value))
        self.assertIn("tsjs-property-fuzz", gates)
        self.assertIn("tsjs-mutation-testing", gates)

    def test_effective_digest_is_deterministic_and_scope_sensitive(self):
        base = [
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "strict-node-esm",
            "--role", "worker", "--task-profile", "implementation", "--assurance-tier", "routine",
        ]
        left, _ = run_json([*base, "--path", "src/index.ts"])
        right, _ = run_json([*base, "--path", "src/index.ts"])
        changed, _ = run_json([*base, "--path", "test/index.test.ts"])
        self.assertEqual(left["effective_sha256"], right["effective_sha256"])
        self.assertNotEqual(left["effective_sha256"], changed["effective_sha256"])
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
                console.log(JSON.stringify({{tools: tools.map(x => x.name), commands: commands.map(x => x[0])}}));
            """), encoding="utf-8")
            value = json.loads(run(["node", script]).stdout)
            self.assertIn("bbk_tsjs_resolve", value["tools"])
            self.assertIn("bbk_tsjs_structure_review", value["tools"])
            self.assertIn("bbk:tsjs:gates", value["commands"])
            self.assertIn("bbk:tsjs:structure", value["commands"])

    @unittest.skipUnless(shutil.which("node"), "node is required for installed OMP extension qualification")
    def test_installed_omp_extension_executes_profile_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            home = base / "home"
            home.mkdir()
            env = os.environ.copy()
            env.update({"HOME": str(home), "BBK_INSTALL_ROOT": str(base / "data"), "BBK_BIN_DIR": str(base / "bin")})
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "user", "--omp"], env=env)
            self.assertTrue(installed["omp"])
            extension = home / ".omp" / "agent" / "extensions" / "bbk-profile-typescript-javascript" / "index.js"
            script = base / "installed-tsjs-omp-mock.mjs"
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
                const tool = tools.find(value => value.name === 'bbk_tsjs_preflight');
                if (!tool) throw new Error('missing bbk_tsjs_preflight');
                const result = await tool.execute('call-1', {{root: {json.dumps(str(FIXTURES / 'strict-node-esm'))}, runTools: false}}, undefined, undefined, {{cwd: {json.dumps(str(FIXTURES / 'strict-node-esm'))}}});
                if (result.isError || result.details?.schema !== 'bbk.tsjs-preflight.v1') throw new Error(JSON.stringify(result.details));
                console.log(JSON.stringify({{schema: result.details.schema, tools: tools.length}}));
            """), encoding="utf-8")
            value = json.loads(run(["node", script], env=env).stdout)
            self.assertEqual(value["schema"], "bbk.tsjs-preflight.v1")
            run([sys.executable, INSTALL, "uninstall", "--scope", "user"], env=env)
            self.assertTrue(home.exists())

    def test_user_install_and_uninstall_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            home.mkdir()
            env = os.environ.copy()
            env.update({"HOME": str(home), "BBK_INSTALL_ROOT": str(home / "data"), "BBK_BIN_DIR": str(home / "bin")})
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "user"], env=env)
            self.assertTrue(installed["codex"] and installed["omp"] and installed["claude"])
            self.assertEqual(len(list((home / ".agents" / "skills").glob("*/SKILL.md"))), 13)
            self.assertEqual(len(list((home / ".claude" / "skills").glob("*/SKILL.md"))), 13)
            self.assertTrue((home / ".omp" / "agent" / "extensions" / "bbk-profile-typescript-javascript" / "index.js").is_file())
            self.assertTrue((home / "bin" / ("bbk-tsjs.cmd" if os.name == "nt" else "bbk-tsjs")).is_file())
            current = json.loads((home / "data" / "profiles" / "typescript-javascript" / "current.json").read_text(encoding="utf-8"))
            self.assertEqual(current["version"], "0.1.0-alpha.3")
            status, _ = run_json([sys.executable, INSTALL, "--json", "status", "--scope", "user"], env=env)
            self.assertEqual(status["summary"].get("current"), len(status["files"]))
            run([sys.executable, INSTALL, "uninstall", "--scope", "user"], env=env)
            self.assertTrue(home.exists())
            self.assertFalse((home / "data" / "profile-install-manifests" / "typescript-javascript.json").exists())

    def test_project_install_roundtrip_preserves_project_root(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            project.mkdir()
            installed, _ = run_json([sys.executable, INSTALL, "--json", "install", "--scope", "project", "--root", project, "--omp"])
            self.assertFalse(installed["codex"])
            self.assertTrue(installed["omp"])
            self.assertFalse(installed["claude"])
            self.assertTrue((project / ".bbk-kit" / "profiles" / "typescript-javascript" / "0.1.0-alpha.3" / "PROFILE.json").is_file())
            self.assertTrue((project / ".omp" / "extensions" / "bbk-profile-typescript-javascript" / "index.js").is_file())
            run([sys.executable, INSTALL, "uninstall", "--scope", "project", "--root", project])
            self.assertTrue(project.exists())
            self.assertFalse((project / ".bbk-profile-typescript-javascript-install.json").exists())

    @unittest.skipUnless(BBK_CORE_ROOT and (BBK_CORE_ROOT / "tools" / "bbk.py").is_file(), "BBK alpha.3 core reference not configured")
    def test_bbk_alpha3_core_rejects_alpha4_profile_explicitly(self):
        bbk = BBK_CORE_ROOT / "tools" / "bbk.py"  # type: ignore[operator]
        command = [
            sys.executable, bbk, "--json", "profile", "resolve",
            "--profile-dir", ROOT, "--id", "typescript-javascript",
            "--source", FIXTURES / "strict-node-esm", "--role", "worker",
            "--task-profile", "implementation", "--assurance-tier", "routine",
        ]
        # Source-tree tests may run after edits and before the successor package
        # manifest is frozen. Clean-extraction qualification separately proves
        # verified profile discovery without this development-only bypass.
        command.append("--allow-unverified")
        value, result = run_json(command, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(value["status"], "ERROR")
        self.assertIn("bbk_minimum", value["error"])
        self.assertIn("0.1.0-alpha.4", value["error"])


    def test_alpha4_profile_and_output_schemas(self):
        from jsonschema import Draft202012Validator
        profile = json.loads((ROOT / "PROFILE.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "schemas" / "bbk-language-profile-v1.schema.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema).iter_errors(profile))
        self.assertEqual(errors, [], [error.message for error in errors])
        required = {
            "bbk-tsjs-implementation-structure-projection-v1.schema.json",
            "bbk-tsjs-execution-slice-projection-v1.schema.json",
            "bbk-tsjs-structure-review-result-v1.schema.json",
            "bbk-tsjs-planned-actual-structure-comparison-v1.schema.json",
        }
        self.assertTrue(required <= {path.name for path in (ROOT / "schemas").glob("*.json")})

    def test_alpha4_generic_positive_and_negative_fixtures(self):
        from jsonschema import Draft202012Validator
        contract_schema = json.loads((ROOT / "schemas" / "bbk-implementation-structure-contract-v1.schema.json").read_text(encoding="utf-8"))
        slice_schema = json.loads((ROOT / "schemas" / "bbk-execution-slice-v1.schema.json").read_text(encoding="utf-8"))
        contract_validator = Draft202012Validator(contract_schema)
        slice_validator = Draft202012Validator(slice_schema)
        for path in sorted((FIXTURES / "alpha4" / "structure").glob("*.json")):
            errors = list(contract_validator.iter_errors(json.loads(path.read_text(encoding="utf-8"))))
            if path.name == "invalid-contract.json":
                self.assertTrue(errors)
            else:
                self.assertEqual(errors, [], (path, [error.message for error in errors]))
        for path in sorted((FIXTURES / "alpha4" / "slices").glob("*.json")):
            errors = list(slice_validator.iter_errors(json.loads(path.read_text(encoding="utf-8"))))
            if path.name == "invalid-slice.json":
                self.assertTrue(errors)
            else:
                self.assertEqual(errors, [], (path, [error.message for error in errors]))

    def test_structure_projection_is_deterministic_and_schema_valid(self):
        from jsonschema import Draft202012Validator
        command = [
            sys.executable, CLI, "--json", "structure",
            "--root", FIXTURES / "public-esm-package",
            "--contract", FIXTURES / "alpha4" / "structure" / "public-esm-package.json",
        ]
        left, _ = run_json(command)
        right, _ = run_json(command)
        self.assertEqual(left, right)
        self.assertEqual(left["applicability"]["disposition"], "SUPPORTED")
        self.assertEqual(left["profile"]["version"], "0.1.0-alpha.3")
        self.assertTrue(any(item["tsjs_kind"] == "package-manifest" for item in left["projection"]["artifact_topology"]))
        self.assertTrue(any(item["consumer_evidence_required"] for item in left["projection"]["key_contracts"]))
        self.assertFalse(left["authority"]["projection_is_authority"])
        check = dict(left)
        output_digest = check.pop("output_digest")
        self.assertEqual(output_digest, hashlib.sha256(json.dumps(check, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest())
        schema = json.loads((ROOT / "schemas" / "bbk-tsjs-implementation-structure-projection-v1.schema.json").read_text())
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(left)), [])

    def test_non_tsjs_subject_returns_partial_projection(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure",
            "--root", FIXTURES / "strict-node-esm",
            "--contract", FIXTURES / "alpha4" / "generic-kit" / "procedure-contract.json",
        ])
        self.assertEqual(value["applicability"]["disposition"], "PARTIAL")
        self.assertTrue(value["unsupported_or_uncertain"])
        self.assertFalse(value["authority"]["may_expand_work_scope"])

    def test_invalid_contract_and_slice_are_blocked(self):
        contract, _ = run_json([
            sys.executable, CLI, "--json", "structure", "--root", FIXTURES / "strict-node-esm",
            "--contract", FIXTURES / "alpha4" / "structure" / "invalid-contract.json",
        ])
        slice_value, _ = run_json([
            sys.executable, CLI, "--json", "slice", "--root", FIXTURES / "strict-node-esm",
            "--slice", FIXTURES / "alpha4" / "slices" / "invalid-slice.json",
        ])
        self.assertEqual(contract["applicability"]["disposition"], "BLOCKED")
        self.assertTrue(contract["blockers"])
        self.assertEqual(slice_value["applicability"]["disposition"], "BLOCKED")
        self.assertTrue(slice_value["blockers"])

    def test_execution_slice_projection_and_foundation_exception(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "slice", "--root", FIXTURES / "public-esm-package",
            "--slice", FIXTURES / "alpha4" / "slices" / "foundation-exception.json",
        ])
        self.assertEqual(value["projection"]["sequencing_assessment"]["classification"], "FOUNDATION_EXCEPTION")
        self.assertEqual(value["projection"]["sequencing_assessment"]["next_integrated_slice_ref"], "ES-TSJS-PUBLIC-ESM")
        self.assertIn("tsjs-implementation-structure-review", value["projection"]["validation_boundary"]["focused_review_packs"])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "slice.json"
            raw = json.loads((FIXTURES / "alpha4" / "slices" / "foundation-exception.json").read_text())
            raw["metadata"] = {"fixture": True}
            path.write_text(json.dumps(raw), encoding="utf-8")
            risky, _ = run_json([sys.executable, CLI, "--json", "slice", "--root", FIXTURES / "public-esm-package", "--slice", path])
            self.assertEqual(risky["projection"]["sequencing_assessment"]["classification"], "HORIZONTAL_RISK")
            self.assertTrue(risky["advisories"])

    def test_resolver_binds_contract_slice_and_projection_digests(self):
        command = [
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "public-esm-package",
            "--role", "worker", "--assurance-tier", "material",
            "--structure-contract", FIXTURES / "alpha4" / "structure" / "public-esm-package.json",
            "--execution-slice", FIXTURES / "alpha4" / "slices" / "public-esm-package.json",
        ]
        left, _ = run_json(command)
        right, _ = run_json(command)
        self.assertEqual(left["effective_sha256"], right["effective_sha256"])
        self.assertEqual(left["inputs"]["task_profile"], "implementation-structure")
        self.assertNotIn("tsjs-implementation-structure-review", selected_ids(left))
        self.assertIn("tsjs-implementation-structure-review", [item["id"] for item in left["recommended_validator_packs"]])
        support = left["implementation_structure"]
        self.assertRegex(support["contract_digest"], r"^[0-9a-f]{64}$")
        self.assertRegex(support["slice_projection_digest"], r"^[0-9a-f]{64}$")
        locked = left["lock"]["profiles"][0]["implementation_structure"]
        self.assertEqual(locked["contract_digest"], support["contract_digest"])
        self.assertEqual(locked["slice_projection_digest"], support["slice_projection_digest"])
        gates = set(gate_ids(left))
        self.assertIn("tsjs-structure-contract-validation", gates)
        self.assertIn("tsjs-slice-touchpoint-evidence", gates)

    def test_structure_reviewer_is_focused_not_full_fanout(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "resolve", "--root", FIXTURES / "public-esm-package",
            "--role", "reviewer", "--task-profile", "implementation-structure", "--assurance-tier", "material",
            "--structure-contract", FIXTURES / "alpha4" / "structure" / "public-esm-package.json",
        ])
        selected = set(selected_ids(value))
        self.assertIn("tsjs-implementation-structure-review", selected)
        self.assertNotIn("tsjs-browser-ui-review", selected)
        self.assertNotIn("tsjs-security-supply-chain-review", selected)
        self.assertNotIn("tsjs-operational-release-review", selected)

    def test_planned_actual_harmless_private_divergence_conforms(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURES / "public-esm-package",
            "--contract", FIXTURES / "alpha4" / "structure" / "public-esm-package.json",
            "--candidate", FIXTURES / "alpha4" / "candidates" / "public-esm-candidate.json",
            "--actual-inventory", FIXTURES / "alpha4" / "actual-inventory" / "public-esm-harmless-private.json",
        ])
        self.assertEqual(value["disposition"], "CONFORMS")
        self.assertEqual(value["comparison"]["summary"]["material"], 0)
        self.assertEqual(value["comparison"]["summary"]["delegated"], 1)

    def test_planned_actual_fixed_export_divergence_is_material(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURES / "public-esm-package",
            "--contract", FIXTURES / "alpha4" / "structure" / "public-esm-package.json",
            "--candidate", FIXTURES / "alpha4" / "candidates" / "public-esm-candidate.json",
            "--actual-inventory", FIXTURES / "alpha4" / "actual-inventory" / "public-esm-material-drift.json",
        ])
        self.assertEqual(value["disposition"], "MATERIAL_DIVERGENCE")
        refs = {item["affected_reference"] for item in value["findings"]}
        self.assertIn("KC-EXPORTS", refs)
        self.assertIn("FD-ESM-EXPORTS", refs)
        self.assertFalse(value["authority"]["may_declare_pass"])

    def test_structure_review_without_semantic_inventory_blocks_instead_of_guessing(self):
        value, _ = run_json([
            sys.executable, CLI, "--json", "structure-review", "--root", FIXTURES / "public-esm-package",
            "--contract", FIXTURES / "alpha4" / "structure" / "public-esm-package.json",
            "--candidate", FIXTURES / "alpha4" / "candidates" / "public-esm-candidate.json",
        ])
        self.assertEqual(value["disposition"], "BLOCKED")
        self.assertTrue(value["blockers"])

    def test_all_required_tsjs_structure_fixture_families_exist(self):
        expected = {
            "strict-typescript-library", "checked-javascript", "transpile-only-typescript",
            "public-esm-package", "dual-package", "browser-runtime-data",
            "async-abort-resource", "omp-extension",
        }
        structure = {path.stem for path in (FIXTURES / "alpha4" / "structure").glob("*.json") if not path.name.startswith("invalid")}
        slices = {path.stem for path in (FIXTURES / "alpha4" / "slices").glob("*.json") if path.stem not in {"invalid-slice", "foundation-exception"}}
        self.assertTrue(expected <= structure)
        self.assertTrue(expected <= slices)
        self.assertTrue((FIXTURES / "alpha4" / "actual-inventory" / "public-esm-material-drift.json").is_file())

    def test_alpha3_profile_classifies_as_legacy_unprojected(self):
        legacy = json.loads((FIXTURES / "alpha4" / "legacy" / "alpha3-profile.json").read_text())
        capability = legacy.get("capabilities", {}).get("implementation_structure")
        status = capability.get("status") if isinstance(capability, dict) else "legacy-unprojected"
        self.assertEqual(status, "legacy-unprojected")
        self.assertIn("resolve", legacy["entrypoints"])

    @unittest.skipUnless(shutil.which("node"), "node is required for installed structure tool qualification")
    def test_installed_omp_structure_tool_invokes_packaged_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            home = base / "home"
            home.mkdir()
            env = os.environ.copy()
            env.update({"HOME": str(home), "BBK_INSTALL_ROOT": str(base / "data"), "BBK_BIN_DIR": str(base / "bin")})
            run([sys.executable, INSTALL, "install", "--scope", "user", "--omp"], env=env)
            extension = home / ".omp" / "agent" / "extensions" / "bbk-profile-typescript-javascript" / "index.js"
            script = base / "structure-tool.mjs"
            script.write_text(textwrap.dedent(f"""
                const chain = () => ({{ optional() {{ return this; }} }});
                const z = {{ object: value => value, string: chain, boolean: chain,
                  enum: values => chain(), array: value => chain() }};
                const tools = [];
                const pi = {{ zod: {{ z }}, setLabel() {{}}, registerTool(value) {{ tools.push(value); }},
                  registerCommand() {{}}, on() {{}}, sendMessage() {{}} }};
                const mod = await import({json.dumps(extension.as_uri())});
                mod.default(pi);
                const tool = tools.find(value => value.name === 'bbk_tsjs_structure');
                if (!tool) throw new Error('missing structure tool');
                const result = await tool.execute('call', {{
                  root: {json.dumps(str(FIXTURES / 'public-esm-package'))},
                  contract: {json.dumps(str(FIXTURES / 'alpha4' / 'structure' / 'public-esm-package.json'))}
                }}, undefined, undefined, {{cwd: {json.dumps(str(FIXTURES / 'public-esm-package'))}}});
                if (result.isError || result.details?.schema !== 'bbk.tsjs-implementation-structure-projection.v1') throw new Error(JSON.stringify(result.details));
                console.log(JSON.stringify({{schema: result.details.schema, disposition: result.details.applicability.disposition}}));
            """), encoding="utf-8")
            value = json.loads(run(["node", script], env=env).stdout)
            self.assertEqual(value["schema"], "bbk.tsjs-implementation-structure-projection.v1")
            self.assertEqual(value["disposition"], "SUPPORTED")
            run([sys.executable, INSTALL, "uninstall", "--scope", "user"], env=env)


if __name__ == "__main__":
    unittest.main()
