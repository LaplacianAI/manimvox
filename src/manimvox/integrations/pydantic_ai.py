"""manimvox's tools as a Pydantic AI toolset (extra: pydantic-ai). Pydantic AI has no SKILL.md loader of its own,
so the toolset carries read_skill and manimvox_instructions() lists the skills:

    from pydantic_ai import Agent
    from manimvox.integrations.pydantic_ai import manimvox_instructions, manimvox_toolset

    agent = Agent("anthropic:claude-opus-5-5", toolsets=[manimvox_toolset()], instructions=manimvox_instructions())
"""

from __future__ import annotations

from .common import file_tools, json_tools, manimvox_instructions, missing, read_skill

try:
    from pydantic_ai import Tool
    from pydantic_ai.toolsets import FunctionToolset
except ImportError as e:
    raise missing("pydantic-ai", "pydantic_ai") from e

__all__ = ["manimvox_instructions", "manimvox_toolset"]


def manimvox_toolset(files: bool = True) -> FunctionToolset:
    """Every manimvox tool and read_skill, plus read, write and list for project files unless files=False."""
    fns = json_tools() + [read_skill] + (file_tools() if files else [])
    return FunctionToolset([Tool(f, name=f.__name__, docstring_format="google") for f in fns])
