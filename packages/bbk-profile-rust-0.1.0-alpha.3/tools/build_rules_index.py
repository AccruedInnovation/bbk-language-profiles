#!/usr/bin/env python3
"""Build the deterministic applicability index for the bundled Rust rule corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "skills" / "rust-skills" / "rules"
OVERRIDES = ROOT / "mappings" / "rule-overrides.json"
OUTPUT = ROOT / "skills" / "rust-skills" / "rules-index.json"


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_metadata(rule_id: str, text: str) -> dict[str, Any]:
    lower = text.lower()
    channels = ["stable"]
    if "nightly" in lower or "#![feature" in lower:
        channels = ["stable", "nightly"] if "stable" in lower else ["nightly"]
    tools: list[str] = []
    crates: list[str] = []
    checks = {
        "cargo clippy": "clippy", "rustfmt": "rustfmt", "cargo miri": "miri",
        "cargo flamegraph": "cargo-flamegraph", "perf ": "perf", "llvm-profdata": "llvm-profdata",
    }
    for needle, tool in checks.items():
        if needle in lower:
            tools.append(tool)
    crate_candidates = [
        "anyhow", "thiserror", "tokio", "tracing", "proptest", "loom", "criterion", "insta",
        "smallvec", "arrayvec", "thin-vec", "compact_str", "ahash", "rayon", "serde", "bitflags",
        "mockall", "wide", "likely_stable",
    ]
    for crate in crate_candidates:
        if re.search(rf"\b{re.escape(crate.lower())}\b", lower):
            crates.append(crate)
    triggers = [rule_id.split("-", 1)[0]]
    for keyword in ["unsafe", "ffi", "async", "concurrency", "public-api", "serialization", "performance", "memory", "testing", "documentation", "observability"]:
        if keyword.replace("-", " ") in lower:
            triggers.append(keyword)
    return {
        "channels": sorted(set(channels)),
        "external_tools": sorted(set(tools)),
        "suggested_crates": sorted(set(crates)),
        "triggers": sorted(set(triggers)),
    }


def build() -> dict[str, Any]:
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    category_defaults = overrides["category_defaults"]
    rule_overrides = overrides["rules"]
    rules = []
    for path in sorted(RULES.glob("*.md")):
        rule_id = path.stem
        category = rule_id.split("-", 1)[0]
        text = path.read_text(encoding="utf-8")
        item: dict[str, Any] = {
            "id": rule_id,
            "path": f"rules/{path.name}",
            "category": category,
            "sha256": sha(path.read_bytes()),
            "title": next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), rule_id),
            "worker_applicability": True,
            "reviewer_applicability": True,
            "limitations": [],
            "evidence_required": False,
        }
        item.update(category_defaults.get(category, {}))
        item.update(text_metadata(rule_id, text))
        override = rule_overrides.get(rule_id, {})
        for key, value in override.items():
            if key == "limitations":
                item["limitations"] = list(dict.fromkeys([*item.get("limitations", []), *value]))
            else:
                item[key] = value
        rules.append(item)
    payload = {
        "schema": "bbk.rust-rules-index.v1",
        "source_skill": "rust-skills",
        "source_version": "1.5.1-bbk.1",
        "rule_count": len(rules),
        "rules": rules,
    }
    payload["content_sha256"] = sha(canonical(payload))
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    value = build()
    data = (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != data:
            print("rust rules index drift", flush=True)
            return 1
        print(f"Rust rules index current: {value['rule_count']} rules")
        return 0
    OUTPUT.write_bytes(data)
    print(f"Wrote {OUTPUT}: {value['rule_count']} rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
