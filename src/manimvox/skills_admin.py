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

SKILLS_CLI = "skills@1.7.2"  # bump deliberately: npx runs this package


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
    """A manimvox skill we may replace or delete: a link or folder named like one of ours that really is one."""
    name = entry.name
    if name not in SKILL_NAMES:
        return False
    if entry.is_symlink():
        if Path(os.readlink(entry)).name != name:
            return False
        if not entry.exists():
            return True  # dangling
    elif not entry.is_dir():
        return False
    md = entry / "SKILL.md"
    if not md.is_file():
        return False
    try:
        return read_frontmatter(md).get("name") == name
    except ValueError:
        return False


def _clear(entry: Path) -> None:
    if entry.is_symlink() or entry.is_file():
        entry.unlink()
    elif entry.is_dir():
        shutil.rmtree(entry)


def _guard(target: Path, src: Path) -> None:
    rt, rs = Path(target).resolve(), Path(src).resolve()
    if rt == rs or rs in rt.parents:
        raise ValueError(f"{target} is manimvox's own skills folder; nothing to install")


def install_checked(
    target_dirs: list[Path], mode: Literal["link", "copy"], src: Path | None = None
) -> tuple[list[str], bool]:
    """Install; returns the messages and whether anything was skipped because it was not ours."""
    src = Path(src) if src else skills_path()
    for t in target_dirs:
        _guard(t, src)
    msgs: list[str] = []
    skipped = False
    fell_back = False
    for t in target_dirs:
        t.mkdir(parents=True, exist_ok=True)
        used = mode
        done = 0
        for name in SKILL_NAMES:
            dest = t / name
            if dest.exists() or dest.is_symlink():
                if not _is_ours(dest):
                    msgs.append(f"{dest} exists and is not a manimvox skill; left untouched")
                    skipped = True
                    continue
                _clear(dest)
            if used == "link":
                try:
                    os.symlink(src / name, dest, target_is_directory=True)
                    done += 1
                    continue
                except OSError:
                    used, fell_back = "copy", True
            shutil.copytree(src / name, dest)
            done += 1
        msgs.append(f"{t}: {done} skills ({'linked' if used == 'link' else 'copied'})")
    if fell_back:
        msgs.append("symlinks unavailable here; copied the skills instead")
    return msgs, skipped


def install(target_dirs: list[Path], mode: Literal["link", "copy"], src: Path | None = None) -> list[str]:
    return install_checked(target_dirs, mode, src)[0]


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


def remove(target_dirs: list[Path], src: Path | None = None) -> list[Path]:
    src = Path(src) if src else skills_path()
    for t in target_dirs:
        _guard(t, src)
    removed = []
    for t in target_dirs:
        if not t.is_dir():
            continue
        for e in sorted(t.iterdir()):
            if e.name in SKILL_NAMES and _is_ours(e):
                _clear(e)
                removed.append(e)
    return removed


def npx_command(agent_ids, scope_global: bool, copy: bool, yes: bool, src: Path, npx: str = "npx") -> list[str]:
    cmd = [npx, "--yes", SKILLS_CLI, "add", str(src), "--skill", "*"]
    for a in agent_ids or []:
        cmd += ["-a", a]
    if scope_global:
        cmd.append("-g")
    if copy:
        cmd.append("--copy")
    if yes:
        cmd.append("-y")
    return cmd


def npx_path() -> str | None:
    """The resolved npx executable (npx.cmd on Windows), so no shell is needed."""
    return shutil.which("npx")


def has_npx() -> bool:
    return npx_path() is not None


def known_targets(scope: Literal["project", "global"], root: Path, home: Path) -> list[Path]:
    """Every agent folder for the scope, detected or not: where an install may have gone."""
    return targets(AGENTS, scope, root, home)


def run_npx(cmd: list[str]) -> int:
    env = dict(os.environ, DISABLE_TELEMETRY="1")
    return subprocess.run(cmd, env=env, check=False).returncode


def is_tty() -> bool:
    return sys.stdin is not None and sys.stdin.isatty()
