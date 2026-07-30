import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

function userDataRoot() {
  if (process.env.BBK_INSTALL_ROOT) return path.resolve(process.env.BBK_INSTALL_ROOT);
  if (process.platform === "win32") return path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"), "BBK");
  if (process.platform === "darwin") return path.join(os.homedir(), "Library", "Application Support", "BBK");
  return path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), ".local", "share"), "bbk");
}

function readCurrent(currentPath) {
  try {
    const value = JSON.parse(fs.readFileSync(currentPath, "utf8"));
    if (value?.id === "python" && typeof value.path === "string") return value.path;
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
  if (process.env.BBK_PROFILE_PYTHON_ROOT) return path.resolve(process.env.BBK_PROFILE_PYTHON_ROOT);
  for (const root of ancestors(cwd)) {
    for (const current of [
      path.join(root, ".bbk", "profiles", "python", "current.json"),
      path.join(root, ".bbk-kit", "profiles", "python", "current.json"),
    ]) {
      const value = readCurrent(current);
      if (value) return value;
    }
  }
  return readCurrent(path.join(userDataRoot(), "profiles", "python", "current.json"));
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
  if (process.env.BBK_PYTHON_PROFILE_CLI) return explicitCommand(process.env.BBK_PYTHON_PROFILE_CLI);
  const root = profileRoot(cwd);
  if (root) {
    const script = path.join(root, "tools", "bbk_python.py");
    if (fs.existsSync(script)) {
      const python = process.env.BBK_PYTHON || (process.platform === "win32" ? "py" : "python3");
      return { executable: python, prefix: process.platform === "win32" && !process.env.BBK_PYTHON ? ["-3", script] : [script] };
    }
  }
  return { executable: process.platform === "win32" ? "bbk-python.cmd" : "bbk-python", prefix: [] };
}

function runPython(args, cwd, signal) {
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
        details = { status: "ERROR", stdout, stderr, parseError: "bbk-python did not return JSON" };
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
    ...(params.workUnit ? ["--work-unit", params.workUnit] : []),
    ...(params.structureContract ? ["--structure-contract", params.structureContract] : []),
    ...(params.executionSlice ? ["--execution-slice", params.executionSlice] : []),
  ];
}

function registerTool(pi, definition) {
  pi.registerTool({
    name: definition.name,
    label: definition.label,
    description: definition.description,
    parameters: definition.parameters,
    async execute(_id, params, signal, _onUpdate, ctx) {
      return toolResult(await runPython(definition.argv(params), ctx.cwd, signal));
    },
  });
}

// Slash commands report through ctx.ui.notify only. Structured JSON is
// returned only by LLM-callable tools, where model-facing content is intended.


