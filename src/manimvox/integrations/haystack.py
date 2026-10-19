"""manimvox's tools for Haystack (extra: haystack), and the skills through Haystack's own SkillToolset:

    from haystack.components.agents import Agent
    from manimvox.integrations.haystack import manimvox_skills, manimvox_tools

    agent = Agent(chat_generator=..., tools=[*manimvox_tools("hash-maps"), manimvox_skills()])

Haystack sends usage telemetry unless HAYSTACK_TELEMETRY_ENABLED=False is set.
"""

from __future__ import annotations

from pathlib import Path

from ..skills import skills_path
from .common import arg_docs, args_model, file_tools, json_tools, missing

try:
    from haystack.tools import SkillToolset, Tool
except ImportError as e:
    raise missing("haystack", "haystack") from e


def _parameters(fn) -> dict:
    schema = args_model(fn).model_json_schema()
    schema.pop("title", None)
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)
    return schema


def manimvox_tools(project: str | Path, files: bool = True) -> list[Tool]:
    """Every manimvox tool pinned to `project`, plus read, write and list for its files unless files=False."""
    fns = json_tools(project) + (file_tools(project) if files else [])
    return [Tool(name=f.__name__, description=arg_docs(f)[0], parameters=_parameters(f), function=f) for f in fns]


def manimvox_skills() -> SkillToolset:
    """The manimvox skills as Haystack's load_skill and read_skill_file tools."""
    from haystack.skill_stores.file_system import FileSystemSkillStore

    return SkillToolset(FileSystemSkillStore(str(skills_path())))
