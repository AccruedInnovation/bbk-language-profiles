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
    if (value?.id === "go" && typeof value.path === "string") return value.path;
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
  if (process.env.BBK_PROFILE_GO_ROOT) return path.resolve(process.env.BBK_PROFILE_GO_ROOT);
  for (const root of ancestors(cwd)) {
    for (const current of [
      path.join(root, ".bbk", "profiles", "go", "current.json"),
      path.join(root, ".bbk-kit", "profiles", "go", "current.json"),
    ]) {
      const value = readCurrent(current);
      if (value) return value;
    }
  }
  return readCurrent(path.join(userDataRoot(), "profiles", "go", "current.json"));
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
  if (process.env.BBK_GO_CLI) return explicitCommand(process.env.BBK_GO_CLI);
  const root = profileRoot(cwd);
  if (root) {
    const script = path.join(root, "tools", "bbk_go.py");
    if (fs.existsSync(script)) {
      const python = process.env.BBK_PYTHON || (process.platform === "win32" ? "py" : "python3");
      return { executable: python, prefix: process.platform === "win32" && !process.env.BBK_PYTHON ? ["-3", script] : [script] };
    }
  }
  return { executable: process.platform === "win32" ? "bbk-go.cmd" : "bbk-go", prefix: [] };
}

function runGo(args, cwd, signal) {
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
        details = { status: "ERROR", stdout, stderr, parseError: "bbk-go did not return JSON" };
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
      return toolResult(await runGo(definition.argv(params), ctx.cwd, signal));
    },
  });
}

// Slash commands report through ctx.ui.notify only. Structured JSON is
// returned only by LLM-callable tools, where model-facing content is intended.


