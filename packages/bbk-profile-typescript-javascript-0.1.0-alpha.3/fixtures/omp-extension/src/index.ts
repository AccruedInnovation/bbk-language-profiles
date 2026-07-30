export default function extension(pi: { registerTool(value: unknown): void; registerCommand(name: string, value: unknown): void }) {
  pi.registerTool({ name: "fixture" });
  pi.registerCommand("fixture", {});
}
