"""Plugin and dynamic loading signals."""

from importlib import import_module


class Plugin:
    name = "built-in"


def load_plugin(module_name: str):
    return import_module(module_name)
