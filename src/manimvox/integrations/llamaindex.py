"""manimvox's tools for LlamaIndex (extra: llamaindex). LlamaIndex has no SKILL.md loader, so the tools include
read_skill and manimvox_instructions() lists the skills:

    from llama_index.core.agent.workflow import FunctionAgent
    from manimvox.integrations.llamaindex import manimvox_instructions, manimvox_tools

    agent = FunctionAgent(tools=manimvox_tools("hash-maps"), llm=..., system_prompt=manimvox_instructions())
"""

from __future__ import annotations

from pathlib import Path

from .common import arg_docs, args_model, file_tools, json_tools, manimvox_instructions, missing, read_skill

try:
    from llama_index.core.tools import FunctionTool
except ImportError as e:
    raise missing("llamaindex", "llamaindex") from e

__all__ = ["manimvox_instructions", "manimvox_tools"]


def manimvox_tools(project: str | Path, files: bool = True) -> list[FunctionTool]:
    """Every manimvox tool pinned to `project` and read_skill, plus read, write and list for its files unless files=False."""
    fns = json_tools(project) + [read_skill] + (file_tools(project) if files else [])
    return [FunctionTool.from_defaults(fn=f, name=f.__name__, description=arg_docs(f)[0], fn_schema=args_model(f))
            for f in fns]