function profileCapabilityCommand(cwd) {
  if (process.env.BBK_GO_PROFILE_DISPATCH_CLI) return explicitCommand(process.env.BBK_GO_PROFILE_DISPATCH_CLI);
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

export default function bbkGoExtension(pi) {
  const { z } = pi.zod;
  pi.setLabel("BBK Go Profile");
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
    name: "bbk_go_state_effect",
    label: "BBK Go State–Decision–Effect Projection",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation state-effect against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("state-effect", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_go_state_effect_inventory",
    label: "BBK Go State–Decision–Effect Inventory",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation state-effect-inventory against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("state-effect-inventory", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_go_state_effect_review",
    label: "BBK Go State–Decision–Effect Review",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation state-effect-review against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("state-effect-review", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_go_review_context",
    label: "BBK Go Review Context",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation review-context against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("review-context", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_go_review_lens",
    label: "BBK Go Review Lens",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation review-lens against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("review-lens", params.request, ctx.cwd, signal)); },
  });
  pi.registerTool({
    name: "bbk_go_evidence_adapter",
    label: "BBK Go Evidence Adapter",
    description: "Run the read-only BBK alpha.8 typed profile-capability operation evidence-adapter against one exact request package.",
    parameters: z.object({ request: z.string() }),
    async execute(_id, params, signal, _onUpdate, ctx) { return toolResult(await runProfileCapability("evidence-adapter", params.request, ctx.cwd, signal)); },
  });

  registerTool(pi, {
    name: "bbk_go_preflight",
    label: "BBK Go Preflight",
    description: "Inspect the effective Go module/workspace, toolchain declaration, supported configurations, and repository commands without granting or running project effects by default.",
    parameters: z.object({ root: z.string().optional(), runTools: z.boolean().optional() }),
    argv: p => ["preflight", ...(p.root ? ["--root", p.root] : []), ...(p.runTools ? ["--run-tools"] : [])],
  });
  registerTool(pi, {
    name: "bbk_go_resolve",
    label: "BBK Go Resolve",
    description: "Resolve proportional Go skills, focused review packs, and planned gates from the role, task, changed scope, and assurance tier.",
    parameters,
    argv: p => ["resolve", ...commonArgs(p)],
  });
  registerTool(pi, {
    name: "bbk_go_gate_plan",
    label: "BBK Go Gate Plan",
    description: "Compile a non-executing, repository-aware Go gate plan. Tool installation and effects remain separately authorized.",
    parameters,
    argv: p => ["gate-plan", ...commonArgs(p)],
  });


  registerTool(pi, {
    name: "bbk_go_structure",
    label: "BBK Go Structure",
    description: "Project an exact BBK ImplementationStructureContract into Go packages, contracts, ownership, failure, test seams, and review selection without mutating the repository.",
    parameters: z.object({
      root: z.string().optional(),
      contract: z.string(),
      role: z.string().optional(),
      taskProfile: z.string().optional(),
      assuranceTier: z.enum(["routine", "material", "consequential", "critical"]).optional(),
      runTools: z.boolean().optional(),
    }),
    argv: p => ["structure", ...(p.root ? ["--root", p.root] : []), "--contract", p.contract, ...(p.role ? ["--role", p.role] : []), ...(p.taskProfile ? ["--task-profile", p.taskProfile] : []), ...(p.assuranceTier ? ["--assurance-tier", p.assuranceTier] : []), ...(p.runTools ? ["--run-tools"] : [])],
  });
  registerTool(pi, {
    name: "bbk_go_slice",
    label: "BBK Go Execution Slice",
    description: "Project an exact BBK ExecutionSlice into a Go touchpoint, dependency closure, assertion evidence, candidate boundary, and scaffolding disposition.",
    parameters: z.object({
      root: z.string().optional(),
      slice: z.string(),
      role: z.string().optional(),
      taskProfile: z.string().optional(),
      assuranceTier: z.enum(["routine", "material", "consequential", "critical"]).optional(),
      runTools: z.boolean().optional(),
    }),
    argv: p => ["slice", ...(p.root ? ["--root", p.root] : []), "--slice", p.slice, ...(p.role ? ["--role", p.role] : []), ...(p.taskProfile ? ["--task-profile", p.taskProfile] : []), ...(p.assuranceTier ? ["--assurance-tier", p.assuranceTier] : []), ...(p.runTools ? ["--run-tools"] : [])],
  });
  registerTool(pi, {
    name: "bbk_go_structure_review",
    label: "BBK Go Structure Review",
    description: "Compare fixed and consequential planned Go structure with one exact candidate and actual inventory while tolerating delegated private differences.",
    parameters: z.object({
      root: z.string().optional(),
      contract: z.string(),
      candidate: z.string(),
      actualInventory: z.string().optional(),
      assuranceTier: z.enum(["routine", "material", "consequential", "critical"]).optional(),
      runTools: z.boolean().optional(),
    }),
    argv: p => ["structure-review", ...(p.root ? ["--root", p.root] : []), "--contract", p.contract, "--candidate", p.candidate, ...(p.actualInventory ? ["--actual-inventory", p.actualInventory] : []), ...(p.assuranceTier ? ["--assurance-tier", p.assuranceTier] : []), ...(p.runTools ? ["--run-tools"] : [])],
  });

  pi.registerCommand("bbk:go:state-effect", {
    description: "Run state-effect; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:go:state-effect <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("state-effect", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "State–Decision–Effect Projection failed" : "State–Decision–Effect Projection completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:go:state-effect-inventory", {
    description: "Run state-effect-inventory; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:go:state-effect-inventory <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("state-effect-inventory", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "State–Decision–Effect Inventory failed" : "State–Decision–Effect Inventory completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:go:state-effect-review", {
    description: "Run state-effect-review; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:go:state-effect-review <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("state-effect-review", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "State–Decision–Effect Review failed" : "State–Decision–Effect Review completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:go:review-context", {
    description: "Run review-context; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:go:review-context <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("review-context", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "Review Context failed" : "Review Context completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:go:review-lens", {
    description: "Run review-lens; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:go:review-lens <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("review-lens", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "Review Lens failed" : "Review Lens completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });
  pi.registerCommand("bbk:go:evidence-adapter", {
    description: "Run evidence-adapter; argument is the exact BBK profile-capability request JSON path",
    handler: async (args, ctx) => {
      const request = args?.trim();
      if (!request) { ctx.ui.notify("Usage: /bbk:go:evidence-adapter <request.json>", "warning"); return undefined; }
      const value = await runProfileCapability("evidence-adapter", request, ctx.cwd);
      ctx.ui.notify(value.details?.status === "ERROR" ? "Evidence Adapter failed" : "Evidence Adapter completed", value.details?.status === "ERROR" ? "error" : "info");
      return undefined;
    },
  });

  pi.registerCommand("bbk:go", {
    description: "Resolve the Go profile for the current changed scope",
    handler: async (args, ctx) => {
      const hints = args?.trim() ? args.trim().split(/\s+/) : [];
      const value = await runGo(["resolve", ...hints.flatMap(hint => ["--hint", hint])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Go profile resolved" : "Go profile resolution failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:go:preflight", {
    description: "Inspect the current Go workspace without executing Go commands or toolchain selection unless 'run-tools' is supplied",
    handler: async (args, ctx) => {
      const runTools = args?.trim() === "run-tools";
      const value = await runGo(["preflight", ...(runTools ? ["--run-tools"] : [])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Go preflight completed" : "Go preflight failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:go:gates", {
    description: "Compile a Go gate plan; optional argument is the assurance tier",
    handler: async (args, ctx) => {
      const tier = args?.trim();
      const value = await runGo(["gate-plan", ...(tier ? ["--assurance-tier", tier] : [])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Go gate plan compiled" : "Go gate planning failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });


  pi.registerCommand("bbk:go:structure", {
    description: "Project an ImplementationStructureContract; argument is the contract JSON path",
    handler: async (args, ctx) => {
      const contract = args?.trim();
      if (!contract) { ctx.ui.notify("Provide a contract JSON path", "error"); return; }
      const value = await runGo(["structure", "--contract", contract], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Go structure projected" : "Go structure projection failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:go:slice", {
    description: "Project an ExecutionSlice; argument is the slice JSON path",
    handler: async (args, ctx) => {
      const slice = args?.trim();
      if (!slice) { ctx.ui.notify("Provide a slice JSON path", "error"); return; }
      const value = await runGo(["slice", "--slice", slice], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Go slice projected" : "Go slice projection failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });
  pi.registerCommand("bbk:go:structure-review", {
    description: "Review planned versus actual structure; arguments are contract and candidate paths",
    handler: async (args, ctx) => {
      const parts = args?.trim().split(/\s+/).filter(Boolean) || [];
      if (parts.length < 2) { ctx.ui.notify("Provide contract and candidate JSON paths", "error"); return; }
      const value = await runGo(["structure-review", "--contract", parts[0], "--candidate", parts[1], ...(parts[2] ? ["--actual-inventory", parts[2]] : [])], ctx.cwd);
      ctx.ui.notify(value.code === 0 ? "Go structure review completed" : "Go structure review failed", value.code === 0 ? "info" : "error");
      return undefined;
    },
  });

  pi.on("session_start", async (_event, ctx) => {
    const root = profileRoot(ctx.cwd);
    ctx.ui.notify(root ? `BBK Go profile 0.1.0-alpha.3 loaded` : "BBK Go profile extension loaded; profile package not found", root ? "info" : "warning");
  });
}
