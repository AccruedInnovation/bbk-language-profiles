import { test } from "node:test";
import { strict as assert } from "node:assert";
import { parseInput } from "../src/index.js";
test("parses", () => assert.equal(parseInput('{"value":"x"}').value, "x"));
