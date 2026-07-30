export interface Input { value: string }
export function parseInput(raw: string): Input {
  const value: unknown = JSON.parse(raw);
  if (!value || typeof value !== "object" || typeof (value as { value?: unknown }).value !== "string") {
    throw new TypeError("invalid input");
  }
  return { value: (value as { value: string }).value };
}
export async function run(signal: AbortSignal): Promise<string> {
  if (signal.aborted) throw signal.reason;
  return "ok";
}
