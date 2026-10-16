"""The agent skills bundled with manimvox: where they are, what they hold, and the manifest that pins them."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from . import __version__

SKILL_NAMES = (
    "manimvox", "manimvox-core", "manimvox-animation", "manimvox-creative", "manimvox-voice", "manimvox-cli",
    "manimvox-paper", "manimvox-playlist", "manimvox-concept", "manimvox-pr",
)
MANIFEST_NAME = "skills-manifest.json"


def skills_path() -> Path:
    """The skills folder: bundled in the wheel as manimvox/_skills, or the repo's skills/ in a dev install."""
    here = Path(__file__).resolve().parent
    for p in (here / "_skills", here.parents[1] / "skills"):
        if p.is_dir():
            return p
    raise FileNotFoundError("manimvox's skills are missing from this install; reinstall manimvox")


def _value(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def read_frontmatter(skill_md: Path) -> dict[str, object]:
    """The YAML frontmatter of a SKILL.md, for the subset skills use: `key: value` and one-level maps."""
    lines = Path(skill_md).read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---" or "---" not in [x.strip() for x in lines[1:]]:
        raise ValueError(f"{skill_md}: no frontmatter (a SKILL.md starts with --- name/description ---)")
    end = 1 + [x.strip() for x in lines[1:]].index("---")
    out: dict[str, object] = {}
    current: dict[str, str] | None = None
    map_key: str | None = None  # the top-level key of `current`
    map_indent = 0
    last: str | None = None  # the key whose value a continuation line would extend

    def check(key: str, raw: str) -> None:
        val = raw.strip()
        if val and val[0] in "|>[{":
            raise ValueError(f"{skill_md}: key {key!r}: block and flow values are not supported; "
                             "write a plain or quoted one-line value")

    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" \t"))
        k, sep, v = line.strip().partition(":")
        k = k.strip()
        if indent == 0:
            if not sep:
                raise ValueError(f"{skill_md}: key {last!r}: multi-line values are not supported; "
                                 "write it on one line" if last else f"{skill_md}: not a `key: value` line: {line!r}")
            check(k, v)
            if v.strip():
                out[k] = _value(v)
                current = None
            else:
                current = {}
                map_key, map_indent = k, 0
                out[k] = current
            last = k
            continue
        if current is None:
            raise ValueError(f"{skill_md}: key {last!r}: multi-line values are not supported; write it on one line")
        if map_indent == 0:
            map_indent = indent
        if indent > map_indent:
            raise ValueError(f"{skill_md}: key {map_key!r}: maps nest one level only (line {line.strip()!r})")
        if not sep or not v.strip():
            raise ValueError(f"{skill_md}: key {map_key!r}: each entry is `name: value` on one line "
                             f"(line {line.strip()!r})")
        check(k, v)
        current[k] = _value(v)
    return out


def skill_dirs(root: Path) -> list[Path]:
    root = Path(root)
    return sorted(p for p in root.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()) if root.is_dir() else []


def content_hash(skill_dir: Path) -> tuple[str, int]:
    """sha256 over each file's relative path and bytes (CRLF read as LF), in sorted order; and the file count."""
    h = hashlib.sha256()
    files = sorted(p for p in Path(skill_dir).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    for p in files:
        h.update(p.relative_to(skill_dir).as_posix().encode("utf-8") + b"\0")
        h.update(p.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return h.hexdigest(), len(files)


def build_manifest(root: Path, version: str) -> dict:
    skills = {}
    for d in skill_dirs(root):
        sha, n = content_hash(d)
        skills[d.name] = {"sha256": sha, "files": n}
    return {"version": version, "skills": skills}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m manimvox.skills")
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("manifest", help="write or check skills-manifest.json")
    g = m.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    m.add_argument("--root", default=None, help="the skills folder (default: the repo's skills/)")
    m.add_argument("--out", default=None, help="manifest path (default: next to the skills folder)")
    a = p.parse_args(argv)
    root = Path(a.root) if a.root else skills_path()
    out = Path(a.out) if a.out else root.parent / MANIFEST_NAME
    want = build_manifest(root, __version__)
    text = json.dumps(want, indent=2) + "\n"
    if a.write:
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out} ({len(want['skills'])} skills)")
        return 0
    have = out.read_text(encoding="utf-8") if out.is_file() else ""
    if have != text:
        print(f"{out} is out of date: run python -m manimvox.skills manifest --write", file=sys.stderr)
        return 1
    print(f"{out}: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
