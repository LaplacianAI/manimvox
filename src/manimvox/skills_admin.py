"""Install the bundled skills into coding agents: through `npx skills` when Node.js is present, natively otherwise."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .skills import SKILL_NAMES, content_hash, read_frontmatter, skills_path


@dataclass(frozen=True)
class Agent:
    id: str
    detect: str  # relative to home; "" = always present
    project: str  # relative to the project root
    global_: str  # relative to home


AGENTS = (
    Agent("claude-code", ".claude", ".claude/skills", ".claude/skills"),
    Agent("codex", ".codex", ".agents/skills", ".agents/skills"),
    Agent("cursor", ".cursor", ".agents/skills", ".cursor/skills"),
    Agent("gemini-cli", ".gemini", ".agents/skills", ".gemini/skills"),
    Agent("github-copilot", ".copilot", ".agents/skills", ".copilot/skills"),
    Agent("opencode", ".config/opencode", ".agents/skills", ".config/opencode/skills"),
    Agent("universal", "", ".agents/skills", ".agents/skills"),
)
BY_ID = {a.id: a for a in AGENTS}


def detect_agents(home: Path) -> list[Agent]:
    return [a for a in AGENTS if not a.detect or (Path(home) / a.detect).is_dir()]


def targets(agents, scope: Literal["project", "global"], root: Path, home: Path) -> list[Path]:
    out: list[Path] = []
    for a in agents:
        p = (Path(root) / a.project) if scope == "project" else (Path(home) / a.global_)
        if p not in out:
            out.append(p)
    return out


def _is_ours(entry: Path) -> bool:
    if entry.is_symlink() and not entry.exists():
        return entry.name in SKILL_NAMES
    md = entry / "SKILL.md"
    if not md.is_file():
        return False
    try:
        return read_frontmatter(md).get("name") in SKILL_NAMES
    except ValueError:
        return False


def _clear(entry: Path) -> None:
    if entry.is_symlink() or entry.is_file():
        entry.unlink()
    elif entry.is_dir():
        shutil.rmtree(entry)


def install(target_dirs: list[Path], mode: Literal["link", "copy"], src: Path | None = None) -> list[str]:
    src = Path(src) if src else skills_path()
    msgs: list[str] = []
    fell_back = False
    for t in target_dirs:
        t.mkdir(parents=True, exist_ok=True)
        used = mode
        for name in SKILL_NAMES:
            dest = t / name
            if dest.exists() or dest.is_symlink():
                _clear(dest)
            if used == "link":
                try:
                    os.symlink(src / name, dest, target_is_directory=True)
                    continue
                except OSError:
                    used, fell_back = "copy", True
            shutil.copytree(src / name, dest)
        msgs.append(f"{t}: {len(SKILL_NAMES)} skills ({'linked' if used == 'link' else 'copied'})")
    if fell_back:
        msgs.append("symlinks unavailable here; copied the skills instead")
    return msgs


def status(target_dir: Path, src: Path | None = None) -> dict[str, str]:
    src = Path(src) if src else skills_path()
    out = {}
    for name in SKILL_NAMES:
        p = target_dir / name
        if p.is_symlink() and not p.exists():
            out[name] = "broken"
        elif not (p / "SKILL.md").is_file():
            out[name] = "missing"
        else:
            out[name] = "ok" if content_hash(p) == content_hash(src / name) else "outdated"
    return out


def holds_ours(target_dir: Path) -> bool:
    return target_dir.is_dir() and any(_is_ours(e) for e in target_dir.iterdir())


def remove(target_dirs: list[Path]) -> list[Path]:
    removed = []
    for t in target_dirs:
        if not t.is_dir():
            continue
        for e in sorted(t.iterdir()):
            if e.name in SKILL_NAMES and _is_ours(e):
                _clear(e)
                removed.append(e)
    return removed


def npx_command(agent_ids, scope_global: bool, copy: bool, yes: bool, src: Path) -> list[str]:
    cmd = ["npx", "--yes", "skills", "add", str(src), "--skill", "*"]
    for a in agent_ids or []:
        cmd += ["-a", a]
    if scope_global:
        cmd.append("-g")
    if copy:
        cmd.append("--copy")
    if yes:
        cmd.append("-y")
    return cmd


def has_npx() -> bool:
    return shutil.which("npx") is not None


def run_npx(cmd: list[str]) -> int:
    env = dict(os.environ, DISABLE_TELEMETRY="1")
    return subprocess.run(cmd, env=env, check=False).returncode


def is_tty() -> bool:
    return sys.stdin is not None and sys.stdin.isatty()
