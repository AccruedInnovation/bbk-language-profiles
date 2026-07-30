from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "omp" / "extension" / "index.js"


class OmpCommandContextBoundaryTests(unittest.TestCase):
    def test_slash_commands_do_not_inject_results_into_model_context(self):
        text = EXTENSION.read_text(encoding="utf-8")
        self.assertNotIn("sendMessage(", text)
        self.assertNotIn("sendUserMessage(", text)
        self.assertNotIn("return value.details", text)
        self.assertNotIn("return ctx.ui.notify", text)
        self.assertIn("ctx.ui.notify", text)

    def test_llm_callable_tools_still_return_structured_results(self):
        text = EXTENSION.read_text(encoding="utf-8")
        self.assertIn("content:", text)
        self.assertIn("details:", text)
        self.assertIn("registerTool", text)


if __name__ == "__main__":
    unittest.main()
