// @ts-check
/** @param {unknown} value */
export function nameOf(value) {
  if (!value || typeof value !== "object" || !("name" in value) || typeof value.name !== "string") throw new TypeError("invalid");
  return value.name;
}
