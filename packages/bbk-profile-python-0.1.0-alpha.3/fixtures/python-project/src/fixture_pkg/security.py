"""Deliberate security-sensitive constructs used only for trigger qualification."""

import pickle
import subprocess


def load_trusted(data: bytes):
    return pickle.loads(data)


def run_argv(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, check=True, text=True, capture_output=True)
