"""manimvox's tools for the OpenAI Agents SDK (extra: openai-agents). A plain Agent has no SKILL.md loader, so the
tools include read_skill and manimvox_instructions() lists the skills:

    from agents import Agent
    from manimvox.integrations.openai_agents import manimvox_instructions, manimvox_tools

    agent = Agent(name="manimvox", instructions=manimvox_instructions(), tools=manimvox_tools("hash-maps"))
"""

from __future__ import annotations

from pathlib import Path

from .common import file_tools, json_tools, manimvox_instructions, missing, read_skill

try:
    from agents import FunctionTool, function_tool
except ImportError as e:
    raise missing("openai-agents", "openai_agents") from e

__all__ = ["manimvox_instructions", "manimvox_tools"]


def manimvox_tools(project: str | Path, files: bool = True) -> list[FunctionTool]:
    """Every manimvox tool and read_skill, plus read, write and list for project files unless files=False.

    strict_mode=False keeps optional arguments optional; the SDK's strict mode would make every one required.
    """
    fns = json_tools(project) + [read_skill] + (file_tools(project) if files else [])
    return [function_tool(f, name_override=f.__name__, strict_mode=False) for f in fns]
