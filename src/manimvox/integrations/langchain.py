"""manimvox's tools as LangChain tools, and what LangChain Deep Agents needs to load the skills (extra: langchain).

    from deepagents import create_deep_agent
    from manimvox.integrations.langchain import deep_agent_kwargs

    agent = create_deep_agent(model="anthropic:claude-opus-5-5", **deep_agent_kwargs("hash-maps"))
"""

from __future__ import annotations

from pathlib import Path

from ..skills import skills_path
from .common import INSTRUCTIONS, json_tools, missing, project_note

try:
    from langchain_core.tools import BaseTool, StructuredTool
except ImportError as e:
    raise missing("langchain", "langchain") from e

SKILLS_ROUTE = "/skills/"


def manimvox_tools(project: str | Path) -> list[BaseTool]:
    """Every manimvox tool as a StructuredTool, with each argument described from the docstring."""
    return [StructuredTool.from_function(f, name=f.__name__, parse_docstring=True, error_on_invalid_docstring=False)
            for f in json_tools(project)]


def deep_agent_kwargs(project: str | Path) -> dict:
    """Keyword arguments for deepagents.create_deep_agent: the tools, the skills, the files and what to tell the model.

    The agent's file tools see the project folder as / and the skills, read-only, under /skills/. The project folder
    is created if missing, so new_project can fill it.
    """
    try:
        from deepagents import FilesystemPermission
        from deepagents.backends import CompositeBackend, FilesystemBackend
    except ImportError as e:
        raise missing("langchain", "langchain") from e
    root = Path(project).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    backend = CompositeBackend(default=FilesystemBackend(root_dir=root, virtual_mode=True),
                               routes={SKILLS_ROUTE: FilesystemBackend(root_dir=skills_path(), virtual_mode=True)})
    prompt = (f"{INSTRUCTIONS}\n\n{project_note(root)} Your file tools see that folder as /, so "
              f"{root / 'episodes'} is /episodes/. The skills are under {SKILLS_ROUTE} and read-only.")
    return {
        "tools": manimvox_tools(root),
        "skills": [SKILLS_ROUTE],
        "backend": backend,
        "permissions": [FilesystemPermission(operations=["write"], paths=[f"{SKILLS_ROUTE}**"], mode="deny")],
        "system_prompt": prompt,
    }
