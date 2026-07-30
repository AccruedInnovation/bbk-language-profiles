import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const PROFILE_ID = "typescript-javascript";
const VERSION = "0.1.0-alpha.3";

function userDataRoot() {
  if (process.env.BBK_INSTALL_ROOT) return path.resolve(process.env.BBK_INSTALL_ROOT);
  if (process.platform === "win32") return path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"), "BBK");
  if (process.platform === "darwin") return path.join(os.homedir(), "Library", "Application Support", "BBK");
  return path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), ".local", "share"), "bbk");
}

function readCurrent(currentPath) {
  try {
    const value = JSON.parse(fs.readFileSync(currentPath, "utf8"));
    if (value?.id === PROFILE_ID && typeof value.path === "string") return value.path;
  } catch {
    // Continue through the deterministic search order.
  }
  return null;
}

function ancestors(cwd) {
  const values = [];
  let current = path.resolve(cwd);
  while (true) {
    values.push(current);
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return values;
}

function profileRoot(cwd) {
  if (process.env.BBK_PROFILE_TSJS_ROOT) return path.resolve(process.env.BBK_PROFILE_TSJS_ROOT);
  for (const root of ancestors(cwd)) {
    for (const current of [
      path.join(root, ".bbk", "profiles", PROFILE_ID, "current.json"),
      path.join(root, ".bbk-kit", "profiles", PROFILE_ID, "current.json"),
    ]) {
      const value = readCurrent(current);
      if (value) return value;
    }
  }
  return readCurrent(path.join(userDataRoot(), "profiles", PROFILE_ID, "current.json"));
}

function pythonCommand(script) {
  const python = process.env.BBK_PYTHON || (process.platform === "win32" ? "py" : "python3");
  return { executable: python, prefix: process.platform === "win32" && !process.env.BBK_PYTHON ? ["-3", script] : [script] };
}

function explicitCommand(value) {
  if (String(value).toLowerCase().endsWith(".py")) return pythonCommand(path.resolve(value));
  return { executable: value, prefix: [] };
}

function command(cwd) {
  if (process.env.BBK_TSJS_CLI) return explicitCommand(process.env.BBK_TSJS_CLI);
  const root = profileRoot(cwd);
  if (root) {
    const script = path.join(root, "tools", "bbk_tsjs.py");
    if (fs.existsSync(script)) {
      const python = process.env.BBK_PYTHON || (process.platform === "win32" ? "py" : "python3");
      return { executable: python, prefix: process.platform === "win32" && !process.env.BBK_PYTHON ? ["-3", script] : [script] };
    }
  }
  return { executable: process.platform === "win32" ? "bbk-tsjs.cmd" : "bbk-tsjs", prefix: [] };
}

function runTsjs(args, cwd, signal) {
  return new Promise((resolve, reject) => {
    const selected = command(cwd);
    const child = spawn(selected.executable, [...selected.prefix, "--json", ...args], {
      cwd,
      env: process.env,
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", chunk => { stdout += chunk; });
    child.stderr.on("data", chunk => { stderr += chunk; });
    const abort = () => child.kill("SIGTERM");
    signal?.addEventListener?.("abort", abort, { once: true });
    child.on("error", reject);
    child.on("close", code => {
      signal?.removeEventListener?.("abort", abort);
      let details;
      try {
        details = stdout.trim() ? JSON.parse(stdout) : { status: code === 0 ? "PASS" : "ERROR" };
      } catch {
        details = { status: "ERROR", stdout, stderr, parseError: "bbk-tsjs did not return JSON" };
      }
      if (stderr.trim()) details.stderr = stderr;
      resolve({ code, details });
    });
  });
}

function toolResult(value) {
  return {
    content: [{ type: "text", text: JSON.stringify(value.details, null, 2) }],
    details: value.details,
    isError: value.code !== 0,
  };
}

function commonArgs(params) {
  return [
    ...(params.root ? ["--root", params.root] : []),
    ...(params.role ? ["--role", params.role] : []),
    ...(params.taskProfile ? ["--task-profile", params.taskProfile] : []),
    ...(params.assuranceTier ? ["--assurance-tier", params.assuranceTier] : []),
    ...(params.hints || []).flatMap(value => ["--hint", value]),
    ...(params.changeClasses || []).flatMap(value => ["--change-class", value]),
    ...(params.paths || []).flatMap(value => ["--path", value]),
    ...(params.runTools ? ["--run-tools"] : []),
  ];
}

function registerTool(pi, definition) {
  pi.registerTool({
    name: definition.name,
    label: definition.label,
    description: definition.description,
    parameters: definition.parameters,
    async execute(_id, params, signal, _onUpdate, ctx) {
      return toolResult(await runTsjs(definition.argv(params), ctx.cwd, signal));
    },
  });
}

// Slash commands report through ctx.ui.notify only. Structured JSON is
// returned only by LLM-callable tools, where model-facing content is intended.


function profileCapabilityCommand(cwd) {
  if (process.env.BBK_TSJS_PROFILE_DISPATCH_CLI) return explicitCommand(process.env.BBK_TSJS_PROFILE_DISPATCH_CLI);
  const root = profileRoot(cwd);
  if (root) {
    const script = path.join(root, "tools", "profile.py");
    if (fs.existsSync(script)) {
      const python = process.env.BBK_PYTHON || (process.platform === "win32" ? "py" : "python3");
      return { executable: python, prefix: process.platform === "win32" && !process.env.BBK_PYTHON ? ["-3", script] : [script] };
    }
  }
  return { executable: process.platform === "win32" ? "py" : "python3", prefix: [path.join(path.dirname(new URL(import.meta.url).pathname), "..", "..", "tools", "profile.py")] };
}

function runProfileCapability(operation, request, cwd, signal) {
  return new Promise((resolve, reject) => {
    const selected = profileCapabilityCommand(cwd);
    const child = spawn(selected.executable, [...selected.prefix, "--json", operation, "--request", request], { cwd, env: process.env, windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8"); child.stderr.setEncoding("utf8");
    child.stdout.on("data", chunk => { stdout += chunk; }); child.stderr.on("data", chunk => { stderr += chunk; });
    const abort = () => child.kill("SIGTERM"); signal?.addEventListener?.("abort", abort, { once: true });
    child.on("error", reject);
    child.on("close", code => {
      signal?.removeEventListener?.("abort", abort);
      let details;
      try { details = stdout.trim() ? JSON.parse(stdout) : { schema: "bbk.profile-capability-result.v1", status: "ERROR", payload: { error: { message: "empty profile dispatch output" } } }; }
      catch { details = { schema: "bbk.profile-capability-result.v1", status: "ERROR", payload: { error: { message: "invalid profile dispatch JSON", stdout, stderr } } }; }
      resolve({ code, details });
    });
  });
}

export default function bbkTsjsExtension(pi) {
  const { z } = pi.zod;
  pi.setLabel("BBK TypeScript/JavaScript Profile");
  const parameters = z.object({
    root: z.string().optional(),
    role: z.string().optional(),
    taskProfile: z.string().optional(),
    assuranceTier: z.enum(["routine", "material", "consequential", "critical"]).optional(),
    hints: z.array(z.string()).optional(),
    changeClasses: z.array(z.string()).optional(),
    paths: z.array(z.string()).optional(),
    runTools: z.boolean().optional(),
  });

  pi.registerTool({
    name: "bbk_tsjs_state_effect",
    label: "BBK TypeScript/JavaScript State–Decision–Effect Projection",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation state-effect against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("state-effect", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_tsjs_state_effect_inventory",
    label: "BBK TypeScript/JavaScript State–Decision–Effect Inventory",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation state-effect-inventory against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("state-effect-inventory", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_tsjs_state_effect_review",
    label: "BBK TypeScript/JavaScript State–Decision–Effect Review",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation state-effect-review against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("state-effect-review", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_tsjs_review_context",
    label: "BBK TypeScript/JavaScript Review Context",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation review-context against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("review-context", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_tsjs_review_lens",
    label: "BBK TypeScript/JavaScript Review Lens",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation review-lens against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("review-lens", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_tsjs_evidence_adapter",
    label: "BBK TypeScript/JavaScript Evidence Adapter",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation evidence-adapter against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("evidence-adapter", params.request, ctx.cwd, signal)); },
  });

  registerTool(pi, {
    name: "bbk_tsjs_preflight",
    label: "BBK TS/JS Preflight",
    description: "Inspect the effective package/workspace, language modes, runtimes, package manager, module contract, build/test stack, and repository commands without installing or running project gates.",
    parameters: z.object({ root: z.string().optional(), runTools: z.boolean().optional() }),
    argv: p => ["preflight", ...(p.root ? ["--root", p.root] : []), ...(p.runTools ? ["--run-tools"] : [])],
  });
  registerTool(pi, {
    name: "bbk_tsjs_structure",
    label: "BBK TS/JS Structure Projection",
    description: "Project an accepted generic ImplementationStructureContract into TypeScript/JavaScript package, module, export, declaration, runtime-schema, ownership, effect, and review vocabulary without mutating the repository.",
    parameters: z.object({
      root: z.string().optional(),
      contract: z.string(),
      role: z.string().optional(),
      taskProfile: z.string().optional(),
      assuranceTier: z.enum(["routine", "material", "consequential", "critical"]).optional(),
      runTools: z.boolean().optional(),
    }),
    argv: p => [
      "structure", "--contract", p.contract,
      ...(p.root ? ["--root", p.root] : []),
      ...(p.role ? ["--role", p.role] : []),
      ...(p.taskProfile ? ["--task-profile", p.taskProfile] : []),
      ...(p.assuranceTier ? ["--assurance-tier", p.assuranceTier] : []),
      ...(p.runTools ? ["--run-tools"] : []),
    ],
  });
  registerTool(pi, {
    name: "bbk_tsjs_slice",
    label: "BBK TS/JS Execution Slice Projection",
    description: "Project a generic ExecutionSlice into TypeScript/JavaScript touchpoint, dependency, evidence, candidate, validation, sequencing, and scaffolding guidance without executing the slice.",
    parameters: z.object({
      root: z.string().optional(),
      slice: z.string(),
      role: z.string().optional(),
      taskProfile: z.string().optional(),
      assuranceTier: z.enum(["routine", "material", "consequential", "critical"]).optional(),
      runTools: z.boolean().optional(),
    }),
    argv: p => [
      "slice", "--slice", p.slice,
      ...(p.root ? ["--root", p.root] : []),
      ...(p.role ? ["--role", p.role] : []),
      ...(p.taskProfile ? ["--task-profile", p.taskProfile] : []),
      ...(p.assuranceTier ? ["--assurance-tier", p.assuranceTier] : []),
      ...(p.runTools ? ["--run-tools"] : []),
    ],
  });
  registerTool(pi, {
    name: "bbk_tsjs_structure_review",
    label: "BBK TS/JS Structure Review",
    description: "Compare an exact candidate and optional actual inventory with the fixed consequential shape in an accepted ImplementationStructureContract while preserving delegated private freedom.",
    parameters: z.object({
      root: z.string().optional(),
      contract: z.string(),
      candidate: z.string(),
      actualInventory: z.string().optional(),
      assuranceTier: z.enum(["routine", "material", "consequential", "critical"]).optional(),
      runTools: z.boolean().optional(),
    }),
    argv: p => [
      "structure-review", "--contract", p.contract, "--candidate", p.candidate,
      ...(p.root ? ["--root", p.root] : []),
      ...(p.actualInventory ? ["--actual-inventory", p.actualInventory] : []),
      ...(p.assuranceTier ? ["--assurance-tier", p.assuranceTier] : []),
      ...(p.runTools ? ["--run-tools"] : []),
    ],
  });
  registerTool(pi, {
    name: "bbk_tsjs_resolve",
    label: "BBK TS/JS Resolve",
    description: "Resolve proportional TS/JS worker guidance, focused review packs, and planned gates from role, task, changed scope, runtime, and assurance tier.",
    parameters,
    argv: p => ["resolve", ...commonArgs(p)],
  });
  registerTool(pi, {
    name: "bbk_tsjs_gate_plan",
    label: "BBK TS/JS Gate Plan",
    description: "Compile a non-executing, repository-aware TS/JS gate plan. Installation, lifecycle scripts, browser runs, package publication, and other effects remain separately authorized.",
    parameters,
    argv: p => ["gate-plan", ...commonArgs(p)],
  });

  pi.registerCommand("bbk:tsjs:state-effect", {
    description: "Run state-effect; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:tsjs:state-effect <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("state-effect", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "State–Decision–Effect Projection failed" : "State–Decision–Effect Projection completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:tsjs:state-effect-inventory", {
    description: "Run state-effect-inventory; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:tsjs:state-effect-inventory <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("state-effect-inventory", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "State–Decision–Effect Inventory failed" : "State–Decision–Effect Inventory completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:tsjs:state-effect-review", {
    description: "Run state-effect-review; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:tsjs:state-effect-review <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("state-effect-review", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "State–Decision–Effect Review failed" : "State–Decision–Effect Review completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:tsjs:review-context", {
    description: "Run review-context; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:tsjs:review-context <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("review-context", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "Review Context failed" : "Review Context completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:tsjs:review-lens", {
    description: "Run review-lens; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:tsjs:review-lens <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("review-lens", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "Review Lens failed" : "Review Lens completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:tsjs:evidence-adapter", {
    description: "Run evidence-adapter; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:tsjs:evidence-adapter <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("evidence-adapter", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "Evidence Adapter failed" : "Evidence Adapter completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });

  pi.registerCommand("bbk:tsjs", {
    description: "Resolve the TypeScript/JavaScript profile for the current changed scope",
    handler: async (args, ctx) => {
      const hints = args?.trim() ? args.trim().split(/\s+/) : [];
      const value = await runTsjs(["resolve", ...hints.flatMap(hint => ["--hint", hint])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "TS/JS profile resolved" : "TS/JS profile resolution failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:tsjs:preflight", {
    description: "Inspect the current TS/JS project; add 'run-tools' to query installed version commands only",
    handler: async (args, ctx) => {
      const runTools = args?.trim() === "run-tools";
      const value = await runTsjs(["preflight", ...(runTools ? ["--run-tools"] : [])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "TS/JS preflight completed" : "TS/JS preflight failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:tsjs:gates", {
    description: "Compile a TS/JS gate plan; optional argument is the assurance tier",
    handler: async (args, ctx) => {
      const tier = args?.trim();
      const value = await runTsjs(["gate-plan", ...(tier ? ["--assurance-tier", tier] : [])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "TS/JS gate plan compiled" : "TS/JS gate planning failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:tsjs:structure", {
    description: "Project a generic structure contract; argument is the contract JSON path",
    handler: async (args, ctx) => {
      const contract = args?.trim();
      if (!contract) { ctx.ui.notify("Usage: /bbk:tsjs:structure <contract.json>", "warning"); return undefined; }
      const value = await runTsjs(["structure", "--contract", contract], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "TS/JS structure projected" : "TS/JS structure projection failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:tsjs:slice", {
    description: "Project a generic execution slice; argument is the slice JSON path",
    handler: async (args, ctx) => {
      const slice = args?.trim();
      if (!slice) { ctx.ui.notify("Usage: /bbk:tsjs:slice <slice.json>", "warning"); return undefined; }
      const value = await runTsjs(["slice", "--slice", slice], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "TS/JS slice projected" : "TS/JS slice projection failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:tsjs:structure-review", {
    description: "Review planned versus actual structure: <contract.json> <candidate.json> [actual-inventory.json]",
    handler: async (args, ctx) => {
      const values = args?.trim().split(/\s+/).filter(Boolean) || [];
      if (values.length < 2) { ctx.ui.notify("Usage: /bbk:tsjs:structure-review <contract.json> <candidate.json> [actual-inventory.json]", "warning"); return undefined; }
      const argv = ["structure-review", "--contract", values[0], "--candidate", values[1], ...(values[2] ? ["--actual-inventory", values[2]] : [])];
      const value = await runTsjs(argv, ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "TS/JS structure review completed" : "TS/JS structure review failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });

  pi.on("session_start", async (_event, ctx) => {
    const root = profileRoot(ctx.cwd);
    ctx.ui.notify(root ? `BBK TypeScript/JavaScript profile ${VERSION} loaded` : "BBK TS/JS profile extension loaded; profile package not found", root ? "info" : "warning");
  });
}
