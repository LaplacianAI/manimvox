"""manimvox's tools for CrewAI (extra: crewai). CrewAI loads the skills itself:

    from crewai import Agent
    import manimvox
    from manimvox.integrations.crewai import manimvox_tools

    agent = Agent(role=..., goal=..., backstory=..., tools=manimvox_tools("hash-maps"), skills=[manimvox.skills_path()])
"""

from __future__ import annotations

import sys
from pathlib import Path

from .common import arg_docs, args_model, file_tools, json_tools, missing

try:
    from crewai.tools.base_tool import Tool
except ImportError as e:
    raise ImportError(f"{missing('crewai', 'crewai')}. CrewAI supports Python below 3.14 only: on 3.14 the extra "
                      f"installs nothing (this is Python {sys.version_info.major}.{sys.version_info.minor})") from e


def manimvox_tools(project: str | Path, files: bool = True) -> list[Tool]:
    """Every manimvox tool pinned to `project`, plus read, write and list for its files unless files=False.

    CrewAI's tool() decorator drops the argument descriptions, so each tool is built from an explicit schema.
    """
    fns = json_tools(project) + (file_tools(project) if files else [])
    return [Tool(name=f.__name__, description=arg_docs(f)[0], func=f, args_schema=args_model(f)) for f in fns]
