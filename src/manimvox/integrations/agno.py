"""manimvox's tools as an Agno toolkit (extra: agno). Agno reads the skills with its own loader:

    from agno.agent import Agent
    from agno.skills import LocalSkills, Skills
    import manimvox
    from manimvox.integrations.agno import ManimvoxTools

    agent = Agent(skills=Skills(loaders=[LocalSkills(str(manimvox.skills_path()))]), tools=[ManimvoxTools("hash-maps")])
"""

from __future__ import annotations

from pathlib import Path

from .common import INSTRUCTIONS, file_tools, json_tools, missing

try:
    from agno.tools import Toolkit
except ImportError as e:
    raise missing("agno", "agno") from e


class ManimvoxTools(Toolkit):
    """Every manimvox tool, plus read, write and list for project files unless files=False, pinned to `project`."""

    def __init__(self, project: str | Path, files: bool = True, **kwargs):
        kwargs.setdefault("name", "manimvox")
        kwargs.setdefault("instructions", INSTRUCTIONS)
        kwargs.setdefault("add_instructions", True)
        super().__init__(tools=json_tools(project) + (file_tools(project) if files else []), **kwargs)
