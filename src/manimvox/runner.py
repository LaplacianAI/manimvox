"""Run Manim for one episode in a subprocess, with the environment the kit reads."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Literal

from .project import EpisodeRef, Project
from .voice import VoiceSpec

Quality = Literal["draft", "final"]


class RenderError(Exception):
    pass


def manim_command(ep: EpisodeRef, quality: Quality, media_dir: Path) -> list[str]:
    q = ["-ql", "--fps", "10", "--disable_caching"] if quality == "draft" else ["-qh", "--fps", "30"]
    return [sys.executable, "-m", "manim", "render", *q, "--progress_bar", "none",
            "--media_dir", str(media_dir), "-o", ep.stem, str(ep.path), ep.cls]


def built_path(project: Project, ep: EpisodeRef, quality: Quality) -> Path:
    media = project.build_dir / ep.stem / ("media_draft" if quality == "draft" else "media")
    res = "480p10" if quality == "draft" else "1080p30"
    return media / "videos" / ep.stem / res / f"{ep.stem}.mp4"


def render_episode(project: Project, ep: EpisodeRef, quality: Quality, voice: VoiceSpec | None) -> Path:
    if not ep.path.exists():
        raise RenderError(f"{ep.path} does not exist")
    built = built_path(project, ep, quality)
    built.unlink(missing_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("MANIMVOX_") or k == "MANIMVOX_CACHE"}
    env |= {"MANIMVOX_PROJECT": str(project.root), "MANIMVOX_STEM": ep.stem, "PYTHONUTF8": "1"}
    if quality == "draft":
        env["MANIMVOX_NOTTS"] = "1"
    else:
        env["MANIMVOX_VOICE_RESOLVED"] = str(voice)
    media = built.parents[3]
    r = subprocess.run(manim_command(ep, quality, media), check=False, cwd=project.root, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not built.exists():
        tail = "\n".join((r.stderr or r.stdout).strip().splitlines()[-25:])
        raise RenderError(f"manim failed for {ep.stem}:\n{tail}")
    return built
