"""manimvox's tools for Google ADK (extra: google-adk), and the skills through ADK's own SkillToolset:

    from google.adk.agents import LlmAgent
    from manimvox.integrations.google_adk import manimvox_skill_toolset, manimvox_tools

    agent = LlmAgent(name="manimvox", model=..., instruction=..., tools=[*manimvox_tools("hash-maps"), manimvox_skill_toolset()])
"""

from __future__ import annotations

import inspect
import typing
from pathlib import Path
from typing import Annotated

from ..skills import skills_path
from .common import arg_docs, file_tools, json_tools, missing

try:
    from google.adk.tools import FunctionTool
    from google.adk.tools.skill_toolset import SkillToolset
except ImportError as e:
    raise missing("google-adk", "google_adk") from e

SKILL_TOOLS = ["list_skills", "load_skill", "load_skill_resource"]  # read-only: run_skill_script is left out


def _described(fn):
    """A copy of fn whose annotations carry each Args: description, the only place ADK reads them from."""
    from pydantic import Field

    _, docs = arg_docs(fn)
    hints = typing.get_type_hints(fn)
    sig = inspect.signature(fn)
    ann = {n: Annotated[hints[n], Field(description=docs.get(n, ""))] for n in sig.parameters}

    def run(*args, **kwargs):
        return fn(*args, **kwargs)

    run.__name__ = run.__qualname__ = fn.__name__
    run.__doc__ = fn.__doc__
    run.__annotations__ = {**ann, "return": str}
    run.__signature__ = sig.replace(parameters=[p.replace(annotation=ann[p.name]) for p in sig.parameters.values()],
                                    return_annotation=str)
    return run


def manimvox_tools(project: str | Path, files: bool = True) -> list[FunctionTool]:
    """Every manimvox tool pinned to `project`, plus read, write and list for its files unless files=False."""
    fns = json_tools(project) + (file_tools(project) if files else [])
    return [FunctionTool(_described(f)) for f in fns]


def manimvox_skill_toolset() -> SkillToolset:
    """The manimvox skills as ADK's list_skills, load_skill and load_skill_resource tools."""
    from google.adk.skills import load_skills_from_dir

    return SkillToolset(skills=load_skills_from_dir(str(skills_path())), tool_filter=SKILL_TOOLS)
