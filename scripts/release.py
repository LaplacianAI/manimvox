"""Set a new version everywhere it is written, and date the changelog's Unreleased section.

    uv run python scripts/release.py 0.2.0

Changes `__version__`, every plugin manifest, the README's series.json example and the skills manifest, then
turns `## [Unreleased]` in CHANGELOG.md into `## [0.2.0] - <today>` under a fresh empty Unreleased section, with
the compare links at the bottom. Review the diff, merge it, then push the tag `v0.2.0` to publish.
"""

from __future__ import annotations

import datetime
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INIT = ROOT / "src" / "manimvox" / "__init__.py"
MANIFESTS = [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", ".codex-plugin/plugin.json",
             ".cursor-plugin/plugin.json", "gemini-extension.json", "plugin.json"]
REPO = "https://github.com/LaplacianAI/manimvox"


def current() -> str:
    m = re.search(r'^__version__ = "(.+)"$', INIT.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        raise SystemExit(f"no __version__ in {INIT}")
    return m[1]


def replace(path: Path, old: str, new: str, count: int | None = None) -> None:
    text = path.read_text(encoding="utf-8")
    n = text.count(old)
    if not n or (count is not None and n != count):
        raise SystemExit(f"{path.relative_to(ROOT)}: expected {count or 'some'} of {old!r}, found {n}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def changelog(text: str, old: str, new: str, today: str) -> str:
    if "## [Unreleased]" not in text:
        raise SystemExit("CHANGELOG.md has no ## [Unreleased] section")
    if f"## [{new}]" in text:
        raise SystemExit(f"CHANGELOG.md already has a {new} section")
    text = text.replace("## [Unreleased]", f"## [Unreleased]\n\n## [{new}] - {today}", 1)
    unreleased = f"[Unreleased]: {REPO}/compare/v{old}...HEAD"
    if unreleased not in text:
        raise SystemExit(f"CHANGELOG.md has no link line {unreleased!r}")
    return text.replace(unreleased, f"[Unreleased]: {REPO}/compare/v{new}...HEAD\n"
                                    f"[{new}]: {REPO}/compare/v{old}...v{new}", 1)


def main(argv: list[str]) -> None:
    if len(argv) != 1 or not re.fullmatch(r"\d+\.\d+\.\d+", argv[0]):
        raise SystemExit("usage: python scripts/release.py X.Y.Z")
    new, old = argv[0], current()
    if tuple(map(int, new.split("."))) <= tuple(map(int, old.split("."))):
        raise SystemExit(f"{new} is not newer than {old}")
    log = ROOT / "CHANGELOG.md"
    dated = changelog(log.read_text(encoding="utf-8"), old, new, datetime.date.today().isoformat())  # checked first:
    replace(INIT, f'__version__ = "{old}"', f'__version__ = "{new}"', 1)  # a bad changelog changes nothing
    for m in MANIFESTS:
        replace(ROOT / m, f'"version": "{old}"', f'"version": "{new}"', 1)
    replace(ROOT / "README.md", f'"manimvox": "{old}"', f'"manimvox": "{new}"')
    log.write_text(dated, encoding="utf-8")
    # a fresh interpreter, so the manifest is stamped with the new __version__
    subprocess.run([sys.executable, "-m", "manimvox.skills", "manifest", "--write"], check=True, cwd=ROOT)
    print(f"{old} -> {new}. Review the diff, merge it, then: git tag v{new} && git push origin v{new}")


if __name__ == "__main__":
    main(sys.argv[1:])