function profileCapabilityCommand(cwd) {
  if (process.env.BBK_PYTHON_PROFILE_DISPATCH_CLI) return explicitCommand(process.env.BBK_PYTHON_PROFILE_DISPATCH_CLI);
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

export default function bbkPythonExtension(pi) {
  const { z } = pi.zod;
  pi.setLabel("BBK Python Profile");
  const parameters = z.object({
    root: z.string().optional(),
    role: z.string().optional(),
    taskProfile: z.string().optional(),
    assuranceTier: z.enum(["routine", "material", "consequential", "critical"]).optional(),
    hints: z.array(z.string()).optional(),
    changeClasses: z.array(z.string()).optional(),
    paths: z.array(z.string()).optional(),
    runTools: z.boolean().optional(),
    workUnit: z.string().optional(),
    structureContract: z.string().optional(),
    executionSlice: z.string().optional(),
  });

  pi.registerTool({
    name: "bbk_python_state_effect",
    label: "BBK Python State–Decision–Effect Projection",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation state-effect against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("state-effect", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_python_state_effect_inventory",
    label: "BBK Python State–Decision–Effect Inventory",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation state-effect-inventory against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("state-effect-inventory", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_python_state_effect_review",
    label: "BBK Python State–Decision–Effect Review",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation state-effect-review against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("state-effect-review", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_python_review_context",
    label: "BBK Python Review Context",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation review-context against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("review-context", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_python_review_lens",
    label: "BBK Python Review Lens",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation review-lens against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("review-lens", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_python_evidence_adapter",
    label: "BBK Python Evidence Adapter",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation evidence-adapter against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("evidence-adapter", params.request, ctx.cwd, signal)); },
  });

  registerTool(pi, {
    name: "bbk_python_preflight",
    label: "BBK Python Preflight",
    description: "Inspect Python packaging, interpreter, environment, support signals, and repository commands without granting or running project effects by default.",
    parameters: z.object({ root: z.string().optional(), runTools: z.boolean().optional() }),
    argv: p => ["preflight", ...(p.root ? ["--root", p.root] : []), ...(p.runTools ? ["--run-tools"] : [])],
  });
  registerTool(pi, {
    name: "bbk_python_resolve",
    label: "BBK Python Resolve",
    description: "Resolve proportional Python skills, focused review packs, and planned gates from the role, task, changed scope, and assurance tier.",
    parameters,
    argv: p => ["resolve", ...commonArgs(p)],
  });
  registerTool(pi, {
    name: "bbk_python_gate_plan",
    label: "BBK Python Gate Plan",
    description: "Compile a non-executing, repository-aware Python gate plan. Tool installation and effects remain separately authorized.",
    parameters,
    argv: p => ["gate-plan", ...commonArgs(p)],
  });
  registerTool(pi, {
    name: "bbk_python_structure",
    label: "BBK Python Structure Projection",
    description: "Project one generic BBK ImplementationStructureContract into Python vocabulary without mutating the repository or changing the generic contract.",
    parameters: z.object({
      root: z.string().optional(), contract: z.string(), role: z.string().optional(),
      assuranceTier: z.enum(["routine", "material", "consequential", "critical"]).optional(),
    }),
    argv: p => ["structure", "--contract", p.contract, ...(p.root ? ["--root", p.root] : []), ...(p.role ? ["--role", p.role] : []), ...(p.assuranceTier ? ["--assurance-tier", p.assuranceTier] : [])],
  });
  registerTool(pi, {
    name: "bbk_python_slice",
    label: "BBK Python Execution Slice Projection",
    description: "Project one generic BBK ExecutionSlice into a Python touchpoint, dependency closure, candidate boundary, and evidence plan without executing gates.",
    parameters: z.object({
      root: z.string().optional(), slice: z.string(), contract: z.string().optional(), role: z.string().optional(),
      assuranceTier: z.enum(["routine", "material", "consequential", "critical"]).optional(),
    }),
    argv: p => ["slice", "--slice", p.slice, ...(p.contract ? ["--contract", p.contract] : []), ...(p.root ? ["--root", p.root] : []), ...(p.role ? ["--role", p.role] : []), ...(p.assuranceTier ? ["--assurance-tier", p.assuranceTier] : [])],
  });
  registerTool(pi, {
    name: "bbk_python_structure_review",
    label: "BBK Python Structure Review",
    description: "Compare an exact Python candidate with fixed and consequential implementation-structure decisions while allowing harmless private differences inside delegated freedom.",
    parameters: z.object({
      root: z.string().optional(), contract: z.string(), candidate: z.string(), actualInventory: z.string().optional(),
      assuranceTier: z.enum(["routine", "material", "consequential", "critical"]).optional(),
    }),
    argv: p => ["structure-review", "--contract", p.contract, "--candidate", p.candidate, ...(p.actualInventory ? ["--actual-inventory", p.actualInventory] : []), ...(p.root ? ["--root", p.root] : []), ...(p.assuranceTier ? ["--assurance-tier", p.assuranceTier] : [])],
  });

  pi.registerCommand("bbk:python:state-effect", {
    description: "Run state-effect; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:python:state-effect <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("state-effect", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "State–Decision–Effect Projection failed" : "State–Decision–Effect Projection completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:python:state-effect-inventory", {
    description: "Run state-effect-inventory; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:python:state-effect-inventory <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("state-effect-inventory", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "State–Decision–Effect Inventory failed" : "State–Decision–Effect Inventory completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:python:state-effect-review", {
    description: "Run state-effect-review; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:python:state-effect-review <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("state-effect-review", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "State–Decision–Effect Review failed" : "State–Decision–Effect Review completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:python:review-context", {
    description: "Run review-context; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:python:review-context <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("review-context", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "Review Context failed" : "Review Context completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:python:review-lens", {
    description: "Run review-lens; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:python:review-lens <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("review-lens", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "Review Lens failed" : "Review Lens completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:python:evidence-adapter", {
    description: "Run evidence-adapter; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:python:evidence-adapter <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("evidence-adapter", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "Evidence Adapter failed" : "Evidence Adapter completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });

  pi.registerCommand("bbk:python", {
    description: "Resolve the Python profile for the current changed scope",
    handler: async (args, ctx) => {
      const hints = args?.trim() ? args.trim().split(/\s+/) : [];
      const value = await runPython(["resolve", ...hints.flatMap(hint => ["--hint", hint])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Python profile resolved" : "Python profile resolution failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:python:preflight", {
    description: "Inspect the current Python project without executing project tools or installers unless 'run-tools' is supplied",
    handler: async (args, ctx) => {
      const runTools = args?.trim() === "run-tools";
      const value = await runPython(["preflight", ...(runTools ? ["--run-tools"] : [])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Python preflight completed" : "Python preflight failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:python:gates", {
    description: "Compile a Python gate plan; optional argument is the assurance tier",
    handler: async (args, ctx) => {
      const tier = args?.trim();
      const value = await runPython(["gate-plan", ...(tier ? ["--assurance-tier", tier] : [])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Python gate plan compiled" : "Python gate planning failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:python:structure", {
    description: "Project a generic ImplementationStructureContract; argument is the contract JSON path",
    handler: async (args, ctx) => {
      const contract = args?.trim();
      if (!contract) { ctx.ui.notify("Usage: /bbk:python:structure <contract.json>", "warning"); return undefined; }
      const value = await runPython(["structure", "--contract", contract], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Python structure projected" : "Python structure projection failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:python:slice", {
    description: "Project a generic ExecutionSlice; arguments are <slice.json> [contract.json]",
    handler: async (args, ctx) => {
      const [slice, contract] = args?.trim().split(/\s+/).filter(Boolean) || [];
      if (!slice) { ctx.ui.notify("Usage: /bbk:python:slice <slice.json> [contract.json]", "warning"); return undefined; }
      const value = await runPython(["slice", "--slice", slice, ...(contract ? ["--contract", contract] : [])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Python slice projected" : "Python slice projection failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:python:structure-review", {
    description: "Compare planned and actual Python structure; arguments are <contract.json> <candidate.json> [inventory.json]",
    handler: async (args, ctx) => {
      const [contract, candidate, inventory] = args?.trim().split(/\s+/).filter(Boolean) || [];
      if (!contract || !candidate) { ctx.ui.notify("Usage: /bbk:python:structure-review <contract.json> <candidate.json> [inventory.json]", "warning"); return undefined; }
      const value = await runPython(["structure-review", "--contract", contract, "--candidate", candidate, ...(inventory ? ["--actual-inventory", inventory] : [])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Python structure review completed" : "Python structure review failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });

  pi.on("session_start", async (_event, ctx) => {
    const root = profileRoot(ctx.cwd);
    ctx.ui.notify(root ? `BBK Python profile 0.1.0-alpha.3 loaded` : "BBK Python profile extension loaded; profile package not found", root ? "info" : "warning");
  });
}
