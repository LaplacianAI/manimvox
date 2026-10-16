"""When manimvox may do something big (download a model) without asking, and how it asks."""
from __future__ import annotations

from collections.abc import Callable, Mapping


def make_confirm(assume_yes: bool, env: Mapping[str, str], stdin) -> Callable[[str], bool]:
    def confirm(prompt: str) -> bool:
        if assume_yes or env.get("MANIMVOX_ASSUME_YES") == "1":
            return True
        if not stdin.isatty():
            return False  # an agent or CI: never block on input
        return input(f"{prompt} [y/N] ").strip().lower().startswith("y")

    return confirm
