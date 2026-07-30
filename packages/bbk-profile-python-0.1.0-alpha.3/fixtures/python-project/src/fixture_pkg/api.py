"""Small typed public API."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Greeting:
    message: str


def greet(name: str) -> Greeting:
    normalized = name.strip()
    if not normalized:
        raise ValueError("name must not be empty")
    return Greeting(message=f"Hello, {normalized}!")


def main() -> int:
    print(greet("fixture").message)
    return 0
