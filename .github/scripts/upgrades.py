"""Print, as a Markdown table, the packages whose newest allowed version differs from the locked one.

    python .github/scripts/upgrades.py locked.txt latest.txt

Both files are `uv export --no-hashes` output: one `name==version` per line, with comment and marker lines.
"""
import re
import sys
from pathlib import Path

PIN = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;\\]+)")


def pins(path: str) -> dict[str, str]:
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = PIN.match(line)
        if m:
            out[m[1].lower()] = m[2]
    return out


def main(locked_path: str, latest_path: str) -> None:
    locked, latest = pins(locked_path), pins(latest_path)
    rows = [(name, locked.get(name, "(new)"), latest.get(name, "(gone)"))
            for name in sorted(locked.keys() | latest.keys()) if locked.get(name) != latest.get(name)]
    if not rows:
        print("Every dependency is already at its newest allowed version.")
        return
    print(f"{len(rows)} package(s) newer than `uv.lock`:\n")
    print("| Package | Locked | Newest |\n|---|---|---|")
    for name, a, b in rows:
        print(f"| {name} | {a} | {b} |")


if __name__ == "__main__":
    main(*sys.argv[1:3])
